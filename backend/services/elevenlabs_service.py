"""
ElevenLabs TTS (Text-to-Speech) service for streaming audio generation.

Uses ElevenLabs API for low-latency, natural-sounding voice synthesis
with streaming support for real-time conversation.
"""

import os
import asyncio
import logging
from typing import Optional, AsyncGenerator
import httpx

from backend.core.logging import setup_logging

logger = setup_logging(__name__)


class ElevenLabsService:
    """Service for text-to-speech using ElevenLabs."""

    def __init__(self):
        """Initialize ElevenLabs service."""
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID")  # Optional, uses default if not set
        self.model = os.getenv("ELEVENLABS_MODEL", "eleven_turbo_v2_5")
        self.base_url = "https://api.elevenlabs.io/v1"
        self.enabled = bool(self.api_key)
        
        if self.enabled:
            # If no voice_id specified, use default conversational voice
            # Default voice IDs vary, but we'll fetch it if needed
            if not self.voice_id:
                self.voice_id = self._get_default_voice_id()
            logger.info(f"ElevenLabs TTS service initialized with model: {self.model}, voice: {self.voice_id}")
        else:
            logger.warning("ElevenLabs API key not found - TTS service disabled")

    def _get_default_voice_id(self) -> str:
        """
        Get default conversational voice ID.

        Returns:
            Default voice ID string
        """
        # Default to the configured voice ID
        # User can override with ELEVENLABS_VOICE_ID env var
        return os.getenv("ELEVENLABS_DEFAULT_VOICE_ID", "cgSgspJ2msm6clMCkdW9")

    async def text_to_speech_stream(
        self,
        text: str,
        voice_id: Optional[str] = None,
        model: Optional[str] = None,
        stability: float = 0.5,
        similarity_boost: float = 0.75
    ) -> AsyncGenerator[bytes, None]:
        """
        Convert text to speech and stream audio chunks.

        Args:
            text: Text to convert to speech
            voice_id: Voice ID to use (overrides default)
            model: Model to use (overrides default)
            stability: Stability setting (0.0-1.0)
            similarity_boost: Similarity boost (0.0-1.0)

        Yields:
            Audio chunks as bytes (MP3 or PCM format)
        """
        if not self.enabled:
            logger.error("ElevenLabs service is disabled - cannot generate speech")
            return

        voice = voice_id or self.voice_id
        model_name = model or self.model

        if not voice:
            logger.error("No voice ID specified and no default available")
            return

        try:
            url = f"{self.base_url}/text-to-speech/{voice}/stream"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }

            data = {
                "text": text,
                "model_id": model_name,
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost
                }
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream("POST", url, json=data, headers=headers) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        logger.error(f"ElevenLabs API error {response.status_code}: {error_text.decode()}")
                        return

                    async for chunk in response.aiter_bytes(chunk_size=4096):
                        if chunk:
                            yield chunk

        except Exception as e:
            logger.error(f"Error generating speech with ElevenLabs: {str(e)}", exc_info=True)

    async def text_to_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        model: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Convert text to speech and return complete audio.

        Args:
            text: Text to convert to speech
            voice_id: Voice ID to use (overrides default)
            model: Model to use (overrides default)

        Returns:
            Complete audio as bytes, or None if failed
        """
        audio_chunks = []
        async for chunk in self.text_to_speech_stream(text, voice_id, model):
            audio_chunks.append(chunk)
        
        if audio_chunks:
            return b"".join(audio_chunks)
        return None

    async def get_voices(self) -> Optional[list]:
        """
        Get list of available voices.

        Returns:
            List of voice objects, or None if failed
        """
        if not self.enabled:
            return None

        try:
            url = f"{self.base_url}/voices"
            headers = {"xi-api-key": self.api_key}

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("voices", [])
                else:
                    logger.error(f"Failed to fetch voices: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Error fetching voices from ElevenLabs: {str(e)}")
            return None

    def is_enabled(self) -> bool:
        """Check if ElevenLabs service is enabled."""
        return self.enabled


# Global ElevenLabs service instance
elevenlabs_service = ElevenLabsService()
