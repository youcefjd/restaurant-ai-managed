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
from contextlib import contextmanager
from deepgram import DeepgramClient
from deepgram.core.events import EventType
from deepgram.listen.v1.types.listen_v1results import ListenV1Results

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
                self.client = DeepgramClient(api_key=self.api_key)
                logger.info("Deepgram STT service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Deepgram client: {str(e)}")
                self.client = None
                self.enabled = False
        else:
            self.client = None
            logger.warning("Deepgram API key not found - STT service disabled")

    def create_live_transcription(
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
            Live transcription connection wrapper or None if failed
        """
        if not self.enabled:
            logger.error("Deepgram service is disabled - cannot create live transcription")
            return None

        try:
            # Create live transcription connection using the new SDK v3.0+ API
            # connect() returns a context manager that yields the socket client
            connection_context = self.client.listen.v1.connect(
                model="nova-2",
                language="en-US",
                smart_format="true",
                interim_results="true",  # Get partial results
                punctuate="true",
                utterances="true",
                endpointing="300",  # Endpoint after 300ms of silence
            )
            
            # Enter the context manager to get the socket client
            socket_client = connection_context.__enter__()

            # Set up event handlers
            def on_open_handler(data):
                logger.info("Deepgram live transcription connection opened")

            def on_message_handler(data):
                """Handle transcription messages from Deepgram."""
                try:
                    # Only process Results messages (transcription data)
                    if isinstance(data, ListenV1Results):
                        # Extract transcript from the channel alternatives
                        if data.channel and data.channel.alternatives and len(data.channel.alternatives) > 0:
                            transcript = data.channel.alternatives[0].transcript or ""
                            is_final = data.is_final or False
                            
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

            def on_close_handler(data):
                """Handle connection close."""
                logger.info("Deepgram live transcription connection closed")
                if on_close:
                    on_close()

            # Register event handlers using EventType
            socket_client.on(EventType.OPEN, on_open_handler)
            socket_client.on(EventType.MESSAGE, on_message_handler)
            socket_client.on(EventType.ERROR, on_error_handler)
            socket_client.on(EventType.CLOSE, on_close_handler)

            # Start listening for messages in a background thread
            # start_listening() blocks, so we need to run it in a separate thread
            import threading
            listener_thread = threading.Thread(target=socket_client.start_listening, daemon=True)
            listener_thread.start()
            logger.info("Deepgram live transcription started")

            # Create a wrapper object to store both the socket client and context manager
            class ConnectionWrapper:
                def __init__(self, socket_client, context_manager):
                    self.socket_client = socket_client
                    self.context_manager = context_manager
                    
                def send_media(self, data: bytes):
                    return self.socket_client.send_media(data)
                
                def finish(self):
                    # Exit the context manager to close the connection
                    try:
                        self.context_manager.__exit__(None, None, None)
                    except Exception:
                        pass

            wrapper = ConnectionWrapper(socket_client, connection_context)
            return wrapper

        except Exception as e:
            logger.error(f"Failed to create Deepgram live transcription: {str(e)}")
            if on_error:
                on_error(e)
            return None

    async def send_audio(self, connection: Any, audio_data: bytes) -> bool:
        """
        Send audio data to Deepgram connection.

        Args:
            connection: Live transcription connection wrapper object
            audio_data: Raw audio bytes (PCM16 format)

        Returns:
            True if successful, False otherwise
        """
        if not connection:
            logger.error("No Deepgram connection provided")
            return False

        try:
            connection.send_media(audio_data)
            return True
        except Exception as e:
            logger.error(f"Failed to send audio to Deepgram: {str(e)}")
            return False

    async def close_connection(self, connection: Any) -> bool:
        """
        Close Deepgram connection.

        Args:
            connection: Live transcription connection wrapper object

        Returns:
            True if successful, False otherwise
        """
        if not connection:
            return False

        try:
            # Use the wrapper's finish method to close the connection
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
