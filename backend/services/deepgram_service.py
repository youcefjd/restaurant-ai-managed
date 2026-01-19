"""
Deepgram STT (Speech-to-Text) service for real-time streaming transcription.

Uses Deepgram SDK v5+ WebSocket API for low-latency speech recognition.
"""

import os
import asyncio
import logging
import threading
from typing import Optional, Callable, Any

from backend.core.logging import setup_logging

logger = setup_logging(__name__)


class DeepgramService:
    """Service for real-time speech-to-text using Deepgram SDK v5+."""

    def __init__(self):
        """Initialize Deepgram service."""
        self.api_key = os.getenv("DEEPGRAM_API_KEY")
        self.enabled = bool(self.api_key)
        self._client = None

        if self.enabled:
            logger.info("Deepgram STT service initialized")
        else:
            logger.warning("DEEPGRAM_API_KEY not set - STT service disabled")

    def _get_client(self):
        """Lazy-load Deepgram client."""
        if self._client is None and self.enabled:
            try:
                from deepgram import DeepgramClient
                self._client = DeepgramClient(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to create Deepgram client: {e}")
                self.enabled = False
        return self._client

    async def create_live_connection(
        self,
        on_transcript: Callable[[str, bool], None],
        on_error: Optional[Callable[[Exception], None]] = None,
        on_close: Optional[Callable[[], None]] = None,
        sample_rate: int = 8000,
        encoding: str = "linear16",
        channels: int = 1
    ) -> Optional['LiveConnection']:
        """
        Create a live transcription connection.

        Args:
            on_transcript: Callback for transcription (text, is_final)
            on_error: Callback for errors
            on_close: Callback for connection close
            sample_rate: Audio sample rate in Hz (default 8000 for telephony)
            encoding: Audio encoding (linear16 for PCM)
            channels: Number of audio channels

        Returns:
            LiveConnection wrapper or None if failed
        """
        if not self.enabled:
            logger.error("Deepgram service is disabled")
            return None

        client = self._get_client()
        if not client:
            return None

        try:
            from deepgram.core.events import EventType

            # Create connection with Deepgram v5 SDK
            # Increased endpointing and utterance_end for better sentence detection
            socket_context = client.listen.v1.connect(
                model="nova-2",
                language="en-US",
                encoding=encoding,
                sample_rate=str(sample_rate),
                channels=str(channels),
                interim_results="true",
                smart_format="true",
                punctuate="true",
                endpointing="500",  # 500ms pause to end utterance (was 300)
                utterance_end_ms="1500",  # 1.5s to detect end (was 1000)
                vad_events="true"
            )

            # Enter context to get socket
            socket = socket_context.__enter__()

            # Define event handlers
            def handle_message(result):
                """Handle transcription results."""
                try:
                    # Handle different result types from Deepgram
                    # Could be LiveTranscriptionResponse, MetadataResponse, etc.

                    # Skip non-transcript messages (metadata, utterance_end, etc.)
                    if not hasattr(result, 'channel'):
                        return

                    channel = result.channel
                    if not channel or not hasattr(channel, 'alternatives'):
                        return

                    alternatives = channel.alternatives
                    if not alternatives or len(alternatives) == 0:
                        return

                    transcript = alternatives[0].transcript
                    is_final = getattr(result, 'is_final', False)

                    if transcript and transcript.strip():
                        on_transcript(transcript.strip(), is_final)
                except AttributeError:
                    # Not a transcript message, ignore
                    pass
                except Exception as e:
                    logger.error(f"Error processing Deepgram result: {e}")
                    if on_error:
                        on_error(e)

            def handle_error(error):
                """Handle errors."""
                logger.error(f"Deepgram error: {error}")
                if on_error:
                    on_error(Exception(str(error)))

            def handle_close(event):
                """Handle connection close."""
                logger.info("Deepgram connection closed")
                if on_close:
                    on_close()

            def handle_open(event):
                """Handle connection open."""
                logger.info("Deepgram connection opened")

            # Register event handlers using the correct method signature
            socket.on(EventType.MESSAGE, handle_message)
            socket.on(EventType.ERROR, handle_error)
            socket.on(EventType.CLOSE, handle_close)
            socket.on(EventType.OPEN, handle_open)

            # Start listening in background thread
            def listen_thread():
                try:
                    socket.start_listening()
                except Exception as e:
                    logger.error(f"Error in Deepgram listener: {e}")
                    if on_error:
                        on_error(e)

            listener = threading.Thread(target=listen_thread, daemon=True)
            listener.start()

            logger.info("Deepgram live connection started successfully")
            return LiveConnection(socket, socket_context, listener)

        except Exception as e:
            logger.error(f"Failed to create Deepgram live connection: {e}", exc_info=True)
            if on_error:
                on_error(e)
            return None

    def is_enabled(self) -> bool:
        """Check if Deepgram service is enabled."""
        return self.enabled


class LiveConnection:
    """Wrapper for Deepgram live transcription connection."""

    def __init__(self, socket, context, listener_thread):
        """Initialize with Deepgram socket."""
        self._socket = socket
        self._context = context
        self._listener = listener_thread
        self._closed = False

    async def send_audio(self, audio_bytes: bytes) -> bool:
        """
        Send audio data to Deepgram.

        Args:
            audio_bytes: Raw audio bytes (linear16 PCM)

        Returns:
            True if successful, False otherwise
        """
        if self._closed:
            return False

        try:
            self._socket.send_media(audio_bytes)
            return True
        except Exception as e:
            logger.error(f"Failed to send audio to Deepgram: {e}")
            self._closed = True  # Mark as closed on error
            return False

    def send_keepalive(self) -> bool:
        """Send keepalive message to Deepgram to prevent timeout."""
        if self._closed:
            return False

        try:
            # Deepgram SDK v5 keepalive
            if hasattr(self._socket, 'keep_alive'):
                self._socket.keep_alive()
            return True
        except Exception as e:
            logger.debug(f"Keepalive failed: {e}")
            return False

    async def close(self) -> bool:
        """Close the Deepgram connection."""
        if self._closed:
            return True

        try:
            self._closed = True

            # Send close message
            try:
                self._socket.send_close_stream()
            except:
                pass

            # Exit context
            try:
                self._context.__exit__(None, None, None)
            except:
                pass

            logger.info("Deepgram connection closed")
            return True
        except Exception as e:
            logger.error(f"Error closing Deepgram connection: {e}")
            return False

    @property
    def is_closed(self) -> bool:
        """Check if connection is closed."""
        return self._closed


# Global Deepgram service instance
deepgram_service = DeepgramService()
