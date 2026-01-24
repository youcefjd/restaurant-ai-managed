"""
Service for saving and managing conversation transcripts.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.database import SupabaseDB

logger = logging.getLogger(__name__)


class TranscriptService:
    """Service for managing conversation transcripts."""

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
        # Check if transcript already exists
        existing = db.query_one("transcripts", {
            "conversation_id": conversation_id,
            "account_id": account_id
        })

        if existing:
            # Update existing transcript
            update_data = {
                "messages": messages,
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
                "messages": messages,
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

        # Add new message
        messages = transcript.get("messages") or []
        messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })

        updated = db.update("transcripts", transcript["id"], {
            "messages": messages,
            "updated_at": datetime.now().isoformat()
        })

        return updated


# Global instance
transcript_service = TranscriptService()
