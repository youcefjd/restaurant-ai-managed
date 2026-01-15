"""
Transcript API endpoints for viewing SMS and voice call conversations.
"""

import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database import get_db
from backend.models_platform import Transcript, RestaurantAccount, TranscriptType

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/accounts/{account_id}/transcripts")
async def list_transcripts(
    account_id: int,
    transcript_type: Optional[str] = Query(None, description="Filter by type: 'sms' or 'voice'"),
    customer_phone: Optional[str] = Query(None, description="Filter by customer phone number"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List transcripts for a restaurant account.
    
    Args:
        account_id: Restaurant account ID
        transcript_type: Optional filter by type (sms or voice)
        customer_phone: Optional filter by customer phone number
        skip: Number of records to skip
        limit: Maximum number of records to return
    
    Returns:
        List of transcripts with pagination info
    """
    # Verify account exists
    account = db.query(RestaurantAccount).filter(RestaurantAccount.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Build query
    query = db.query(Transcript).filter(Transcript.account_id == account_id)
    
    # Apply filters
    if transcript_type:
        if transcript_type not in ["sms", "voice"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="transcript_type must be 'sms' or 'voice'"
            )
        query = query.filter(Transcript.transcript_type == transcript_type)
    
    if customer_phone:
        query = query.filter(Transcript.customer_phone == customer_phone)
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering
    transcripts = query.order_by(desc(Transcript.created_at)).offset(skip).limit(limit).all()
    
    # Format response
    transcript_list = []
    for transcript in transcripts:
        transcript_list.append({
            "id": transcript.id,
            "transcript_type": transcript.transcript_type,
            "customer_phone": transcript.customer_phone,
            "twilio_phone": transcript.twilio_phone,
            "conversation_id": transcript.conversation_id,
            "messages": transcript.messages,
            "summary": transcript.summary,
            "outcome": transcript.outcome,
            "duration_seconds": transcript.duration_seconds,
            "created_at": transcript.created_at.isoformat(),
            "updated_at": transcript.updated_at.isoformat() if transcript.updated_at else None,
            "message_count": len(transcript.messages) if transcript.messages else 0
        })
    
    return {
        "transcripts": transcript_list,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/accounts/{account_id}/transcripts/{transcript_id}")
async def get_transcript(
    account_id: int,
    transcript_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific transcript by ID.
    
    Args:
        account_id: Restaurant account ID
        transcript_id: Transcript ID
    
    Returns:
        Full transcript details
    """
    # Verify account exists
    account = db.query(RestaurantAccount).filter(RestaurantAccount.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Get transcript
    transcript = db.query(Transcript).filter(
        Transcript.id == transcript_id,
        Transcript.account_id == account_id
    ).first()
    
    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcript not found"
        )
    
    return {
        "id": transcript.id,
        "transcript_type": transcript.transcript_type,
        "customer_phone": transcript.customer_phone,
        "twilio_phone": transcript.twilio_phone,
        "conversation_id": transcript.conversation_id,
        "messages": transcript.messages,
        "summary": transcript.summary,
        "outcome": transcript.outcome,
        "duration_seconds": transcript.duration_seconds,
        "created_at": transcript.created_at.isoformat(),
        "updated_at": transcript.updated_at.isoformat() if transcript.updated_at else None,
        "message_count": len(transcript.messages) if transcript.messages else 0
    }


@router.get("/accounts/{account_id}/transcripts/stats")
async def get_transcript_stats(
    account_id: int,
    db: Session = Depends(get_db)
):
    """
    Get statistics about transcripts for an account.
    
    Returns:
        Statistics including total counts, by type, recent activity, etc.
    """
    # Verify account exists
    account = db.query(RestaurantAccount).filter(RestaurantAccount.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Get all transcripts for this account
    all_transcripts = db.query(Transcript).filter(Transcript.account_id == account_id).all()
    
    # Calculate statistics
    total = len(all_transcripts)
    sms_count = sum(1 for t in all_transcripts if t.transcript_type == "sms")
    voice_count = sum(1 for t in all_transcripts if t.transcript_type == "voice")
    
    # Count outcomes
    outcomes = {}
    for transcript in all_transcripts:
        if transcript.outcome:
            outcomes[transcript.outcome] = outcomes.get(transcript.outcome, 0) + 1
    
    # Get recent activity (last 7 days)
    from datetime import timedelta
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_count = sum(1 for t in all_transcripts if t.created_at >= seven_days_ago)
    
    return {
        "total_transcripts": total,
        "sms_count": sms_count,
        "voice_count": voice_count,
        "recent_count": recent_count,
        "outcomes": outcomes
    }
