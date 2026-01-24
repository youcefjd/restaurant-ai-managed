"""
Transcript API endpoints for viewing SMS and voice call conversations.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query

from backend.database import get_db, SupabaseDB

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/accounts/{account_id}/transcripts")
async def list_transcripts(
    account_id: int,
    transcript_type: Optional[str] = Query(None, description="Filter by type: 'sms' or 'voice'"),
    customer_phone: Optional[str] = Query(None, description="Filter by customer phone number"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: SupabaseDB = Depends(get_db)
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
    account = db.query_one("restaurant_accounts", {"id": account_id})
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    # Validate transcript_type if provided
    if transcript_type:
        if transcript_type not in ["sms", "voice"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="transcript_type must be 'sms' or 'voice'"
            )

    # Build filters
    filters = {"account_id": account_id}
    if transcript_type:
        filters["transcript_type"] = transcript_type
    if customer_phone:
        filters["customer_phone"] = customer_phone

    # Get total count
    total = db.count("transcripts", filters)

    # Get transcripts with pagination and ordering
    transcripts = db.query_all(
        "transcripts",
        filters=filters,
        order_by="created_at",
        order_desc=True,
        offset=skip,
        limit=limit
    )

    # Format response
    transcript_list = []
    for transcript in transcripts:
        transcript_list.append({
            "id": transcript["id"],
            "transcript_type": transcript.get("transcript_type"),
            "customer_phone": transcript.get("customer_phone"),
            "twilio_phone": transcript.get("twilio_phone"),
            "conversation_id": transcript.get("conversation_id"),
            "messages": transcript.get("messages"),
            "summary": transcript.get("summary"),
            "outcome": transcript.get("outcome"),
            "duration_seconds": transcript.get("duration_seconds"),
            "order_id": transcript.get("order_id"),
            "created_at": transcript["created_at"],
            "updated_at": transcript.get("updated_at"),
            "message_count": len(transcript.get("messages") or [])
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
    db: SupabaseDB = Depends(get_db)
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
    account = db.query_one("restaurant_accounts", {"id": account_id})
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    # Get transcript
    transcript = db.query_one("transcripts", {"id": transcript_id, "account_id": account_id})

    if not transcript:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcript not found"
        )

    return {
        "id": transcript["id"],
        "transcript_type": transcript.get("transcript_type"),
        "customer_phone": transcript.get("customer_phone"),
        "twilio_phone": transcript.get("twilio_phone"),
        "conversation_id": transcript.get("conversation_id"),
        "messages": transcript.get("messages"),
        "summary": transcript.get("summary"),
        "outcome": transcript.get("outcome"),
        "duration_seconds": transcript.get("duration_seconds"),
        "order_id": transcript.get("order_id"),
        "created_at": transcript["created_at"],
        "updated_at": transcript.get("updated_at"),
        "message_count": len(transcript.get("messages") or [])
    }


@router.get("/accounts/{account_id}/transcripts/stats")
async def get_transcript_stats(
    account_id: int,
    db: SupabaseDB = Depends(get_db)
):
    """
    Get statistics about transcripts for an account.

    Returns:
        Statistics including total counts, by type, recent activity, etc.
    """
    # Verify account exists
    account = db.query_one("restaurant_accounts", {"id": account_id})
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    # Get all transcripts for this account
    all_transcripts = db.query_all(
        "transcripts",
        filters={"account_id": account_id},
        limit=10000  # Large limit to get all
    )

    # Calculate statistics
    total = len(all_transcripts)
    sms_count = sum(1 for t in all_transcripts if t.get("transcript_type") == "sms")
    voice_count = sum(1 for t in all_transcripts if t.get("transcript_type") == "voice")

    # Count outcomes
    outcomes = {}
    for transcript in all_transcripts:
        outcome = transcript.get("outcome")
        if outcome:
            outcomes[outcome] = outcomes.get(outcome, 0) + 1

    # Get recent activity (last 7 days)
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent_count = 0
    for t in all_transcripts:
        created_at = t.get("created_at")
        if created_at:
            # Parse ISO format datetime string
            if isinstance(created_at, str):
                try:
                    created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    # Compare as naive datetime (remove timezone info for comparison)
                    if created_dt.replace(tzinfo=None) >= seven_days_ago:
                        recent_count += 1
                except (ValueError, TypeError):
                    pass
            elif isinstance(created_at, datetime):
                if created_at >= seven_days_ago:
                    recent_count += 1

    return {
        "total_transcripts": total,
        "sms_count": sms_count,
        "voice_count": voice_count,
        "recent_count": recent_count,
        "outcomes": outcomes
    }
