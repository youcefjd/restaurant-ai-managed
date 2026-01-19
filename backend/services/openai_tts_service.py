"""
OpenAI TTS (Text-to-Speech) service for streaming audio generation.

Uses OpenAI's tts-1 model optimized for real-time low-latency applications.
Converts output to mulaw 8kHz for Twilio compatibility.
"""

import os
import logging
import struct
from typing import Optional, AsyncGenerator

from backend.core.logging import setup_logging

logger = setup_logging(__name__)

# Mulaw encoding table (for converting 16-bit linear to 8-bit mulaw)
MULAW_BIAS = 0x84
MULAW_CLIP = 32635

def _linear_to_mulaw(sample: int) -> int:
    """Convert a 16-bit signed linear sample to 8-bit mulaw."""
    sign = (sample >> 8) & 0x80
    if sign:
        sample = -sample
    sample = min(sample, MULAW_CLIP)
    sample += MULAW_BIAS

    exponent = 7
    for exp in range(7, -1, -1):
        if sample & (1 << (exp + 7)):
            exponent = exp
            break

    mantissa = (sample >> (exponent + 3)) & 0x0F
    mulaw_byte = ~(sign | (exponent << 4) | mantissa)
    return mulaw_byte & 0xFF

# Check for OpenAI SDK
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None


class OpenAITTSService:
    """Service for text-to-speech using OpenAI with Twilio-compatible output."""

    def __init__(self):
        """Initialize OpenAI TTS service."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_TTS_MODEL", "tts-1")  # tts-1 for speed, tts-1-hd for quality
        self.voice = os.getenv("OPENAI_TTS_VOICE", "nova")  # alloy, echo, fable, onyx, nova, shimmer
        self.enabled = bool(self.api_key) and OPENAI_AVAILABLE
        self.client = None

        if self.enabled:
            self.client = AsyncOpenAI(api_key=self.api_key)
            logger.info(f"OpenAI TTS initialized - model: {self.model}, voice: {self.voice}")
        else:
            if not OPENAI_AVAILABLE:
                logger.warning("OpenAI SDK not available - TTS service disabled")
            else:
                logger.warning("OPENAI_API_KEY not set - TTS service disabled")

    def _resample_and_convert_to_mulaw(self, pcm_24k: bytes) -> bytes:
        """
        Convert PCM 24kHz 16-bit to mulaw 8kHz for Twilio.

        Args:
            pcm_24k: PCM audio at 24kHz, 16-bit signed little-endian mono

        Returns:
            Mulaw audio at 8kHz
        """
        try:
            # Parse 16-bit samples from PCM data
            num_samples = len(pcm_24k) // 2
            samples = struct.unpack(f'<{num_samples}h', pcm_24k)

            # Resample from 24kHz to 8kHz (take every 3rd sample)
            resampled = samples[::3]

            # Convert each sample to mulaw
            mulaw_bytes = bytes(_linear_to_mulaw(s) for s in resampled)

            return mulaw_bytes
        except Exception as e:
            logger.error(f"Audio conversion error: {e}")
            return b""

    async def text_to_speech_stream(
        self,
        text: str,
        voice: Optional[str] = None,
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream TTS audio in Twilio-compatible format (mulaw 8kHz).

        Args:
            text: Text to convert to speech
            voice: Voice name (uses default if not specified)

        Yields:
            Audio chunks as bytes (mulaw 8kHz for direct Twilio streaming)
        """
        if not self.enabled:
            logger.error("OpenAI TTS service is disabled")
            return

        voice_name = voice or self.voice

        try:
            # Use streaming response with PCM format
            async with self.client.audio.speech.with_streaming_response.create(
                model=self.model,
                voice=voice_name,
                input=text,
                response_format="pcm",  # Raw PCM 24kHz 16-bit mono
            ) as response:
                # Buffer for accumulating PCM data (need enough for resampling)
                pcm_buffer = b""
                # Process in chunks that are multiples of 6 bytes (for clean 24k->8k resampling)
                chunk_size = 2400  # 50ms of audio at 24kHz (24000 * 0.05 * 2 bytes)

                async for chunk in response.iter_bytes(chunk_size=chunk_size):
                    pcm_buffer += chunk

                    # Process complete chunks
                    while len(pcm_buffer) >= chunk_size:
                        pcm_chunk = pcm_buffer[:chunk_size]
                        pcm_buffer = pcm_buffer[chunk_size:]

                        # Convert to mulaw 8kHz
                        mulaw_chunk = self._resample_and_convert_to_mulaw(pcm_chunk)
                        if mulaw_chunk:
                            yield mulaw_chunk

                # Process remaining buffer
                if pcm_buffer:
                    # Pad to even number of bytes if needed
                    if len(pcm_buffer) % 2 != 0:
                        pcm_buffer += b'\x00'
                    mulaw_chunk = self._resample_and_convert_to_mulaw(pcm_buffer)
                    if mulaw_chunk:
                        yield mulaw_chunk

        except Exception as e:
            logger.error(f"OpenAI TTS streaming error: {e}", exc_info=True)

    async def text_to_speech(
        self,
        text: str,
        voice: Optional[str] = None,
    ) -> Optional[bytes]:
        """
        Convert text to speech and return complete audio.

        Args:
            text: Text to convert
            voice: Voice name (uses default if not specified)

        Returns:
            Complete audio bytes (mulaw 8kHz), or None if failed
        """
        chunks = []
        async for chunk in self.text_to_speech_stream(text, voice):
            chunks.append(chunk)

        return b"".join(chunks) if chunks else None

    def is_enabled(self) -> bool:
        """Check if OpenAI TTS service is enabled."""
        return self.enabled

    def get_available_voices(self) -> list:
        """Get list of available voices."""
        return ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]


# Global OpenAI TTS service instance
openai_tts_service = OpenAITTSService()
