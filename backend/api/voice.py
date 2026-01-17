"""
Voice call webhook endpoints for Twilio Voice API.

Handles incoming calls via Twilio Media Streams (WebSocket) for real-time
audio streaming, processes speech-to-text, and manages conversation flow.
"""

import os
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, date, time, timedelta
from fastapi import APIRouter, Depends, Request, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from sqlalchemy.orm import Session
from twilio.twiml.voice_response import VoiceResponse, Start, Stream

from backend.database import get_db
from backend.models import Restaurant, Table, Customer, Booking, BookingStatus
from backend.services.voice_service import voice_service
from backend.services.sms_service import sms_service
from backend.services.conversation_handler import conversation_handler
from backend.services.transcript_service import transcript_service
from backend.services.deepgram_service import deepgram_service
from backend.services.llm_service import llm_service
from backend.services.elevenlabs_service import elevenlabs_service
from backend.services.media_streams_service import media_streams_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Store conversation state (in production, use Redis or similar)
conversation_state: Dict[str, Dict[str, Any]] = {}


def get_base_url(request: Request) -> str:
    """Extract base URL from request, handling ngrok/proxy headers."""
    base_url = str(request.base_url).rstrip('/')

    # Check for ngrok/proxy headers
    if 'x-forwarded-proto' in request.headers:
        protocol = request.headers['x-forwarded-proto']
        # ngrok uses the Host header, not X-Forwarded-Host
        host = request.headers.get('x-forwarded-host') or request.headers.get('host', '')
        if host and host != 'localhost:8000' and not host.startswith('127.0.0.1'):
            base_url = f"{protocol}://{host}"

    return base_url


@router.post("/welcome")
async def voice_welcome(
    request: Request,
    To: Optional[str] = Form(None),
    From: Optional[str] = Form(None),
    CallSid: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Initial webhook when call is received.
    Returns TwiML with Media Streams Start instruction.

    Args:
        request: FastAPI request object (to get base URL)
        To: Twilio phone number that was called (identifies restaurant)
        From: Caller's phone number
        CallSid: Unique call identifier
        db: Database session
    """
    logger.info(f"Voice call received from {From} to {To}, CallSid: {CallSid}")

    # Get base URL from request (for WebSocket URL)
    base_url = get_base_url(request)
    
    # Convert HTTP(S) to WS(S) for WebSocket URL
    ws_protocol = "wss" if base_url.startswith("https") else "ws"
    ws_base = base_url.replace("https://", "").replace("http://", "")
    ws_url = f"{ws_protocol}://{ws_base}/api/voice/stream"
    
    logger.info(f"Using WebSocket URL: {ws_url}")

    # Normalize phone number (remove spaces, ensure + prefix)
    to_normalized = To.strip() if To else None
    if to_normalized and not to_normalized.startswith('+'):
        to_normalized = '+' + to_normalized

    # Look up which restaurant owns this Twilio number
    from backend.models_platform import RestaurantAccount
    restaurant = db.query(RestaurantAccount).filter(
        RestaurantAccount.twilio_phone_number == to_normalized
    ).first()

    if not restaurant:
        logger.warning(f"No restaurant found for Twilio number {To}")
        response = VoiceResponse()
        response.say(
            "This number is not configured. Please contact support.",
            voice='alice',
            language='en-US'
        )
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    # Check if voice services are available (health check)
    services_available = (
        deepgram_service.is_enabled() and
        llm_service.is_enabled() and
        elevenlabs_service.is_enabled()
    )

    if not services_available:
        logger.warning("Voice services not available - sending SMS fallback")
        # Send SMS fallback
        try:
            sms_message = (
                f"Sorry, we're not currently handling voice orders. "
                f"Please text us your order or call back later. "
                f"You can also visit our website. - {restaurant.business_name}"
            )
            sms_service.send_sms(
                to=From or "",
                message=sms_message,
                from_number=restaurant.twilio_phone_number
            )
        except Exception as e:
            logger.error(f"Failed to send SMS fallback: {str(e)}")
        
        # Return error TwiML
        response = VoiceResponse()
        response.say(
            "Sorry, we're not currently handling voice orders. "
            "Please text us your order or call back later. Thank you.",
            voice='alice',
            language='en-US'
        )
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    # Create TwiML response with Media Streams
    response = VoiceResponse()
    
    # Start Media Streams
    start = Start()
    stream = Stream(
        url=ws_url,
        track='both_tracks'  # Track both incoming and outgoing audio
    )
    start.stream(stream)
    response.append(start)
    
    # Optional: Say something while stream connects
    response.say(
        f"Hi, thanks for calling {restaurant.business_name}. How can I help you?",
        voice='alice',
        language='en-US'
    )
    
    # Keep call alive (hangup will be sent from WebSocket handler)
    
    twiml_str = str(response)
    logger.info(f"Returning Media Streams TwiML: {twiml_str[:300]}")
    return Response(content=twiml_str, media_type="application/xml")


@router.websocket("/stream")
async def media_streams_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for Twilio Media Streams.
    
    Handles bidirectional audio streaming:
    1. Receives audio from Twilio
    2. Sends to Deepgram for STT
    3. Processes transcripts with LLM
    4. Generates TTS with ElevenLabs
    5. Sends audio back to Twilio
    
    Args:
        websocket: WebSocket connection
        db: Database session
    """
    await websocket.accept()
    logger.info("Media Streams WebSocket connection accepted")
    
    # State tracking
    stream_sid = None
    call_sid = None
    from_number = None
    to_number = None
    restaurant_id = None
    restaurant_name = None
    audio_format = None
    
    # Deepgram connection
    deepgram_connection = None
    current_transcript = ""
    is_speaking = False
    is_listening = False  # Whether we're listening for user input
    
    # Conversation state
    conversation_context = {}
    conversation_messages = []
    
    try:
        # Initialize Deepgram connection
        transcript_buffer = []
        final_transcript = ""
        
        async def on_deepgram_message(text: str, is_final: bool):
            """Handle transcription from Deepgram."""
            nonlocal current_transcript, final_transcript, is_listening
            
            if is_final:
                final_transcript = text.strip()
                if final_transcript:
                    logger.info(f"Final transcript: {final_transcript}")
                    transcript_buffer.append({"text": final_transcript, "final": True})
                    current_transcript = ""
                    # Process with LLM
                    asyncio.create_task(process_transcript_with_llm(final_transcript))
            else:
                current_transcript = text.strip()
                if current_transcript:
                    # User is speaking - stop TTS if playing
                    is_listening = True
                    logger.debug(f"Interim transcript: {current_transcript}")
        
        async def on_deepgram_error(error: Exception):
            """Handle Deepgram errors."""
            logger.error(f"Deepgram error: {str(error)}")
            await send_sms_fallback()
            await websocket.close()
        
        async def on_deepgram_close():
            """Handle Deepgram connection close."""
            logger.info("Deepgram connection closed")
        
        # Create Deepgram connection
        if deepgram_service.is_enabled():
            deepgram_connection = await deepgram_service.create_live_transcription(
                on_message=on_deepgram_message,
                on_error=on_deepgram_error,
                on_close=on_deepgram_close
            )
        
        if not deepgram_connection:
            logger.error("Failed to create Deepgram connection - sending SMS fallback")
            await send_sms_fallback()
            await websocket.close()
            return
        
        async def process_transcript_with_llm(transcript: str):
            """Process transcript with LLM and generate response."""
            nonlocal is_listening, conversation_context, conversation_messages
            
            try:
                from backend.database import SessionLocal
                from backend.models_platform import RestaurantAccount
                db = SessionLocal()
                try:
                    # Get restaurant account for menu/hours
                    restaurant = db.query(RestaurantAccount).filter(
                        RestaurantAccount.id == restaurant_id
                    ).first()
                    
                    if not restaurant:
                        logger.error(f"Restaurant not found: {restaurant_id}")
                        return
                    
                    # Process with conversation handler
                    result = await conversation_handler.process_message(
                        message=transcript,
                        phone=from_number or "",
                        restaurant_id=restaurant_id,
                        context=conversation_context,
                        db=db
                    )
                finally:
                    db.close()
                
                # Update conversation state
                conversation_context = result.get("context", {})
                conversation_messages.append({"role": "user", "content": transcript})
                conversation_messages.append({"role": "assistant", "content": result.get("message", "")})
                
                # Get response message
                response_message = result.get("message", "I'm sorry, I didn't understand that.")
                
                # Generate TTS and send to Twilio
                await generate_and_send_tts(response_message)
                
            except Exception as e:
                logger.error(f"Error processing transcript with LLM: {str(e)}", exc_info=True)
                await send_sms_fallback()
        
        async def generate_and_send_tts(text: str):
            """Generate TTS audio and send to Twilio."""
            nonlocal is_listening
            
            try:
                if not elevenlabs_service.is_enabled():
                    logger.error("ElevenLabs not available")
                    return
                
                is_listening = False  # We're speaking now
                
                # Generate TTS audio
                async for audio_chunk in elevenlabs_service.text_to_speech_stream(text):
                    # Send audio to Twilio via Media Streams
                    if stream_sid and audio_chunk:
                        # Convert to format Twilio expects (mulaw or linear16)
                        # For now, assume Twilio expects the format we're sending
                        media_message = media_streams_service.create_media_message(
                            audio_bytes=audio_chunk,
                            stream_sid=stream_sid
                        )
                        await websocket.send_text(media_message)
                
                is_listening = True  # Done speaking, ready to listen
                
            except Exception as e:
                logger.error(f"Error generating/sending TTS: {str(e)}", exc_info=True)
        
        async def send_sms_fallback():
            """Send SMS fallback when voice fails."""
            try:
                from backend.database import SessionLocal
                from backend.models_platform import RestaurantAccount
                db = SessionLocal()
                try:
                    restaurant = db.query(RestaurantAccount).filter(
                        RestaurantAccount.id == restaurant_id
                    ).first()
                    
                    if restaurant and from_number:
                        sms_message = (
                            f"Sorry, we're not currently handling voice orders. "
                            f"Please text us your order or call back later. "
                            f"You can also visit our website. - {restaurant.business_name}"
                        )
                        sms_service.send_sms(
                            to=from_number,
                            message=sms_message,
                            from_number=restaurant.twilio_phone_number
                        )
                finally:
                    db.close()
            except Exception as e:
                logger.error(f"Failed to send SMS fallback: {str(e)}")
        
        # Main message loop
        while True:
            try:
                # Receive message from Twilio
                message = await websocket.receive_text()
                
                # Parse Media Streams message
                parsed = media_streams_service.parse_message(message)
                if not parsed:
                    continue
                
                event_type = parsed.get("type")
                event_data = parsed.get("data", {})
                
                if event_type == "connected":
                    logger.info("Media Streams connected")
                
                elif event_type == "start":
                    stream_sid = parsed.get("stream_sid")
                    call_sid = parsed.get("call_sid")
                    
                    # Extract phone numbers from start event
                    # Twilio sends these in the start event metadata
                    custom_params = event_data.get("customParameters", {})
                    from_number = custom_params.get("from") or event_data.get("from")
                    to_number = custom_params.get("to") or event_data.get("to")
                    
                    # Get audio format
                    audio_format = media_streams_service.get_audio_format(parsed)
                    logger.info(f"Stream started: {stream_sid}, format: {audio_format}")
                    
                    # Look up restaurant
                    if to_number:
                        from backend.database import SessionLocal
                        from backend.models_platform import RestaurantAccount
                        db = SessionLocal()
                        try:
                            to_normalized = to_number.strip()
                            if not to_normalized.startswith('+'):
                                to_normalized = '+' + to_normalized
                            
                            restaurant = db.query(RestaurantAccount).filter(
                                RestaurantAccount.twilio_phone_number == to_normalized
                            ).first()
                            
                            if restaurant:
                                restaurant_id = restaurant.id
                                restaurant_name = restaurant.business_name
                                logger.info(f"Restaurant identified: {restaurant.business_name}")
                            else:
                                logger.warning(f"Restaurant not found for: {to_number}")
                                await websocket.close()
                                return
                        finally:
                            db.close()
                    
                    # Initialize conversation
                    conversation_messages = []
                    conversation_context = {}
                
                elif event_type == "media":
                    # Extract audio from media message
                    audio_bytes = media_streams_service.extract_audio_from_media(parsed)
                    
                    if audio_bytes and deepgram_connection:
                        # Convert audio format if needed
                        if audio_format == "mulaw":
                            # Convert mulaw to linear16 for Deepgram
                            linear16_bytes = media_streams_service.mulaw_to_linear16(audio_bytes)
                        else:
                            linear16_bytes = audio_bytes
                        
                        # Send to Deepgram
                        await deepgram_service.send_audio(deepgram_connection, linear16_bytes)
                
                elif event_type == "stop":
                    logger.info("Media Streams stopped")
                    
                    # Save transcript
                    try:
                        from backend.database import SessionLocal
                        from backend.models_platform import RestaurantAccount
                        db = SessionLocal()
                        try:
                            restaurant = db.query(RestaurantAccount).filter(
                                RestaurantAccount.id == restaurant_id
                            ).first()
                            
                            if restaurant and conversation_messages:
                                transcript_service.save_transcript(
                                    db=db,
                                    account_id=restaurant_id,
                                    transcript_type="voice",
                                    customer_phone=from_number or "",
                                    conversation_id=call_sid or "",
                                    messages=conversation_messages,
                                    twilio_phone=to_number,
                                    outcome=None
                                )
                        finally:
                            db.close()
                    except Exception as e:
                        logger.error(f"Failed to save transcript: {str(e)}")
                    
                    # Close Deepgram connection
                    if deepgram_connection:
                        await deepgram_service.close_connection(deepgram_connection)
                    
                    await websocket.close()
                    break
                
                elif event_type == "error":
                    error_msg = event_data.get("message", "Unknown error")
                    logger.error(f"Media Streams error: {error_msg}")
                    await send_sms_fallback()
                    await websocket.close()
                    break
            
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected")
                break
            except Exception as e:
                logger.error(f"Error in Media Streams handler: {str(e)}", exc_info=True)
                await send_sms_fallback()
                await websocket.close()
                break
    
    except Exception as e:
        logger.error(f"Error in Media Streams WebSocket: {str(e)}", exc_info=True)
        await send_sms_fallback()
    finally:
        # Cleanup
        if deepgram_connection:
            await deepgram_service.close_connection(deepgram_connection)
        try:
            await websocket.close()
        except:
            pass


@router.post("/process")
async def process_speech(
    request: Request,
    SpeechResult: Optional[str] = Form(None),
    CallSid: Optional[str] = Form(None),
    From: Optional[str] = Form(None),
    To: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Process speech input from customer.

    Args:
        SpeechResult: Transcribed speech from Twilio
        CallSid: Unique call identifier
        From: Caller's phone number
        To: Twilio phone number called (identifies restaurant)
        db: Database session

    Returns:
        TwiML response
    """
    logger.info(f"Processing speech from {From} to {To}: {SpeechResult}")

    # Normalize phone number (remove spaces, ensure + prefix)
    to_normalized = To.strip() if To else None
    if to_normalized and not to_normalized.startswith('+'):
        to_normalized = '+' + to_normalized

    # Look up which restaurant owns this Twilio number
    from backend.models_platform import RestaurantAccount
    restaurant = db.query(RestaurantAccount).filter(
        RestaurantAccount.twilio_phone_number == to_normalized
    ).first()

    if not restaurant:
        logger.warning(f"No restaurant found for Twilio number {To}")
        response = voice_service.create_error_response(
            "This number is not configured. Please contact support."
        )
        return Response(content=str(response), media_type="application/xml")

    # Handle missing speech
    if not SpeechResult:
        base_url = get_base_url(request)
        response = voice_service.create_error_response(
            "I didn't catch that. Could you please repeat?",
            base_url=base_url
        )
        return Response(content=str(response), media_type="application/xml")

    # Get or create conversation state
    if CallSid not in conversation_state:
        conversation_state[CallSid] = {
            "phone": From,
            "restaurant_id": restaurant.id,
            "context": {},
            "step": "initial",
            "messages": []
        }

    state = conversation_state[CallSid]
    
    # Add user message to transcript
    if SpeechResult:
        state["messages"].append({
            "role": "user",
            "content": SpeechResult,
            "timestamp": datetime.now().isoformat()
        })

    try:
        # Process the speech with AI conversation handler
        result = await conversation_handler.process_message(
            message=SpeechResult,
            phone=From,
            restaurant_id=restaurant.id,
            context=state["context"],
            db=db
        )

        # Update state
        state["context"] = result.get("context", {})
        state["step"] = result.get("next_step", "initial")
        
        # Get response message for transcript
        response_message = result.get("message", "")
        
        # Add assistant response to transcript
        if response_message:
            state["messages"].append({
                "role": "assistant",
                "content": response_message,
                "timestamp": datetime.now().isoformat()
            })

        # Handle different response types
        response_type = result.get("type")

        if response_type == "confirmation":
            # Booking was made successfully
            booking_data = result.get("booking")
            response = voice_service.create_confirmation_response(
                restaurant_name=booking_data["restaurant_name"],
                booking_date=booking_data["booking_date"],
                booking_time=booking_data["booking_time"],
                party_size=booking_data["party_size"],
                customer_name=booking_data["customer_name"],
                confirmation_id=booking_data["confirmation_id"]
            )

        elif response_type == "availability":
            # Show available time slots
            response = voice_service.create_availability_response(
                available_times=result.get("available_times", []),
                requested_date=result.get("requested_date"),
                party_size=result.get("party_size")
            )

        elif response_type == "gather":
            # Need more information from customer
            base_url = get_base_url(request)
            response = voice_service.create_gather_response(
                prompt=result.get("message", "How can I help you?"),
                base_url=base_url
            )

        elif response_type == "goodbye":
            # End conversation
            response = voice_service.create_goodbye_response()
            # Save transcript before cleaning up
            if CallSid in conversation_state:
                state = conversation_state[CallSid]
                try:
                    outcome = None
                    if "booking" in result:
                        outcome = "booking_created"
                    elif "order" in result:
                        outcome = "order_placed"
                    
                    transcript_service.save_transcript(
                        db=db,
                        account_id=restaurant.id,
                        transcript_type="voice",
                        customer_phone=From,
                        conversation_id=CallSid,
                        messages=state.get("messages", []),
                        twilio_phone=To,
                        outcome=outcome
                    )
                except Exception as e:
                    logger.error(f"Failed to save transcript: {str(e)}")
                del conversation_state[CallSid]

        else:
            # Default: gather more input
            base_url = get_base_url(request)
            message = result.get("message", "I'm not sure I understand. Could you rephrase that?")
            response = voice_service.create_gather_response(prompt=message, base_url=base_url)

        return Response(content=str(response), media_type="application/xml")

    except Exception as e:
        logger.error(f"Error processing speech: {str(e)}", exc_info=True)
        response = voice_service.create_error_response(
            "I'm sorry, I encountered an error. Let me transfer you to our main menu."
        )
        return Response(content=str(response), media_type="application/xml")


@router.post("/status")
async def call_status(
    request: Request,
    CallSid: Optional[str] = Form(None),
    CallStatus: Optional[str] = Form(None),
    CallDuration: Optional[str] = Form(None),
    To: Optional[str] = Form(None),
    From: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Handle call status callbacks.

    Args:
        CallSid: Unique call identifier
        CallStatus: Status of the call (completed, failed, busy, etc.)
        CallDuration: Call duration in seconds
        To: Restaurant's Twilio number
        From: Customer's phone number
        db: Database session

    Returns:
        Success response
    """
    logger.info(f"Call {CallSid} status: {CallStatus}")

    # Save transcript and clean up conversation state when call ends
    if CallStatus in ["completed", "failed", "busy", "no-answer"] and CallSid in conversation_state:
        state = conversation_state[CallSid]
        try:
            from backend.models_platform import RestaurantAccount
            restaurant = db.query(RestaurantAccount).filter(
                RestaurantAccount.id == state.get("restaurant_id")
            ).first()
            
            if restaurant:
                duration_seconds = int(CallDuration) if CallDuration else None
                transcript_service.save_transcript(
                    db=db,
                    account_id=restaurant.id,
                    transcript_type="voice",
                    customer_phone=state.get("phone", From or ""),
                    conversation_id=CallSid,
                    messages=state.get("messages", []),
                    twilio_phone=To,
                    duration_seconds=duration_seconds
                )
        except Exception as e:
            logger.error(f"Failed to save transcript on call end: {str(e)}")
        
        del conversation_state[CallSid]

    return {"status": "ok"}


@router.get("/health")
async def voice_health():
    """Health check for voice service."""
    return {
        "service": "voice",
        "enabled": voice_service.enabled,
        "status": "healthy" if voice_service.enabled else "disabled"
    }


# SMS conversation state (in production, use Redis or similar)
sms_conversation_state: Dict[str, Dict[str, Any]] = {}


@router.post("/sms/incoming")
async def sms_incoming(
    To: Optional[str] = Form(None),
    From: Optional[str] = Form(None),
    Body: Optional[str] = Form(None),
    MessageSid: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Handle incoming SMS messages.

    Args:
        To: Twilio phone number that received the SMS (identifies restaurant)
        From: Customer's phone number
        Body: SMS message content
        MessageSid: Unique message identifier
        db: Database session

    Returns:
        TwiML response with reply message
    """
    logger.info(f"SMS received from {From} to {To}: {Body}")

    # Look up which restaurant owns this Twilio number
    from backend.models_platform import RestaurantAccount
    restaurant = db.query(RestaurantAccount).filter(
        RestaurantAccount.twilio_phone_number == To
    ).first()

    if not restaurant:
        logger.warning(f"No restaurant found for Twilio number {To}")
        response = sms_service.create_twiml_response(
            "This number is not configured. Please contact support."
        )
        return Response(content=response, media_type="application/xml")

    # Handle missing body
    if not Body:
        response = sms_service.create_twiml_response(
            "I didn't receive your message. Could you please try again?"
        )
        return Response(content=response, media_type="application/xml")

    # Get or create conversation state for this phone number
    state_key = f"{From}_{To}"  # Unique per customer-restaurant pair
    if state_key not in sms_conversation_state:
        sms_conversation_state[state_key] = {
            "phone": From,
            "restaurant_id": restaurant.id,
            "context": {},
            "step": "initial",
            "last_activity": datetime.now(),
            "messages": [],
            "conversation_id": MessageSid or f"sms_{From}_{To}_{datetime.now().timestamp()}"
        }

    state = sms_conversation_state[state_key]
    state["last_activity"] = datetime.now()
    
    # Add user message to transcript
    if Body:
        state["messages"].append({
            "role": "user",
            "content": Body,
            "timestamp": datetime.now().isoformat()
        })

    try:
        # Process the message with AI conversation handler
        result = await conversation_handler.process_message(
            message=Body,
            phone=From,
            restaurant_id=restaurant.id,
            context=state["context"],
            db=db
        )

        # Update state
        state["context"] = result.get("context", {})
        state["step"] = result.get("next_step", "initial")

        # Get the response message
        response_message = result.get("message", "I'm not sure I understand. Could you rephrase that?")
        
        # Add assistant response to transcript
        state["messages"].append({
            "role": "assistant",
            "content": response_message,
            "timestamp": datetime.now().isoformat()
        })

        # Handle different response types
        response_type = result.get("type")

        if response_type == "confirmation":
            # Order/booking was made successfully
            if "booking" in result:
                booking_data = result.get("booking")
                response_message = f"""✅ Reservation Confirmed!

{restaurant.business_name}
Date: {booking_data['booking_date']}
Time: {booking_data['booking_time']}
Party Size: {booking_data['party_size']}
Name: {booking_data['customer_name']}

Confirmation #: {booking_data['confirmation_id']}

We'll see you then!"""
            elif "order" in result:
                order_data = result.get("order")
                response_message = f"""✅ Order Confirmed!

{restaurant.business_name}
Order #: {order_data.get('order_id', 'N/A')}
Total: ${order_data.get('total', 0):.2f}

{order_data.get('message', 'Your order will be ready soon!')}"""

        elif response_type == "goodbye":
            # End conversation
            response_message = result.get("message", "Thanks for contacting us!")
            # Save transcript before cleaning up
            if state_key in sms_conversation_state:
                try:
                    outcome = None
                    if "booking" in result:
                        outcome = "booking_created"
                    elif "order" in result:
                        outcome = "order_placed"
                    
                    transcript_service.save_transcript(
                        db=db,
                        account_id=restaurant.id,
                        transcript_type="sms",
                        customer_phone=From,
                        conversation_id=state.get("conversation_id", MessageSid or ""),
                        messages=state.get("messages", []),
                        twilio_phone=To,
                        outcome=outcome
                    )
                except Exception as e:
                    logger.error(f"Failed to save SMS transcript: {str(e)}")
                del sms_conversation_state[state_key]

        # Create TwiML response
        response = sms_service.create_twiml_response(response_message)
        return Response(content=response, media_type="application/xml")

    except Exception as e:
        logger.error(f"Error processing SMS: {str(e)}", exc_info=True)
        response = sms_service.create_twiml_response(
            f"Sorry, I encountered an error. Please call us at {restaurant.phone or 'our restaurant'} or try again later."
        )
        return Response(content=response, media_type="application/xml")


@router.get("/sms/health")
async def sms_health():
    """Health check for SMS service."""
    return {
        "service": "sms",
        "enabled": sms_service.enabled,
        "status": "healthy" if sms_service.enabled else "disabled",
        "active_conversations": len(sms_conversation_state)
    }
