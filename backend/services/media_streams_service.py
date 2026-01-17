"""
Twilio Media Streams handler for WebSocket audio streaming.

Handles bidirectional audio streams between Twilio and the application,
including audio format conversion and protocol message handling.
"""

import json
import base64
import struct
import logging
import io
from typing import Optional, Dict, Any, Callable, BinaryIO
from enum import Enum

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    AudioSegment = None

from backend.core.logging import setup_logging

logger = setup_logging(__name__)


class MediaStreamMessageType(Enum):
    """Twilio Media Streams message types."""
    CONNECTED = "connected"
    START = "start"
    MEDIA = "media"
    STOP = "stop"
    ERROR = "error"


class MediaStreamService:
    """Service for handling Twilio Media Streams WebSocket protocol."""

    def __init__(self):
        """Initialize Media Streams service."""
        self.logger = logger

    def parse_message(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Parse Twilio Media Streams message.

        Args:
            message: JSON message string from Twilio

        Returns:
            Parsed message dictionary, or None if invalid
        """
        try:
            data = json.loads(message)
            event_type = data.get("event")
            
            # For start events, callSid and streamSid are nested in the "start" object
            start_data = data.get("start", {})
            stream_sid = data.get("streamSid") or start_data.get("streamSid")
            call_sid = data.get("callSid") or start_data.get("callSid")
            account_sid = data.get("accountSid") or start_data.get("accountSid")
            
            return {
                "type": event_type,
                "data": data,
                "stream_sid": stream_sid,
                "account_sid": account_sid,
                "call_sid": call_sid,
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Media Streams message: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error parsing message: {str(e)}")
            return None

    def extract_audio_from_media(self, message: Dict[str, Any]) -> Optional[bytes]:
        """
        Extract audio payload from Media Streams media message.

        Args:
            message: Parsed media message dictionary

        Returns:
            Audio bytes (mulaw or linear16), or None if invalid
        """
        try:
            media_payload = message.get("data", {}).get("payload", "")
            if not media_payload:
                return None
            
            # Decode base64 audio payload
            audio_bytes = base64.b64decode(media_payload)
            return audio_bytes
        except Exception as e:
            logger.error(f"Failed to extract audio from media message: {str(e)}")
            return None

    def get_audio_format(self, message: Dict[str, Any]) -> Optional[str]:
        """
        Get audio format from start message.

        Args:
            message: Parsed start message dictionary

        Returns:
            Audio format string (e.g., "mulaw", "linear16"), or None
        """
        try:
            data = message.get("data", {})
            # Check both top-level and nested in "start" object
            media_format = data.get("mediaFormat") or data.get("start", {}).get("mediaFormat", {})
            if isinstance(media_format, dict):
                encoding = media_format.get("encoding", "")
                # Extract format from encoding string (e.g., "audio/x-mulaw" -> "mulaw")
                if encoding:
                    if "mulaw" in encoding.lower():
                        return "mulaw"
                    elif "linear16" in encoding.lower() or "pcm" in encoding.lower():
                        return "linear16"
                    return encoding
            elif isinstance(media_format, str):
                return media_format
            return None
        except Exception as e:
            logger.error(f"Failed to get audio format: {str(e)}")
            return None

    def mulaw_to_linear16(self, mulaw_bytes: bytes, sample_rate: int = 8000) -> bytes:
        """
        Convert mu-law audio to linear16 PCM.
        
        Twilio Media Streams uses 8kHz sample rate for telephony.

        Args:
            mulaw_bytes: Mu-law encoded audio bytes
            sample_rate: Sample rate in Hz (default 8000 for telephony)

        Returns:
            Linear16 PCM audio bytes (16-bit, little-endian, mono)
        """
        if not mulaw_bytes:
            return b''
        
        linear16_samples = []
        mulaw_table = [
            -32124, -31100, -30076, -29052, -28028, -27004, -25980, -24956,
            -23932, -22908, -21884, -20860, -19836, -18812, -17788, -16764,
            -15996, -15484, -14972, -14460, -13948, -13436, -12924, -12412,
            -11900, -11388, -10876, -10364, -9852, -9340, -8828, -8316,
            -7932, -7676, -7420, -7164, -6908, -6652, -6396, -6140,
            -5884, -5628, -5372, -5116, -4860, -4604, -4348, -4092,
            -3900, -3772, -3644, -3516, -3388, -3260, -3132, -3004,
            -2876, -2748, -2620, -2492, -2364, -2236, -2108, -1980,
            -1884, -1820, -1756, -1692, -1628, -1564, -1500, -1436,
            -1372, -1308, -1244, -1180, -1116, -1052, -988, -924,
            -876, -844, -812, -780, -748, -716, -684, -652,
            -620, -588, -556, -524, -492, -460, -428, -396,
            -372, -356, -340, -324, -308, -292, -276, -260,
            -244, -228, -212, -196, -180, -164, -148, -132,
            -120, -112, -104, -96, -88, -80, -72, -64,
            -56, -48, -40, -32, -24, -16, -8, 0,
            32124, 31100, 30076, 29052, 28028, 27004, 25980, 24956,
            23932, 22908, 21884, 20860, 19836, 18812, 17788, 16764,
            15996, 15484, 14972, 14460, 13948, 13436, 12924, 12412,
            11900, 11388, 10876, 10364, 9852, 9340, 8828, 8316,
            7932, 7676, 7420, 7164, 6908, 6652, 6396, 6140,
            5884, 5628, 5372, 5116, 4860, 4604, 4348, 4092,
            3900, 3772, 3644, 3516, 3388, 3260, 3132, 3004,
            2876, 2748, 2620, 2492, 2364, 2236, 2108, 1980,
            1884, 1820, 1756, 1692, 1628, 1564, 1500, 1436,
            1372, 1308, 1244, 1180, 1116, 1052, 988, 924,
            876, 844, 812, 780, 748, 716, 684, 652,
            620, 588, 556, 524, 492, 460, 428, 396,
            372, 356, 340, 324, 308, 292, 276, 260,
            244, 228, 212, 196, 180, 164, 148, 132,
            120, 112, 104, 96, 88, 80, 72, 64,
            56, 48, 40, 32, 24, 16, 8, 0
        ]

        for byte in mulaw_bytes:
            if byte > 255:
                logger.warning(f"Invalid mulaw byte value: {byte}, skipping")
                continue
            linear_sample = mulaw_table[byte]
            linear16_samples.append(struct.pack('<h', linear_sample))

        return b''.join(linear16_samples)

    def linear16_to_mulaw(self, linear16_bytes: bytes) -> bytes:
        """
        Convert linear16 PCM to mu-law audio.

        Args:
            linear16_bytes: Linear16 PCM audio bytes

        Returns:
            Mu-law encoded audio bytes
        """
        mulaw_samples = []
        bias = 0x84
        clip = 32635

        for i in range(0, len(linear16_bytes), 2):
            if i + 1 < len(linear16_bytes):
                sample = struct.unpack('<h', linear16_bytes[i:i+2])[0]
                
                # Get sign
                sign = (sample >> 8) & 0x80
                if sign:
                    sample = -sample
                
                # Clip sample
                if sample > clip:
                    sample = clip
                
                # Convert to mu-law
                sample = sample + bias
                exponent = 0
                for exp in range(8):
                    if sample > 0x7F:
                        sample >>= 1
                        exponent += 1
                    else:
                        break
                
                mantissa = (sample >> 4) & 0x07
                mulaw_byte = ~(sign | (exponent << 4) | mantissa) & 0xFF
                mulaw_samples.append(mulaw_byte)

        return bytes(mulaw_samples)

    def create_media_message(self, audio_bytes: bytes, stream_sid: str, timestamp: str = None) -> str:
        """
        Create Media Streams media message to send audio to Twilio.

        Args:
            audio_bytes: Audio bytes to send
            stream_sid: Stream SID from Twilio
            timestamp: Timestamp (optional, auto-generated if None)

        Returns:
            JSON message string
        """
        import time
        
        if timestamp is None:
            timestamp = str(int(time.time() * 1000))

        payload = base64.b64encode(audio_bytes).decode('utf-8')
        
        message = {
            "event": "media",
            "streamSid": stream_sid,
            "media": {
                "payload": payload
            }
        }

        return json.dumps(message)

    def create_clear_message(self, stream_sid: str) -> str:
        """
        Create clear message to clear Twilio audio buffer.

        Args:
            stream_sid: Stream SID from Twilio

        Returns:
            JSON message string
        """
        message = {
            "event": "clear",
            "streamSid": stream_sid
        }
        return json.dumps(message)

    def mp3_to_mulaw(self, mp3_bytes: bytes, sample_rate: int = 8000) -> bytes:
        """
        Convert MP3 audio to mulaw format for Twilio Media Streams.
        
        Twilio expects 8kHz mono mulaw PCM audio.

        Args:
            mp3_bytes: MP3 encoded audio bytes
            sample_rate: Target sample rate in Hz (default 8000 for telephony)

        Returns:
            Mu-law encoded audio bytes
        """
        if not PYDUB_AVAILABLE:
            logger.error("pydub not available - cannot convert MP3 to mulaw")
            raise ImportError("pydub is required for MP3 to mulaw conversion. Install with: pip install pydub")
        
        if not mp3_bytes:
            return b''
        
        # Check if ffprobe/ffmpeg is available
        import shutil
        ffprobe_path = shutil.which("ffprobe") or shutil.which("ffmpeg")
        if not ffprobe_path:
            error_msg = (
                "ffprobe/ffmpeg not found. pydub requires ffmpeg to convert MP3 audio. "
                "Please install ffmpeg:\n"
                "  macOS: brew install ffmpeg\n"
                "  Linux: sudo apt-get install ffmpeg (or use your package manager)\n"
                "  Windows: Download from https://ffmpeg.org/download.html"
            )
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        try:
            # Load MP3 from bytes
            audio = AudioSegment.from_mp3(io.BytesIO(mp3_bytes))
            
            # Convert to mono if stereo
            if audio.channels > 1:
                audio = audio.set_channels(1)
            
            # Resample to target sample rate (8kHz for telephony)
            if audio.frame_rate != sample_rate:
                audio = audio.set_frame_rate(sample_rate)
            
            # Convert to raw PCM16 (16-bit signed integer, little-endian)
            raw_audio = audio.raw_data
            
            # Convert PCM16 to mulaw
            mulaw_audio = self.linear16_to_mulaw(raw_audio)
            
            return mulaw_audio
            
        except Exception as e:
            logger.error(f"Failed to convert MP3 to mulaw: {str(e)}", exc_info=True)
            raise

    def validate_audio_format(self, audio_bytes: bytes, expected_format: str = "mulaw") -> bool:
        """
        Validate audio format and basic properties.

        Args:
            audio_bytes: Audio bytes to validate
            expected_format: Expected format ("mulaw", "linear16", "mp3")

        Returns:
            True if format appears valid, False otherwise
        """
        if not audio_bytes:
            return False
        
        if expected_format == "mulaw":
            # Mulaw should be single bytes (0-255)
            if len(audio_bytes) == 0:
                return False
            # Check that bytes are in valid range
            return all(0 <= b <= 255 for b in audio_bytes[:100])  # Check first 100 bytes
        
        elif expected_format == "linear16":
            # Linear16 should be even number of bytes (16-bit samples)
            return len(audio_bytes) % 2 == 0
        
        elif expected_format == "mp3":
            # MP3 should start with ID3 tag or MP3 sync word (0xFF 0xFB or 0xFF 0xF3)
            return audio_bytes[:2] in [b'\xff\xfb', b'\xff\xf3', b'ID']
        
        return True


# Global Media Streams service instance
media_streams_service = MediaStreamService()
