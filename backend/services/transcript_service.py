"""
Service for saving and managing conversation transcripts.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from backend.models_platform import Transcript, TranscriptType

logger = logging.getLogger(__name__)


class TranscriptService:
    """Service for managing conversation transcripts."""
    
    @staticmethod
    def save_transcript(
        db: Session,
        account_id: int,
        transcript_type: str,
        customer_phone: str,
        conversation_id: str,
        messages: List[Dict[str, Any]],
        twilio_phone: Optional[str] = None,
        summary: Optional[str] = None,
        outcome: Optional[str] = None,
        duration_seconds: Optional[int] = None
    ) -> Transcript:
        """
        Save or update a transcript.
        
        Args:
            db: Database session
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
            Created or updated Transcript object
        """
        # Check if transcript already exists
        existing = db.query(Transcript).filter(
            Transcript.conversation_id == conversation_id,
            Transcript.account_id == account_id
        ).first()
        
        if existing:
            # Update existing transcript
            existing.messages = messages
            existing.summary = summary
            existing.outcome = outcome
            if duration_seconds is not None:
                existing.duration_seconds = duration_seconds
            existing.updated_at = datetime.now()
            db.commit()
            db.refresh(existing)
            logger.info(f"Updated transcript {existing.id} for conversation {conversation_id}")
            return existing
        else:
            # Create new transcript
            transcript = Transcript(
                account_id=account_id,
                transcript_type=transcript_type,
                customer_phone=customer_phone,
                twilio_phone=twilio_phone,
                conversation_id=conversation_id,
                messages=messages,
                summary=summary,
                outcome=outcome,
                duration_seconds=duration_seconds
            )
            db.add(transcript)
            db.commit()
            db.refresh(transcript)
            logger.info(f"Created transcript {transcript.id} for conversation {conversation_id}")
            return transcript
    
    @staticmethod
    def add_message_to_transcript(
        db: Session,
        conversation_id: str,
        account_id: int,
        role: str,
        content: str
    ) -> Optional[Transcript]:
        """
        Add a message to an existing transcript.
        
        Args:
            db: Database session
            conversation_id: Conversation ID
            account_id: Restaurant account ID
            role: "user" or "assistant"
            content: Message content
        
        Returns:
            Updated Transcript object or None if not found
        """
        transcript = db.query(Transcript).filter(
            Transcript.conversation_id == conversation_id,
            Transcript.account_id == account_id
        ).first()
        
        if not transcript:
            return None
        
        # Add new message
        if not transcript.messages:
            transcript.messages = []
        
        transcript.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        transcript.updated_at = datetime.now()
        db.commit()
        db.refresh(transcript)
        
        return transcript


# Global instance
transcript_service = TranscriptService()
