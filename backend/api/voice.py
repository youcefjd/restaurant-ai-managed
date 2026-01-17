"""
Voice call webhook endpoints for Twilio Voice API.

Handles incoming calls via Twilio Media Streams (WebSocket) for real-time
audio streaming, processes speech-to-text, and manages conversation flow.
"""

import os
import json
import io
import time
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, Request, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from sqlalchemy.orm import Session
from twilio.twiml.voice_response import VoiceResponse, Start

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
from backend.services.voice_monitoring import voice_monitoring

router = APIRouter()
logger = logging.getLogger(__name__)

# Store conversation state (in production, use Redis or similar)
conversation_state: Dict[str, Dict[str, Any]] = {}

# Store call metadata (phone numbers) keyed by CallSid
# This allows WebSocket handler to retrieve phone numbers from the initial webhook
call_metadata: Dict[str, Dict[str, str]] = {}


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
@router.get("/welcome")
async def voice_welcome(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Initial webhook when call is received.
    Returns TwiML with Media Streams Start instruction.
    
    Handles both POST (form data) and GET (query params) for Twilio compatibility.

    Args:
        request: FastAPI request object (to get base URL and parameters)
        db: Database session
    """
    # Extract parameters from either form data (POST) or query params (GET)
    if request.method == "POST":
        form_data = await request.form()
        To = form_data.get("To")
        From = form_data.get("From")
        CallSid = form_data.get("CallSid")
    else:  # GET
        To = request.query_params.get("To")
        From = request.query_params.get("From")
        CallSid = request.query_params.get("CallSid")
    
    logger.info(f"Voice call received from {From} to {To}, CallSid: {CallSid} (method: {request.method})")

    # Get base URL from request (for WebSocket URL)
    base_url = get_base_url(request)
    
    # Convert HTTP(S) to WS(S) for WebSocket URL
    # IMPORTANT: Twilio requires WSS (secure WebSocket) for production
    # Use WSS if base URL is HTTPS, otherwise WS (for local development)
    ws_protocol = "wss" if base_url.startswith("https") else "ws"
    ws_base = base_url.replace("https://", "").replace("http://", "")
    ws_url = f"{ws_protocol}://{ws_base}/api/voice/stream"
    
    logger.info(f"Voice call - From: {From}, To: {To}, CallSid: {CallSid}")
    logger.info(f"Base URL: {base_url}, WebSocket URL: {ws_url}")

    # Normalize phone number (remove spaces, ensure + prefix)
    to_normalized = To.strip() if To else None
    if to_normalized and not to_normalized.startswith('+'):
        to_normalized = '+' + to_normalized

    # Store call metadata for WebSocket handler to retrieve
    if CallSid:
        call_metadata[CallSid] = {
            "from": From or "",
            "to": To or "",
            "to_normalized": to_normalized or ""
        }
        logger.info(f"Stored call metadata for CallSid {CallSid}")

    # Look up which restaurant owns this Twilio number
    from backend.models_platform import RestaurantAccount
    restaurant = db.query(RestaurantAccount).filter(
        RestaurantAccount.twilio_phone_number == to_normalized
    ).first()
    
    logger.info(f"Restaurant found: {restaurant.business_name if restaurant else 'None'}")

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
    
    # Start Media Streams - use direct method to avoid malformed XML
    start = Start()
    # Use the stream() method directly with parameters (not a Stream object)
    start.stream(url=ws_url, track='both_tracks')
    response.append(start)
    
    # Add a brief pause to keep call alive while WebSocket connects
    # This prevents immediate hangup if WebSocket connection is delayed
    response.pause(length=1)  # 1 second pause
    
    # Don't use Twilio's Say verb - we'll use ElevenLabs for all speech via WebSocket
    # This ensures consistent voice throughout the call
    # The initial greeting will be sent via ElevenLabs once the WebSocket connects
    
    # Keep call alive (hangup will be sent from WebSocket handler)
    # With Media Streams, the call stays open as long as the WebSocket is connected
    
    twiml_str = str(response)
    logger.info(f"Returning Media Streams TwiML (first 500 chars): {twiml_str[:500]}")
    logger.info(f"Full TwiML response: {twiml_str}")
    
    # Log important details for debugging
    logger.info(f"Services status - Deepgram: {deepgram_service.is_enabled()}, "
                f"LLM: {llm_service.is_enabled()}, "
                f"ElevenLabs: {elevenlabs_service.is_enabled()}")
    
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
    try:
        await websocket.accept()
        logger.info("✅ Media Streams WebSocket connection accepted from Twilio")
        logger.info(f"WebSocket URL: {websocket.url if hasattr(websocket, 'url') else 'N/A'}")
        logger.info(f"WebSocket headers: {dict(websocket.headers) if hasattr(websocket, 'headers') else 'N/A'}")
    except Exception as accept_error:
        logger.error(f"❌ Failed to accept WebSocket connection: {str(accept_error)}", exc_info=True)
        return
    
    # Start monitoring for this call
    call_sid_temp = None  # Will be set from start event
    monitoring_metrics = None
    
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
    should_close = False  # Flag to signal main loop to close connection
    
    # Connection health tracking
    last_pong_time = None
    connection_healthy = True
    keepalive_task = None
    last_audio_received_time = None
    last_audio_sent_time = None
    consecutive_errors = 0
    max_consecutive_errors = 5
    
    # Conversation state
    conversation_context = {}
    conversation_messages = []
    
    # Define send_sms_fallback early so it can be used in error handlers
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
    
    try:
        # Initialize Deepgram connection
        transcript_buffer = []
        final_transcript = ""
        
        def on_deepgram_message(text: str, is_final: bool):
            """Handle transcription from Deepgram (synchronous callback)."""
            nonlocal current_transcript, final_transcript, is_listening, is_speaking
            
            if is_final:
                final_transcript = text.strip()
                if final_transcript:
                    logger.info(f"Final transcript: {final_transcript}")
                    transcript_buffer.append({"text": final_transcript, "final": True})
                    current_transcript = ""
                    # User finished speaking - ensure we're listening
                    is_listening = True
                    is_speaking = False
                    
                    # Mark ASR first transcript for monitoring
                    if call_sid:
                        voice_monitoring.mark_asr_first_transcript(call_sid)
                    
                    # Process with LLM (async task)
                    asyncio.create_task(process_transcript_with_llm(final_transcript))
            else:
                current_transcript = text.strip()
                if current_transcript:
                    # User is speaking - detect barge-in and stop TTS if playing
                    is_speaking = True
                    is_listening = True  # User is speaking, so we should be listening
                    
                    # Barge-in detection: if TTS is playing, stop it immediately
                    if not is_listening:  # This means TTS was playing
                        logger.info(f"Barge-in detected: User started speaking during TTS playback")
                        # Schedule async task to clear audio buffer
                        try:
                            loop = asyncio.get_running_loop()
                            asyncio.create_task(clear_audio_buffer_on_bargein())
                        except RuntimeError:
                            pass
                    
                    logger.debug(f"Interim transcript: {current_transcript}")
        
        async def clear_audio_buffer_on_bargein():
            """Clear Twilio audio buffer when user interrupts (barge-in)."""
            nonlocal stream_sid
            try:
                if stream_sid:
                    clear_message = media_streams_service.create_clear_message(stream_sid)
                    await websocket.send_text(clear_message)
                    logger.info("Cleared Twilio audio buffer due to barge-in")
            except Exception as e:
                logger.error(f"Failed to clear audio buffer on barge-in: {str(e)}")
        
        def on_deepgram_error(error: Exception):
            """Handle Deepgram errors (synchronous callback)."""
            nonlocal should_close, deepgram_connection
            error_str = str(error).lower()
            
            # Check if error is transient (network, timeout) vs permanent (auth, config)
            is_transient = any(keyword in error_str for keyword in [
                'timeout', 'connection', 'network', 'unavailable', 'temporary',
                'retry', 'rate limit', '429', '503', '502', '504'
            ])
            
            if is_transient:
                logger.warning(f"Transient Deepgram error: {str(error)} - will attempt recovery")
                # Don't close immediately for transient errors - try to reconnect
                # Schedule reconnection attempt
                try:
                    loop = asyncio.get_running_loop()
                    asyncio.create_task(reconnect_deepgram())
                except RuntimeError:
                    pass
            else:
                logger.error(f"Permanent Deepgram error: {str(error)}")
                # Set flag to close connection - main loop will handle it
                should_close = True
                # Try to schedule async fallback in event loop (if available)
                try:
                    loop = asyncio.get_running_loop()
                    asyncio.create_task(send_sms_fallback())
                except RuntimeError:
                    # No event loop running, main loop will handle fallback
                    pass
                except Exception as e:
                    logger.error(f"Failed to schedule SMS fallback: {str(e)}")
        
        def on_deepgram_close():
            """Handle Deepgram connection close (synchronous callback)."""
            nonlocal deepgram_connection
            logger.info("Deepgram connection closed")
            # Try to reconnect if connection was healthy
            if connection_healthy and not should_close:
                try:
                    loop = asyncio.get_running_loop()
                    asyncio.create_task(reconnect_deepgram())
                except RuntimeError:
                    pass
        
        async def reconnect_deepgram(max_retries: int = 3):
            """Reconnect to Deepgram with exponential backoff."""
            nonlocal deepgram_connection, should_close
            
            for attempt in range(max_retries):
                wait_time = min(2 ** attempt, 10)  # Exponential backoff, max 10 seconds
                logger.info(f"Attempting to reconnect Deepgram (attempt {attempt + 1}/{max_retries}) after {wait_time}s")
                
                await asyncio.sleep(wait_time)
                
                if should_close:
                    logger.info("Skipping Deepgram reconnection - connection marked for closure")
                    return
                
                try:
                    # Close old connection if exists
                    if deepgram_connection:
                        await deepgram_service.close_connection(deepgram_connection)
                    
                    # Create new connection
                    new_connection = deepgram_service.create_live_transcription(
                        on_message=on_deepgram_message,
                        on_error=on_deepgram_error,
                        on_close=on_deepgram_close
                    )
                    
                    if new_connection:
                        deepgram_connection = new_connection
                        logger.info("Successfully reconnected to Deepgram")
                        return
                    else:
                        logger.warning(f"Deepgram reconnection attempt {attempt + 1} failed")
                        
                except Exception as e:
                    logger.error(f"Error during Deepgram reconnection attempt {attempt + 1}: {str(e)}")
            
            # All retries failed
            logger.error("Failed to reconnect Deepgram after all retries - sending SMS fallback")
            await send_sms_fallback()
            should_close = True
        
        # Create Deepgram connection with retry logic
        deepgram_connection = None
        if deepgram_service.is_enabled():
            max_initial_retries = 2
            for attempt in range(max_initial_retries):
                try:
                    deepgram_connection = deepgram_service.create_live_transcription(
                        on_message=on_deepgram_message,
                        on_error=on_deepgram_error,
                        on_close=on_deepgram_close
                    )
                    if deepgram_connection:
                        break
                    elif attempt < max_initial_retries - 1:
                        wait_time = 1 * (attempt + 1)  # 1s, 2s
                        logger.warning(f"Initial Deepgram connection failed, retrying in {wait_time}s...")
                        await asyncio.sleep(wait_time)
                except Exception as e:
                    logger.error(f"Exception creating Deepgram connection (attempt {attempt + 1}): {str(e)}")
                    if attempt < max_initial_retries - 1:
                        await asyncio.sleep(1 * (attempt + 1))
        
        if not deepgram_connection:
            logger.error("Failed to create Deepgram connection after retries")
            logger.error("This will cause the call to hang up - check Deepgram API key and service availability")
            # Don't close WebSocket immediately - let Twilio handle it
            # Closing here causes immediate hangup
            try:
                await send_sms_fallback()
            except Exception as sms_error:
                logger.error(f"Failed to send SMS fallback: {str(sms_error)}")
            # Keep WebSocket open briefly to allow Twilio to receive any messages
            await asyncio.sleep(1)
            await websocket.close()
            return
        
        # Connection health monitoring task
        async def monitor_connection_health():
            """Monitor connection health and detect stale connections."""
            nonlocal connection_healthy, should_close, last_audio_received_time, consecutive_errors
            
            try:
                while not should_close:
                    await asyncio.sleep(30)  # Check health every 30 seconds
                    
                    if should_close:
                        break
                    
                    current_time = time.time()
                    
                    # Check if we've received audio recently (within last 60 seconds)
                    # If no audio for 60+ seconds, connection might be stale
                    if last_audio_received_time:
                        time_since_audio = current_time - last_audio_received_time
                        if time_since_audio > 60:
                            logger.warning(
                                f"No audio received for {time_since_audio:.1f}s - "
                                "connection may be stale"
                            )
                            # Don't close immediately, but mark as potentially unhealthy
                            if time_since_audio > 120:  # 2 minutes without audio
                                logger.error("Connection appears stale - no audio for 2+ minutes")
                                connection_healthy = False
                                should_close = True
                                break
                    
                    # Check consecutive errors
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error(
                            f"Too many consecutive errors ({consecutive_errors}) - "
                            "marking connection as unhealthy"
                        )
                        connection_healthy = False
                        should_close = True
                        break
                    
                    # Reset error count if connection seems healthy
                    if consecutive_errors > 0 and last_audio_received_time:
                        time_since_audio = current_time - last_audio_received_time
                        if time_since_audio < 10:  # Recent audio activity
                            consecutive_errors = 0
                            connection_healthy = True
                            
            except asyncio.CancelledError:
                logger.debug("Connection health monitoring task cancelled")
            except Exception as e:
                logger.error(f"Error in connection health monitoring: {str(e)}")
        
        # WebSocket keepalive task - send ping every 20 seconds
        async def websocket_keepalive():
            """Send periodic ping to keep WebSocket connection alive."""
            nonlocal should_close, consecutive_errors, connection_healthy
            try:
                while not should_close and connection_healthy:
                    await asyncio.sleep(20)  # Send ping every 20 seconds
                    if not should_close and connection_healthy:
                        try:
                            # FastAPI WebSocket doesn't have explicit ping/pong,
                            # but we can send a lightweight message to keep connection alive
                            # Twilio Media Streams doesn't require explicit ping, but
                            # we'll monitor connection health by checking if we can still send
                            await websocket.send_text(json.dumps({"event": "ping"}))
                            logger.debug("Sent WebSocket keepalive ping")
                        except Exception as ping_error:
                            logger.warning(f"Failed to send keepalive ping: {str(ping_error)}")
                            consecutive_errors += 1
                            if consecutive_errors >= max_consecutive_errors:
                                should_close = True
                                break
            except asyncio.CancelledError:
                logger.debug("WebSocket keepalive task cancelled")
            except Exception as e:
                logger.error(f"Error in keepalive task: {str(e)}")
        
        # Start health monitoring task
        health_monitor_task = asyncio.create_task(monitor_connection_health())
        
        # Start keepalive and health monitoring tasks
        keepalive_task = asyncio.create_task(websocket_keepalive())
        
        async def process_transcript_with_llm(transcript: str):
            """Process transcript with LLM and generate response."""
            nonlocal is_listening, conversation_context, conversation_messages
            
            # Mark LLM start for monitoring
            if call_sid:
                voice_monitoring.mark_llm_start(call_sid)
            
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
                        if call_sid:
                            voice_monitoring.add_error(call_sid, f"Restaurant not found: {restaurant_id}")
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
                
                # Mark LLM end for monitoring
                if call_sid:
                    voice_monitoring.mark_llm_end(call_sid)
                
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
                if call_sid:
                    voice_monitoring.add_error(call_sid, f"LLM processing error: {str(e)}")
                await send_sms_fallback()
        
        async def generate_and_send_tts(text: str):
            """Generate TTS audio and send to Twilio."""
            nonlocal is_listening, stream_sid
            
            tts_start_time = time.time()
            try:
                if not elevenlabs_service.is_enabled():
                    logger.error("ElevenLabs not available")
                    return
                
                if not stream_sid:
                    logger.warning("No stream_sid available, cannot send TTS")
                    return
                
                is_listening = False  # We're speaking now
                
                logger.info(f"Starting TTS generation for text: {text[:50]}...")
                
                # Buffer to accumulate MP3 chunks
                mp3_buffer = io.BytesIO()
                chunk_count = 0
                
                # Mark TTS first chunk for monitoring
                if call_sid:
                    voice_monitoring.mark_tts_first_chunk(call_sid)
                
                logger.info("Starting ElevenLabs TTS stream...")
                async for audio_chunk in elevenlabs_service.text_to_speech_stream(text):
                    # Check if user started speaking (barge-in detection)
                    # is_speaking is set to True when Deepgram detects user speech
                    if is_speaking or is_listening:
                        logger.info("User interrupted TTS playback (barge-in detected)")
                        # Clear Twilio audio buffer immediately
                        if stream_sid:
                            try:
                                clear_message = media_streams_service.create_clear_message(stream_sid)
                                await websocket.send_text(clear_message)
                            except RuntimeError:
                                # WebSocket already closed, ignore
                                logger.debug("WebSocket closed during barge-in clear")
                        # Stop generating more TTS
                        break
                    
                    if audio_chunk:
                        mp3_buffer.write(audio_chunk)
                        chunk_count += 1
                
                tts_generation_time = time.time() - tts_start_time
                logger.info(f"TTS generation completed: {chunk_count} chunks in {tts_generation_time:.2f}s")
                
                # Check if we got any audio data
                mp3_size = mp3_buffer.tell()
                if mp3_size == 0:
                    logger.warning("No MP3 audio data received from ElevenLabs")
                    return
                
                if not stream_sid:
                    logger.warning("No stream_sid available, cannot send audio")
                    return
                
                # Convert accumulated MP3 to mulaw format that Twilio expects
                # Do this ASAP to start sending audio quickly
                mp3_buffer.seek(0)
                mp3_data = mp3_buffer.read()
                logger.info(f"MP3 data size: {len(mp3_data)} bytes, starting conversion to mulaw")
                
                conversion_start = time.time()
                try:
                    # Convert MP3 → mulaw (8kHz mono PCM)
                    logger.info("Calling mp3_to_mulaw conversion...")
                    mulaw_audio = media_streams_service.mp3_to_mulaw(mp3_data, sample_rate=8000)
                    conversion_time = time.time() - conversion_start
                    logger.info(f"MP3 to mulaw conversion completed in {conversion_time:.2f}s, output size: {len(mulaw_audio)} bytes")
                        
                    # Validate conversion
                    if not media_streams_service.validate_audio_format(mulaw_audio, "mulaw"):
                        logger.warning("Converted audio format validation failed")
                    
                    # Send mulaw audio to Twilio via Media Streams in chunks
                    # CRITICAL: Send first chunk IMMEDIATELY to keep connection alive
                    # Then send remaining chunks quickly
                    chunk_size = 1600  # 200ms of audio at 8kHz
                    total_sent = 0
                    send_chunk_count = 0
                    base_timestamp = int(time.time() * 1000)  # Base timestamp in milliseconds
                    sample_rate = 8000  # 8kHz sample rate
                    
                    try:
                        for i in range(0, len(mulaw_audio), chunk_size):
                            audio_chunk = mulaw_audio[i:i + chunk_size]
                            if not audio_chunk:
                                break
                            
                            # Calculate timestamp for this chunk
                            chunk_timestamp = base_timestamp + int((i / sample_rate) * 1000)
                            
                            # Check if WebSocket is still open
                            try:
                                media_message = media_streams_service.create_media_message(
                                    audio_bytes=audio_chunk,
                                    stream_sid=stream_sid,
                                    timestamp=str(chunk_timestamp)
                                )
                                await websocket.send_text(media_message)
                                total_sent += len(audio_chunk)
                                send_chunk_count += 1
                                
                                # Send first few chunks with no delay to establish connection
                                # Then minimal delay for remaining chunks
                                if send_chunk_count > 3 and i + chunk_size < len(mulaw_audio):
                                    await asyncio.sleep(0.002)  # 2ms delay - very minimal
                            except RuntimeError as ws_err:
                                logger.warning(f"WebSocket closed while sending chunk {send_chunk_count}: {str(ws_err)}")
                                break
                        
                        logger.info(f"✅ Successfully sent {total_sent}/{len(mulaw_audio)} bytes of mulaw audio to Twilio in {send_chunk_count} chunks")
                    except Exception as send_error:
                        # Handle any errors during sending
                        logger.error(f"Error sending audio chunks: {str(send_error)}", exc_info=True)
                        return
                    
                    # Update last audio sent time for health monitoring
                    last_audio_sent_time = time.time()
                    connection_healthy = True
                    
                    # Mark TTS end for monitoring
                    if call_sid:
                        voice_monitoring.mark_tts_end(call_sid)
                        
                except FileNotFoundError as ffmpeg_error:
                    # ffprobe/ffmpeg not found - this is a configuration issue
                    logger.error(f"ffmpeg/ffprobe not found: {str(ffmpeg_error)}")
                    logger.error("Please install ffmpeg to enable voice TTS. See error message above for installation instructions.")
                    # Don't try fallback - it won't work without ffmpeg
                    return
                except Exception as conv_error:
                        logger.error(f"Failed to convert MP3 to mulaw: {str(conv_error)}", exc_info=True)
                        # Try to send raw audio as fallback (may not work, but worth trying)
                        # But first check if websocket is still open
                        try:
                            logger.warning("Attempting to send raw MP3 as fallback (may fail)")
                            media_message = media_streams_service.create_media_message(
                                audio_bytes=mp3_data,
                                stream_sid=stream_sid
                            )
                            await websocket.send_text(media_message)
                        except RuntimeError as ws_error:
                            # WebSocket is already closed
                            logger.warning(f"WebSocket already closed, cannot send fallback audio: {str(ws_error)}")
                            return
                        except Exception as send_error:
                            logger.error(f"Failed to send fallback audio: {str(send_error)}")
                            return
                
                is_listening = True  # Done speaking, ready to listen
                
            except Exception as e:
                logger.error(f"Error generating/sending TTS: {str(e)}", exc_info=True)
                is_listening = True  # Reset listening state on error
        
        # Main message loop
        while True:
            # Check if we should close due to Deepgram error
            if should_close:
                logger.info("Closing connection due to Deepgram error")
                await send_sms_fallback()
                await websocket.close()
                break
            
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
                    
                    # Start monitoring for this call
                    if call_sid:
                        monitoring_metrics = voice_monitoring.start_call(call_sid, stream_sid)
                        logger.info(f"Started monitoring for call {call_sid}")
                    
                    # Extract phone numbers from call metadata (stored in webhook)
                    # Fallback to start event if not found in metadata
                    if call_sid and call_sid in call_metadata:
                        metadata = call_metadata[call_sid]
                        from_number = metadata.get("from")
                        to_number = metadata.get("to")
                        logger.info(f"Retrieved phone numbers from metadata: from={from_number}, to={to_number}")
                    else:
                        # Fallback: try to extract from start event
                        custom_params = event_data.get("customParameters", {}) or event_data.get("start", {}).get("customParameters", {})
                        from_number = custom_params.get("from") or event_data.get("from") or event_data.get("start", {}).get("from")
                        to_number = custom_params.get("to") or event_data.get("to") or event_data.get("start", {}).get("to")
                        logger.warning(f"Phone numbers not found in metadata for CallSid {call_sid}, using fallback")
                    
                    # Log the full start event for debugging
                    logger.info(f"Start event data: {json.dumps(event_data, indent=2)}")
                    
                    # Get audio format - check multiple possible locations
                    audio_format = media_streams_service.get_audio_format(parsed)
                    if not audio_format:
                        # Try alternative locations for audio format
                        media_format = event_data.get("mediaFormat") or event_data.get("media_format")
                        if isinstance(media_format, dict):
                            audio_format = media_format.get("encoding") or media_format.get("format")
                        elif isinstance(media_format, str):
                            audio_format = media_format
                        # Default to mulaw if not found (Twilio's default)
                        if not audio_format:
                            audio_format = "mulaw"
                            logger.warning("Audio format not found in start event, defaulting to mulaw")
                    
                    logger.info(f"Stream started: {stream_sid}, format: {audio_format}, from: {from_number}, to: {to_number}")
                    
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
                    
                    # Send a small silence packet immediately to keep connection alive
                    # This prevents Twilio from closing the connection while TTS is being generated
                    if stream_sid:
                        try:
                            # Send 160 bytes of silence (20ms at 8kHz) - mulaw silence is typically 0x7F
                            silence_bytes = bytes([0x7F] * 160)
                            silence_message = media_streams_service.create_media_message(
                                audio_bytes=silence_bytes,
                                stream_sid=stream_sid,
                                timestamp=str(int(time.time() * 1000))
                            )
                            await websocket.send_text(silence_message)
                            logger.info("Sent initial silence packet to keep connection alive")
                        except Exception as e:
                            logger.warning(f"Failed to send initial silence packet: {str(e)}")
                    
                    # Send initial greeting via ElevenLabs TTS (not Twilio's Say verb)
                    # This ensures consistent voice throughout the call
                    # Send immediately to keep call alive - don't delay
                    if restaurant_name and stream_sid:
                        initial_greeting_task = None
                        async def send_initial_greeting():
                            # No delay - send immediately to keep call alive
                            initial_greeting = f"Hi, thanks for calling {restaurant_name}. How can I help you?"
                            logger.info(f"Sending initial greeting via ElevenLabs: {initial_greeting}")
                            try:
                                await generate_and_send_tts(initial_greeting)
                                logger.info("Initial greeting sent successfully")
                            except Exception as e:
                                logger.error(f"Failed to send initial greeting: {str(e)}", exc_info=True)
                                # Try to send SMS fallback if TTS fails
                                try:
                                    await send_sms_fallback()
                                except Exception as sms_err:
                                    logger.error(f"Failed to send SMS fallback: {str(sms_err)}")
                        
                        # Create task and store reference so we can track it
                        initial_greeting_task = asyncio.create_task(send_initial_greeting())
                        logger.info(f"Created initial greeting task, will send TTS audio shortly")
                
                elif event_type == "media":
                    # Update last audio received time for health monitoring
                    last_audio_received_time = time.time()
                    connection_healthy = True
                    consecutive_errors = 0  # Reset error count on successful audio receipt
                    
                    # Extract audio from media message
                    audio_bytes = media_streams_service.extract_audio_from_media(parsed)
                    
                    if audio_bytes and deepgram_connection:
                        try:
                            # Convert audio format if needed
                            if audio_format == "mulaw":
                                # Convert mulaw to linear16 for Deepgram
                                linear16_bytes = media_streams_service.mulaw_to_linear16(audio_bytes)
                            else:
                                linear16_bytes = audio_bytes
                            
                            # Send to Deepgram with error handling
                            success = await deepgram_service.send_audio(deepgram_connection, linear16_bytes)
                            if not success:
                                logger.warning("Failed to send audio to Deepgram - connection may be unhealthy")
                                consecutive_errors += 1
                        except Exception as audio_error:
                            logger.error(f"Error processing/sending audio to Deepgram: {str(audio_error)}")
                            consecutive_errors += 1
                            # Don't close connection on single audio send failure
                            # Let reconnection logic handle persistent failures
                
                elif event_type == "stop":
                    # Log why the stream stopped
                    stop_reason = event_data.get("reason") or "unknown"
                    logger.info(f"Media Streams stopped - reason: {stop_reason}, call_sid: {call_sid}")
                    
                    # Clean up call metadata
                    if call_sid and call_sid in call_metadata:
                        del call_metadata[call_sid]
                        logger.debug(f"Cleaned up call metadata for CallSid {call_sid}")
                    
                    # End monitoring for this call
                    if call_sid:
                        final_metrics = voice_monitoring.end_call(call_sid)
                        if final_metrics:
                            logger.info(f"Call {call_sid} metrics: {final_metrics}")
                    
                    # Cancel keepalive and health monitoring tasks
                    if keepalive_task:
                        keepalive_task.cancel()
                        try:
                            await keepalive_task
                        except asyncio.CancelledError:
                            pass
                    if 'health_monitor_task' in locals():
                        health_monitor_task.cancel()
                        try:
                            await health_monitor_task
                        except asyncio.CancelledError:
                            pass
                    
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
                
                elif event_type == "pong" or (event_type == "message" and parsed.get("data", {}).get("event") == "pong"):
                    # Handle pong response (if Twilio sends it)
                    last_pong_time = asyncio.get_event_loop().time()
                    connection_healthy = True
                    logger.debug("Received WebSocket pong")
                
                elif event_type == "error":
                    error_msg = event_data.get("message", "Unknown error")
                    logger.error(f"Media Streams error: {error_msg}")
                    await send_sms_fallback()
                    await websocket.close()
                    break
            
            except WebSocketDisconnect:
                logger.info("WebSocket disconnected")
                # Clean up call metadata
                if call_sid and call_sid in call_metadata:
                    del call_metadata[call_sid]
                break
            except Exception as e:
                logger.error(f"Error in Media Streams handler: {str(e)}", exc_info=True)
                # Clean up call metadata
                if call_sid and call_sid in call_metadata:
                    del call_metadata[call_sid]
                await send_sms_fallback()
                await websocket.close()
                break
        
                    # Cancel keepalive and health monitoring tasks when loop exits
        if keepalive_task:
            keepalive_task.cancel()
            try:
                await keepalive_task
            except asyncio.CancelledError:
                pass
        if 'health_monitor_task' in locals():
            health_monitor_task.cancel()
            try:
                await health_monitor_task
            except asyncio.CancelledError:
                pass
    
    except Exception as e:
        logger.error(f"Error in Media Streams WebSocket: {str(e)}", exc_info=True)
        await send_sms_fallback()
    finally:
        # Cleanup call metadata
        if 'call_sid' in locals() and call_sid and call_sid in call_metadata:
            del call_metadata[call_sid]
            logger.debug(f"Cleaned up call metadata for CallSid {call_sid} in finally block")
        
        # Cleanup
        if 'keepalive_task' in locals() and keepalive_task:
            keepalive_task.cancel()
            try:
                await keepalive_task
            except asyncio.CancelledError:
                pass
        if 'health_monitor_task' in locals() and health_monitor_task:
            health_monitor_task.cancel()
            try:
                await health_monitor_task
            except asyncio.CancelledError:
                pass
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


@router.get("/metrics")
async def voice_metrics():
    """Get voice AI performance metrics."""
    return voice_monitoring.get_summary_stats()


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
