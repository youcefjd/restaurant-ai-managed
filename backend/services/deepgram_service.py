"""
Deepgram STT (Speech-to-Text) service for real-time streaming transcription.

Uses Deepgram's WebSocket API for low-latency speech recognition with
partial transcription results for natural conversation flow.
"""

import os
import json
import asyncio
import logging
from typing import Optional, Callable, Dict, Any, AsyncGenerator
from deepgram import DeepgramClient, PrerecordedOptions, LiveOptions, LiveTranscriptionEvents
from deepgram.clients.live.v1 import LiveOptions as LiveOptionsV1

from backend.core.logging import setup_logging

logger = setup_logging(__name__)


class DeepgramService:
    """Service for real-time speech-to-text using Deepgram."""

    def __init__(self):
        """Initialize Deepgram client."""
        self.api_key = os.getenv("DEEPGRAM_API_KEY")
        self.enabled = bool(self.api_key)
        
        if self.enabled:
            try:
                self.client = DeepgramClient(self.api_key)
                logger.info("Deepgram STT service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Deepgram client: {str(e)}")
                self.client = None
                self.enabled = False
        else:
            self.client = None
            logger.warning("Deepgram API key not found - STT service disabled")

    async def create_live_transcription(
        self,
        on_message: Optional[Callable[[str, bool], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        on_close: Optional[Callable[[], None]] = None
    ) -> Optional[Any]:
        """
        Create a live transcription connection.

        Args:
            on_message: Callback for transcription updates (text, is_final)
            on_error: Callback for errors
            on_close: Callback for connection close

        Returns:
            Live transcription connection object or None if failed
        """
        if not self.enabled:
            logger.error("Deepgram service is disabled - cannot create live transcription")
            return None

        try:
            # Configure live transcription options
            options = LiveOptions(
                model="nova-2",
                language="en-US",
                smart_format=True,
                interim_results=True,  # Get partial results
                punctuate=True,
                utterances=True,
                endpointing=300,  # Endpoint after 300ms of silence
            )

            # Create live transcription connection
            connection = self.client.listen.rest.v("1").transcriptions.live(options)

            # Set up event handlers
            def on_open():
                logger.info("Deepgram live transcription connection opened")

            def on_message_handler(data):
                """Handle transcription messages from Deepgram."""
                try:
                    if data:
                        transcript = data.get("channel", {}).get("alternatives", [{}])[0].get("transcript", "")
                        is_final = data.get("is_final", False)
                        
                        if transcript and on_message:
                            on_message(transcript, is_final)
                            if is_final:
                                logger.debug(f"Deepgram final transcript: {transcript}")
                            else:
                                logger.debug(f"Deepgram interim transcript: {transcript}")
                except Exception as e:
                    logger.error(f"Error processing Deepgram message: {str(e)}")
                    if on_error:
                        on_error(e)

            def on_error_handler(error):
                """Handle errors from Deepgram."""
                logger.error(f"Deepgram error: {str(error)}")
                if on_error:
                    on_error(error)

            def on_close_handler():
                """Handle connection close."""
                logger.info("Deepgram live transcription connection closed")
                if on_close:
                    on_close()

            # Register event handlers
            connection.on(LiveTranscriptionEvents.Open, on_open)
            connection.on(LiveTranscriptionEvents.Transcript, on_message_handler)
            connection.on(LiveTranscriptionEvents.Error, on_error_handler)
            connection.on(LiveTranscriptionEvents.Close, on_close_handler)

            # Start the connection
            connection.start()
            logger.info("Deepgram live transcription started")

            return connection

        except Exception as e:
            logger.error(f"Failed to create Deepgram live transcription: {str(e)}")
            if on_error:
                on_error(e)
            return None

    async def send_audio(self, connection: Any, audio_data: bytes) -> bool:
        """
        Send audio data to Deepgram connection.

        Args:
            connection: Live transcription connection object
            audio_data: Raw audio bytes (PCM16 format)

        Returns:
            True if successful, False otherwise
        """
        if not connection:
            logger.error("No Deepgram connection provided")
            return False

        try:
            connection.send(audio_data)
            return True
        except Exception as e:
            logger.error(f"Failed to send audio to Deepgram: {str(e)}")
            return False

    async def close_connection(self, connection: Any) -> bool:
        """
        Close Deepgram connection.

        Args:
            connection: Live transcription connection object

        Returns:
            True if successful, False otherwise
        """
        if not connection:
            return False

        try:
            connection.finish()
            logger.info("Deepgram connection closed")
            return True
        except Exception as e:
            logger.error(f"Failed to close Deepgram connection: {str(e)}")
            return False

    def is_enabled(self) -> bool:
        """Check if Deepgram service is enabled."""
        return self.enabled


# Global Deepgram service instance
deepgram_service = DeepgramService()
