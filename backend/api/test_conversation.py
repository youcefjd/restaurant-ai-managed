"""Test endpoint for direct conversation testing without Twilio"""

from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.conversation_handler import conversation_handler
from backend.models_platform import RestaurantAccount

router = APIRouter()


class ConversationTestRequest(BaseModel):
    """Request for testing conversation"""
    phone: str
    message: str
    account_id: int
    context: Optional[dict] = None


class ConversationTestResponse(BaseModel):
    """Response from conversation test"""
    message: str
    intent: str
    context: dict
    order_id: Optional[int] = None
    booking_id: Optional[int] = None


@router.post("/test-conversation", response_model=ConversationTestResponse)
async def test_conversation(
    request: ConversationTestRequest,
    db: Session = Depends(get_db)
):
    """
    Test conversation handler directly without Twilio TwiML
    For end-to-end testing only
    """
    # Get restaurant account
    account = db.query(RestaurantAccount).filter(
        RestaurantAccount.id == request.account_id
    ).first()

    if not account:
        return ConversationTestResponse(
            message="Restaurant not found",
            intent="error",
            context={}
        )

    # Process conversation
    context = request.context or {}
    result = await conversation_handler.process_message(
        message=request.message,
        phone=request.phone,
        restaurant_id=account.id,
        context=context,
        db=db
    )

    return ConversationTestResponse(
        message=result.get('message', ''),
        intent=result.get('intent', 'unknown'),
        context=result.get('context', {}),
        order_id=result.get('context', {}).get('order_id'),
        booking_id=result.get('context', {}).get('booking_id')
    )
