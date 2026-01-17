"""
Twilio Media Streams handler for WebSocket audio streaming.

Handles bidirectional audio streams between Twilio and the application,
including audio format conversion and protocol message handling.
"""

import json
import base64
import struct
import logging
from typing import Optional, Dict, Any, Callable, BinaryIO
from enum import Enum

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
            return {
                "type": event_type,
                "data": data,
                "stream_sid": data.get("streamSid"),
                "account_sid": data.get("accountSid"),
                "call_sid": data.get("callSid"),
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
            media_format = message.get("data", {}).get("mediaFormat", {})
            return media_format.get("encoding", None)
        except Exception as e:
            logger.error(f"Failed to get audio format: {str(e)}")
            return None

    def mulaw_to_linear16(self, mulaw_bytes: bytes) -> bytes:
        """
        Convert mu-law audio to linear16 PCM.

        Args:
            mulaw_bytes: Mu-law encoded audio bytes

        Returns:
            Linear16 PCM audio bytes
        """
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


# Global Media Streams service instance
media_streams_service = MediaStreamService()
