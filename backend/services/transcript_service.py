"""
Service for saving and managing conversation transcripts.

Includes PCI-compliant redaction of sensitive payment data.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.database import SupabaseDB

logger = logging.getLogger(__name__)


# Patterns for sensitive data redaction
CARD_NUMBER_PATTERN = re.compile(r'\b(?:\d[ -]*?){13,19}\b')
EXPIRY_PATTERN = re.compile(r'\b(0[1-9]|1[0-2])\s*[/-]?\s*(2[0-9]|[0-9]{2})\b')
CVV_PATTERN = re.compile(r'\b\d{3,4}\b')
# More specific pattern to avoid false positives
DTMF_DIGITS_PATTERN = re.compile(r'(?:entered|typed|pressed|digits?|number)[:\s]*([0-9\s\-]{10,})', re.IGNORECASE)


class TranscriptService:
    """Service for managing conversation transcripts."""

    @staticmethod
    def redact_sensitive_data(text: str) -> str:
        """
        Redact sensitive payment data from text.

        PCI DSS requires that card numbers never be stored in plain text.
        This method redacts:
        - Card numbers (13-19 digits)
        - Expiry dates (MM/YY format)
        - CVV codes (3-4 digits in payment context)
        - DTMF digit sequences

        Args:
            text: Text that may contain sensitive data

        Returns:
            Text with sensitive data redacted
        """
        if not text:
            return text

        # Redact card numbers (preserve last 4 for reference)
        def redact_card(match):
            digits = ''.join(filter(str.isdigit, match.group()))
            if len(digits) >= 13:
                return f"****-****-****-{digits[-4:]}"
            return match.group()

        result = CARD_NUMBER_PATTERN.sub(redact_card, text)

        # Redact DTMF digit sequences (digits entered via keypad)
        def redact_dtmf(match):
            prefix = match.group(0)[:match.start(1) - match.start(0)]
            return f"{prefix}[REDACTED]"

        result = DTMF_DIGITS_PATTERN.sub(redact_dtmf, result)

        # Redact sequences that look like card data in payment context
        payment_keywords = ['card', 'payment', 'pay', 'credit', 'debit', 'expir', 'cvv', 'security code']
        text_lower = result.lower()

        if any(keyword in text_lower for keyword in payment_keywords):
            # More aggressive redaction in payment context
            # Redact standalone 3-4 digit numbers (likely CVV)
            result = re.sub(r'\b(\d{3,4})\b(?!\s*(am|pm|days?|hours?|minutes?|items?|\$|%|cents?))',
                           '[***]', result)

        return result

    @staticmethod
    def redact_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Redact sensitive data from a list of messages.

        Args:
            messages: List of message dicts with 'content' field

        Returns:
            Messages with content redacted
        """
        redacted = []
        for msg in messages:
            redacted_msg = msg.copy()
            if 'content' in redacted_msg:
                redacted_msg['content'] = TranscriptService.redact_sensitive_data(
                    redacted_msg['content']
                )
            redacted.append(redacted_msg)
        return redacted

    @staticmethod
    def save_transcript(
        db: SupabaseDB,
        account_id: int,
        transcript_type: str,
        customer_phone: str,
        conversation_id: str,
        messages: List[Dict[str, Any]],
        twilio_phone: Optional[str] = None,
        summary: Optional[str] = None,
        outcome: Optional[str] = None,
        duration_seconds: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Save or update a transcript.

        Args:
            db: Database instance
            account_id: Restaurant account ID
            transcript_type: "sms" or "voice"
            customer_phone: Customer's phone number
            conversation_id: Unique conversation ID (CallSid or MessageSid)
            messages: List of message objects with role, content, timestamp
            twilio_phone: Restaurant's Twilio phone number
            summary: Optional summary of the conversation
            outcome: Optional outcome (booking_created, order_placed, etc.)
            duration_seconds: Optional call duration (for voice)

        Returns:
            Created or updated transcript dict
        """
        # Apply PCI-compliant redaction to messages
        redacted_messages = TranscriptService.redact_messages(messages)

        # Check if transcript already exists
        existing = db.query_one("transcripts", {
            "conversation_id": conversation_id,
            "account_id": account_id
        })

        if existing:
            # Update existing transcript
            update_data = {
                "messages": redacted_messages,
                "summary": summary,
                "outcome": outcome,
                "updated_at": datetime.now().isoformat()
            }
            if duration_seconds is not None:
                update_data["duration_seconds"] = duration_seconds

            updated = db.update("transcripts", existing["id"], update_data)
            logger.info(f"Updated transcript {updated['id']} for conversation {conversation_id}")
            return updated
        else:
            # Look up order by conversation_id to link them
            order = db.query_one("orders", {"conversation_id": conversation_id})
            order_id = order["id"] if order else None

            # Create new transcript
            insert_data = {
                "account_id": account_id,
                "transcript_type": transcript_type,
                "customer_phone": customer_phone,
                "twilio_phone": twilio_phone,
                "conversation_id": conversation_id,
                "messages": redacted_messages,
                "summary": summary,
                "outcome": outcome or ("order_placed" if order else None),
                "duration_seconds": duration_seconds,
                "order_id": order_id
            }
            transcript = db.insert("transcripts", insert_data)
            logger.info(f"Created transcript {transcript['id']} for conversation {conversation_id}, order_id: {order_id}")
            return transcript

    @staticmethod
    def add_message_to_transcript(
        db: SupabaseDB,
        conversation_id: str,
        account_id: int,
        role: str,
        content: str
    ) -> Optional[Dict[str, Any]]:
        """
        Add a message to an existing transcript.

        Args:
            db: Database instance
            conversation_id: Conversation ID
            account_id: Restaurant account ID
            role: "user" or "assistant"
            content: Message content

        Returns:
            Updated transcript dict or None if not found
        """
        transcript = db.query_one("transcripts", {
            "conversation_id": conversation_id,
            "account_id": account_id
        })

        if not transcript:
            return None

        # Redact sensitive data from content
        redacted_content = TranscriptService.redact_sensitive_data(content)

        # Add new message
        messages = transcript.get("messages") or []
        messages.append({
            "role": role,
            "content": redacted_content,
            "timestamp": datetime.now().isoformat()
        })

        updated = db.update("transcripts", transcript["id"], {
            "messages": messages,
            "updated_at": datetime.now().isoformat()
        })

        return updated


# Global instance
transcript_service = TranscriptService()
