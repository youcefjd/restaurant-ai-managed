"""
Voice call webhook endpoints for Twilio Voice API.

Simplified real-time voice AI pipeline:
  Twilio → Deepgram STT → LLM → ElevenLabs TTS → Twilio

Design principles:
  - Simple state machine (LISTENING, PROCESSING, SPEAKING)
  - Stream audio directly without heavy conversion
  - Clean barge-in handling
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, Depends, Request, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from sqlalchemy.orm import Session
from twilio.twiml.voice_response import VoiceResponse, Connect

from backend.database import get_db
from backend.services.deepgram_service import deepgram_service
from backend.services.elevenlabs_service import elevenlabs_service
from backend.services.media_streams_service import media_streams_service
from backend.services.conversation_handler import conversation_handler
from backend.services.transcript_service import transcript_service
from backend.services.sms_service import sms_service
from backend.services.llm_service import llm_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Store call metadata for WebSocket handler
call_metadata: Dict[str, Dict[str, str]] = {}


class CallState(Enum):
    """Voice call state machine states."""
    INITIALIZING = "initializing"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ENDED = "ended"


def get_base_url(request: Request) -> str:
    """Extract base URL from request, handling ngrok/proxy headers."""
    base_url = str(request.base_url).rstrip('/')

    if 'x-forwarded-proto' in request.headers:
        protocol = request.headers['x-forwarded-proto']
        host = request.headers.get('x-forwarded-host') or request.headers.get('host', '')
        if host and not host.startswith('localhost') and not host.startswith('127.0.0.1'):
            base_url = f"{protocol}://{host}"

    return base_url


@router.post("/welcome")
@router.get("/welcome")
async def voice_welcome(request: Request, db: Session = Depends(get_db)):
    """
    Initial webhook when call is received.
    Returns TwiML with Media Streams Start instruction.
    """
    # Extract parameters
    if request.method == "POST":
        form_data = await request.form()
        To = form_data.get("To")
        From = form_data.get("From")
        CallSid = form_data.get("CallSid")
    else:
        To = request.query_params.get("To")
        From = request.query_params.get("From")
        CallSid = request.query_params.get("CallSid")

    logger.info(f"Incoming call: {From} → {To}, CallSid: {CallSid}")

    # Build WebSocket URL
    base_url = get_base_url(request)
    ws_protocol = "wss" if base_url.startswith("https") else "ws"
    ws_base = base_url.replace("https://", "").replace("http://", "")
    ws_url = f"{ws_protocol}://{ws_base}/api/voice/stream"

    # Normalize phone number
    to_normalized = To.strip() if To else None
    if to_normalized and not to_normalized.startswith('+'):
        to_normalized = '+' + to_normalized

    # Store metadata for WebSocket handler
    if CallSid:
        call_metadata[CallSid] = {
            "from": From or "",
            "to": To or "",
            "to_normalized": to_normalized or ""
        }

    # Look up restaurant
    from backend.models_platform import RestaurantAccount
    restaurant = db.query(RestaurantAccount).filter(
        RestaurantAccount.twilio_phone_number == to_normalized
    ).first()

    if not restaurant:
        logger.warning(f"No restaurant for number: {To}")
        response = VoiceResponse()
        response.say("This number is not configured. Please contact support.", voice='alice')
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    # Check services availability
    if not (deepgram_service.is_enabled() and llm_service.is_enabled() and elevenlabs_service.is_enabled()):
        logger.warning("Voice services unavailable")
        response = VoiceResponse()
        response.say("Sorry, voice service is temporarily unavailable. Please try again later.", voice='alice')
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    # Build TwiML with Media Streams (using Connect for bidirectional audio)
    response = VoiceResponse()
    connect = Connect()
    connect.stream(url=ws_url)
    response.append(connect)

    logger.info(f"Returning TwiML with WebSocket URL: {ws_url}")
    return Response(content=str(response), media_type="application/xml")


@router.websocket("/stream")
async def voice_stream(websocket: WebSocket):
    """
    WebSocket endpoint for Twilio Media Streams.

    Handles real-time bidirectional audio:
    1. Receive audio from Twilio (mulaw 8kHz)
    2. Convert to linear16, send to Deepgram
    3. Process transcript with LLM
    4. Stream TTS response back to Twilio
    """
    await websocket.accept()
    logger.info("WebSocket connected")

    # Get event loop for thread-safe callback scheduling
    loop = asyncio.get_event_loop()

    # Call state
    state = CallState.INITIALIZING
    stream_sid: Optional[str] = None
    call_sid: Optional[str] = None
    from_number: Optional[str] = None
    to_number: Optional[str] = None
    restaurant_id: Optional[int] = None
    restaurant_name: Optional[str] = None

    # Deepgram connection
    deepgram_conn = None

    # Conversation state
    conversation_messages = []
    conversation_context = {}
    current_transcript = ""
    is_speaking = False  # User is speaking (barge-in detection)
    tts_active = False  # Track if TTS is currently playing
    barge_in_threshold = 3  # Minimum words to trigger barge-in

    # Task management
    tts_task: Optional[asyncio.Task] = None
    ws_connected = True  # Track WebSocket connection state
    call_ended = False  # Flag to signal call should end
    processing_lock = asyncio.Lock()  # Prevent parallel LLM calls

    # Transcript debouncing - wait for complete sentences
    transcript_buffer = []  # Buffer to collect transcript segments
    debounce_task: Optional[asyncio.Task] = None
    DEBOUNCE_DELAY = 1.2  # Wait 1.2 seconds after last transcript before processing

    async def send_tts(text: str):
        """Generate and send TTS audio to Twilio."""
        nonlocal state, is_speaking, ws_connected, tts_active

        if not stream_sid:
            logger.warning("No stream_sid, cannot send TTS")
            return

        if not ws_connected:
            logger.warning("WebSocket disconnected, cannot send TTS")
            return

        state = CallState.SPEAKING
        tts_active = True
        is_speaking = False  # Reset barge-in flag when starting TTS
        logger.info(f"TTS: {text[:80]}...")

        try:
            chunk_count = 0
            async for audio_chunk in elevenlabs_service.text_to_speech_stream(text):
                # Check if WebSocket is still connected
                if not ws_connected:
                    logger.warning("WebSocket disconnected during TTS, stopping")
                    break

                # Check for barge-in (only if user is actively speaking)
                if is_speaking:
                    logger.info("Barge-in detected, stopping TTS")
                    # Clear Twilio audio buffer
                    try:
                        await websocket.send_text(media_streams_service.create_clear_message(stream_sid))
                    except Exception as e:
                        logger.warning(f"Failed to send clear message: {e}")
                    break

                # Send audio chunk to Twilio
                try:
                    msg = media_streams_service.create_media_message(stream_sid, audio_chunk)
                    await websocket.send_text(msg)
                    chunk_count += 1
                except Exception as e:
                    logger.warning(f"Failed to send TTS chunk: {e}")
                    ws_connected = False
                    break

                # Small delay to prevent overwhelming the connection
                if chunk_count > 2:
                    await asyncio.sleep(0.01)

            logger.info(f"TTS complete: {chunk_count} chunks sent")

        except Exception as e:
            logger.error(f"TTS error: {e}")
        finally:
            state = CallState.LISTENING
            tts_active = False
            is_speaking = False

    async def process_transcript(transcript: str):
        """Process transcript with LLM and send TTS response."""
        nonlocal state, conversation_context, conversation_messages, deepgram_conn, ws_connected, call_ended

        if not transcript.strip():
            return

        # Use lock to prevent parallel LLM calls
        async with processing_lock:
            state = CallState.PROCESSING
            logger.info(f"Processing: {transcript}")

            try:
                from backend.database import SessionLocal
                db = SessionLocal()
                try:
                    result = await conversation_handler.process_message(
                        message=transcript,
                        phone=from_number or "",
                        restaurant_id=restaurant_id,
                        context=conversation_context,
                        conversation_history=conversation_messages,
                        db=db
                    )
                finally:
                    db.close()

                # Update conversation state
                conversation_context = result.get("context", {})
                response_message = result.get("message", "I didn't understand that. Could you repeat?")
                response_type = result.get("type", "gather")

                # Store for transcript
                conversation_messages.append({"role": "user", "content": transcript})
                conversation_messages.append({"role": "assistant", "content": response_message})

                # Track unclear exchanges for graceful hangup
                unclear_count = conversation_context.get("unclear_count", 0)
                if response_type == "unclear" or "didn't catch that" in response_message.lower() or "could you repeat" in response_message.lower():
                    unclear_count += 1
                    conversation_context["unclear_count"] = unclear_count
                    logger.info(f"Unclear exchange count: {unclear_count}")

                    if unclear_count >= 3:
                        # Too many unclear exchanges - gracefully end call
                        response_message = "I'm having trouble understanding. Please call the restaurant directly for assistance. Thank you for calling, goodbye!"
                        response_type = "hangup"
                else:
                    # Reset unclear count on successful exchange
                    conversation_context["unclear_count"] = 0

                # Send TTS response
                await send_tts(response_message)

                # Reconnect Deepgram if it was closed during processing
                if deepgram_conn and deepgram_conn.is_closed:
                    logger.info("Reconnecting Deepgram after timeout...")
                    deepgram_conn = await deepgram_service.create_live_connection(
                        on_transcript=on_transcript,
                        on_error=on_deepgram_error,
                        on_close=on_deepgram_close,
                        sample_rate=8000,
                        encoding="linear16",
                        channels=1
                    )
                    if deepgram_conn:
                        logger.info("Deepgram reconnected successfully")
                    else:
                        logger.warning("Failed to reconnect Deepgram")

                # Handle call ending
                if response_type in ["goodbye", "hangup"]:
                    logger.info(f"Call ending: {response_type}")
                    # Wait for TTS audio to finish playing on Twilio's side
                    # TTS chunks are sent but playback is async - give it time to complete
                    await asyncio.sleep(2.0)
                    # Signal that call should end (main loop will close websocket)
                    call_ended = True
                    ws_connected = False
                    return

            except Exception as e:
                logger.error(f"Processing error: {e}", exc_info=True)
                await send_tts("I'm sorry, I had trouble understanding. Could you repeat that?")
            finally:
                state = CallState.LISTENING

    async def process_debounced_transcript():
        """Process accumulated transcript after debounce delay."""
        nonlocal transcript_buffer

        try:
            # Wait for the debounce delay
            await asyncio.sleep(DEBOUNCE_DELAY)

            # Combine all buffered transcripts
            if transcript_buffer:
                combined = " ".join(transcript_buffer)
                transcript_buffer = []  # Clear buffer
                logger.info(f"Processing combined transcript: {combined}")
                await process_transcript(combined)
        except asyncio.CancelledError:
            # Debounce was cancelled because more transcript came in
            pass

    def on_transcript(text: str, is_final: bool):
        """Handle transcription from Deepgram (called from thread)."""
        nonlocal current_transcript, is_speaking, transcript_buffer, debounce_task, tts_active

        if is_final and text.strip():
            logger.info(f"Final transcript segment: {text}")
            current_transcript = text
            is_speaking = False

            # Add to buffer
            transcript_buffer.append(text.strip())

            # Cancel existing debounce future if any
            if debounce_task:
                debounce_task.cancel()

            # Schedule new debounce task
            debounce_task = asyncio.run_coroutine_threadsafe(
                process_debounced_transcript(), loop
            )

        elif text.strip():
            # Interim result - only trigger barge-in if:
            # 1. TTS is actively playing
            # 2. User has said at least 3 words (to filter noise/short sounds)
            word_count = len(text.strip().split())
            if tts_active and word_count >= barge_in_threshold:
                logger.info(f"Barge-in trigger: '{text}' ({word_count} words)")
                is_speaking = True
            logger.debug(f"Interim: {text}")

    def on_deepgram_error(error: Exception):
        """Handle Deepgram errors - log but don't crash, TTS can still work."""
        nonlocal deepgram_conn
        error_str = str(error)
        if "timeout" in error_str.lower() or "1011" in error_str:
            logger.warning(f"Deepgram timeout (expected during LLM processing): {error}")
        else:
            logger.error(f"Deepgram error: {error}")

    def on_deepgram_close():
        """Handle Deepgram connection close."""
        logger.info("Deepgram connection closed")

    try:
        # Create Deepgram connection
        deepgram_conn = await deepgram_service.create_live_connection(
            on_transcript=on_transcript,
            on_error=on_deepgram_error,
            on_close=on_deepgram_close,
            sample_rate=8000,
            encoding="linear16",
            channels=1
        )

        if not deepgram_conn:
            logger.error("Failed to create Deepgram connection")
            await websocket.close()
            return

        # Main message loop
        while True:
            # Check if call has ended
            if call_ended:
                logger.info("Call ended flag set, exiting loop")
                break

            try:
                raw_message = await websocket.receive_text()
                msg = media_streams_service.parse_message(raw_message)

                if not msg:
                    continue

                event = msg.get("event")

                if event == "connected":
                    logger.info("Twilio Media Streams connected")

                elif event == "start":
                    stream_sid = msg.get("stream_sid")
                    call_sid = msg.get("call_sid")

                    # Get phone numbers from stored metadata
                    if call_sid and call_sid in call_metadata:
                        meta = call_metadata[call_sid]
                        from_number = meta.get("from")
                        to_number = meta.get("to")

                    logger.info(f"Stream started: {stream_sid}, from: {from_number}")

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
                                logger.info(f"Restaurant: {restaurant_name}")
                            else:
                                logger.warning(f"Restaurant not found for: {to_number}")
                                await websocket.close()
                                return
                        finally:
                            db.close()

                    state = CallState.LISTENING

                    # Send greeting
                    if restaurant_name:
                        greeting = f"Hi, thanks for calling {restaurant_name}. How can I help you today?"
                        tts_task = asyncio.create_task(send_tts(greeting))

                elif event == "media":
                    # Extract and process audio
                    audio_bytes = media_streams_service.extract_audio(msg)
                    if audio_bytes and deepgram_conn:
                        # Convert mulaw to linear16 for Deepgram
                        linear16 = media_streams_service.mulaw_to_linear16(audio_bytes)
                        await deepgram_conn.send_audio(linear16)

                elif event == "stop":
                    logger.info("Stream stopped")
                    ws_connected = False

                    # Clean up metadata
                    if call_sid and call_sid in call_metadata:
                        del call_metadata[call_sid]

                    # Save transcript
                    if conversation_messages and restaurant_id:
                        try:
                            from backend.database import SessionLocal
                            db = SessionLocal()
                            try:
                                transcript_service.save_transcript(
                                    db=db,
                                    account_id=restaurant_id,
                                    transcript_type="voice",
                                    customer_phone=from_number or "",
                                    conversation_id=call_sid or "",
                                    messages=conversation_messages,
                                    twilio_phone=to_number
                                )
                            finally:
                                db.close()
                        except Exception as e:
                            logger.error(f"Failed to save transcript: {e}")

                    break

            except WebSocketDisconnect:
                logger.info("WebSocket disconnected")
                ws_connected = False
                break
            except RuntimeError as e:
                # Handle "WebSocket is not connected" error gracefully
                if "not connected" in str(e).lower():
                    logger.info("WebSocket closed, ending session")
                else:
                    logger.error(f"WebSocket runtime error: {e}")
                ws_connected = False
                break
            except Exception as e:
                logger.error(f"Message handling error: {e}", exc_info=True)
                ws_connected = False
                break

    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)

    finally:
        # Cleanup
        if call_sid and call_sid in call_metadata:
            del call_metadata[call_sid]

        if deepgram_conn:
            await deepgram_conn.close()

        if tts_task and not tts_task.done():
            tts_task.cancel()

        try:
            await websocket.close()
        except:
            pass

        logger.info("WebSocket session ended")


@router.post("/status")
async def call_status(
    CallSid: Optional[str] = Form(None),
    CallStatus: Optional[str] = Form(None),
    CallDuration: Optional[str] = Form(None)
):
    """Handle call status callbacks."""
    logger.info(f"Call {CallSid} status: {CallStatus}, duration: {CallDuration}s")

    # Clean up any lingering metadata
    if CallSid and CallSid in call_metadata:
        del call_metadata[CallSid]

    return {"status": "ok"}


@router.get("/health")
async def voice_health():
    """Health check for voice service."""
    return {
        "service": "voice",
        "deepgram": deepgram_service.is_enabled(),
        "elevenlabs": elevenlabs_service.is_enabled(),
        "llm": llm_service.is_enabled(),
        "status": "healthy" if all([
            deepgram_service.is_enabled(),
            elevenlabs_service.is_enabled(),
            llm_service.is_enabled()
        ]) else "degraded"
    }
