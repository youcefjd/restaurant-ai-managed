"""
Twilio Media Streams handler for WebSocket audio streaming.

Handles bidirectional audio streams between Twilio and the application,
including audio format conversion and protocol message handling.
"""

import json
import base64
import struct
import logging
from typing import Optional, Dict, Any

from backend.core.logging import setup_logging

logger = setup_logging(__name__)


# Mu-law decoding table (256 values mapping mulaw byte to linear16 sample)
MULAW_DECODE_TABLE = [
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


class MediaStreamsService:
    """Service for handling Twilio Media Streams WebSocket protocol."""

    def parse_message(self, raw_message: str) -> Optional[Dict[str, Any]]:
        """
        Parse Twilio Media Streams message.

        Args:
            raw_message: Raw JSON string from Twilio WebSocket

        Returns:
            Parsed message with extracted fields, or None if invalid
        """
        try:
            data = json.loads(raw_message)
            event = data.get("event")

            result = {
                "event": event,
                "raw": data,
            }

            if event == "connected":
                result["protocol"] = data.get("protocol")

            elif event == "start":
                start_data = data.get("start", {})
                result["stream_sid"] = data.get("streamSid") or start_data.get("streamSid")
                result["call_sid"] = start_data.get("callSid")
                result["account_sid"] = start_data.get("accountSid")
                result["tracks"] = start_data.get("tracks", [])
                result["media_format"] = start_data.get("mediaFormat", {})
                result["custom_parameters"] = start_data.get("customParameters", {})

            elif event == "media":
                result["stream_sid"] = data.get("streamSid")
                # IMPORTANT: Twilio sends audio in data.media.payload, NOT data.payload
                media = data.get("media", {})
                result["payload"] = media.get("payload", "")
                result["timestamp"] = media.get("timestamp")
                result["track"] = media.get("track")
                result["chunk"] = media.get("chunk")

            elif event == "stop":
                result["stream_sid"] = data.get("streamSid")
                result["stop"] = data.get("stop", {})

            elif event == "mark":
                result["stream_sid"] = data.get("streamSid")
                result["mark"] = data.get("mark", {})

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Media Streams message: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing message: {e}")
            return None

    def extract_audio(self, parsed_message: Dict[str, Any]) -> Optional[bytes]:
        """
        Extract audio bytes from a parsed media message.

        Args:
            parsed_message: Parsed message from parse_message()

        Returns:
            Raw audio bytes (mulaw), or None if not a media message
        """
        if parsed_message.get("event") != "media":
            return None

        payload = parsed_message.get("payload", "")
        if not payload:
            return None

        try:
            return base64.b64decode(payload)
        except Exception as e:
            logger.error(f"Failed to decode audio payload: {e}")
            return None

    def mulaw_to_linear16(self, mulaw_bytes: bytes) -> bytes:
        """
        Convert mu-law audio to linear16 PCM for Deepgram.

        Args:
            mulaw_bytes: Mu-law encoded audio bytes (8kHz)

        Returns:
            Linear16 PCM audio bytes (16-bit, little-endian)
        """
        if not mulaw_bytes:
            return b''

        samples = []
        for byte in mulaw_bytes:
            samples.append(struct.pack('<h', MULAW_DECODE_TABLE[byte]))

        return b''.join(samples)

    def create_media_message(
        self,
        stream_sid: str,
        audio_bytes: bytes,
        timestamp: Optional[str] = None
    ) -> str:
        """
        Create a media message to send audio to Twilio.

        Args:
            stream_sid: Stream SID from Twilio
            audio_bytes: Audio bytes to send (should be mulaw for Twilio)
            timestamp: Optional timestamp

        Returns:
            JSON string to send via WebSocket
        """
        import time

        message = {
            "event": "media",
            "streamSid": stream_sid,
            "media": {
                "payload": base64.b64encode(audio_bytes).decode('utf-8')
            }
        }

        if timestamp:
            message["media"]["timestamp"] = timestamp

        return json.dumps(message)

    def create_mark_message(self, stream_sid: str, name: str) -> str:
        """
        Create a mark message to track audio playback position.

        Args:
            stream_sid: Stream SID from Twilio
            name: Mark name for tracking

        Returns:
            JSON string to send via WebSocket
        """
        return json.dumps({
            "event": "mark",
            "streamSid": stream_sid,
            "mark": {"name": name}
        })

    def create_clear_message(self, stream_sid: str) -> str:
        """
        Create a clear message to stop audio playback (for barge-in).

        Args:
            stream_sid: Stream SID from Twilio

        Returns:
            JSON string to send via WebSocket
        """
        return json.dumps({
            "event": "clear",
            "streamSid": stream_sid
        })


# Global Media Streams service instance
media_streams_service = MediaStreamsService()
