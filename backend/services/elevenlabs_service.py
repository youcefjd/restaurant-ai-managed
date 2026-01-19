"""
ElevenLabs TTS (Text-to-Speech) service for streaming audio generation.

Uses ElevenLabs API with ulaw_8000 output format for direct Twilio compatibility.
No ffmpeg conversion needed - audio streams directly to caller.
"""

import os
import logging
from typing import Optional, AsyncGenerator
import httpx

from backend.core.logging import setup_logging

logger = setup_logging(__name__)


class ElevenLabsService:
    """Service for text-to-speech using ElevenLabs with Twilio-compatible output."""

    def __init__(self):
        """Initialize ElevenLabs service."""
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", "cgSgspJ2msm6clMCkdW9")
        self.model = os.getenv("ELEVENLABS_MODEL", "eleven_turbo_v2_5")
        self.base_url = "https://api.elevenlabs.io/v1"
        self.enabled = bool(self.api_key)

        if self.enabled:
            logger.info(f"ElevenLabs TTS initialized - model: {self.model}, voice: {self.voice_id}")
        else:
            logger.warning("ELEVENLABS_API_KEY not set - TTS service disabled")

    async def text_to_speech_stream(
        self,
        text: str,
        voice_id: Optional[str] = None,
        output_format: str = "ulaw_8000"
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream TTS audio in Twilio-compatible format.

        Args:
            text: Text to convert to speech
            voice_id: Voice ID (uses default if not specified)
            output_format: Audio format - "ulaw_8000" for Twilio (default)

        Yields:
            Audio chunks as bytes (ulaw 8kHz for direct Twilio streaming)
        """
        if not self.enabled:
            logger.error("ElevenLabs service is disabled")
            return

        voice = voice_id or self.voice_id
        if not voice:
            logger.error("No voice ID configured")
            return

        url = f"{self.base_url}/text-to-speech/{voice}/stream"

        headers = {
            "Accept": "audio/basic",  # For ulaw format
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }

        # Add output format as query parameter
        params = {"output_format": output_format}

        data = {
            "text": text,
            "model_id": self.model,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            }
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream(
                    "POST",
                    url,
                    json=data,
                    headers=headers,
                    params=params
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        logger.error(f"ElevenLabs API error {response.status_code}: {error_text.decode()}")
                        return

                    # Stream audio chunks directly - already in ulaw format
                    async for chunk in response.aiter_bytes(chunk_size=640):
                        if chunk:
                            yield chunk

        except httpx.TimeoutException:
            logger.error("ElevenLabs request timed out")
        except Exception as e:
            logger.error(f"ElevenLabs streaming error: {e}", exc_info=True)

    async def text_to_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        output_format: str = "ulaw_8000"
    ) -> Optional[bytes]:
        """
        Convert text to speech and return complete audio.

        Args:
            text: Text to convert
            voice_id: Voice ID (uses default if not specified)
            output_format: Audio format

        Returns:
            Complete audio bytes, or None if failed
        """
        chunks = []
        async for chunk in self.text_to_speech_stream(text, voice_id, output_format):
            chunks.append(chunk)

        return b"".join(chunks) if chunks else None

    async def get_voices(self) -> Optional[list]:
        """
        Get list of available voices (for health check).

        Returns:
            List of voice objects, or None if failed
        """
        if not self.enabled:
            logger.warning("ElevenLabs service not enabled (no API key)")
            return None

        try:
            url = f"{self.base_url}/voices"
            headers = {"xi-api-key": self.api_key}

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("voices", [])
                elif response.status_code == 401:
                    logger.error("ElevenLabs API key is invalid (401 Unauthorized)")
                    return None
                elif response.status_code == 403:
                    logger.error("ElevenLabs API access forbidden (403) - check API key permissions")
                    return None
                else:
                    logger.error(f"Failed to fetch voices: HTTP {response.status_code} - {response.text[:200]}")
                    return None

        except httpx.TimeoutException:
            logger.error("ElevenLabs API request timed out")
            return None
        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to ElevenLabs API: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching voices: {type(e).__name__}: {e}")
            return None

    def is_enabled(self) -> bool:
        """Check if ElevenLabs service is enabled."""
        return self.enabled


# Global ElevenLabs service instance
elevenlabs_service = ElevenLabsService()
