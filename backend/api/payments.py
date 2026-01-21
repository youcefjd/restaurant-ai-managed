"""
Payment processing endpoints for Stripe integration.

Handles payment intent creation, checkout sessions, and webhook events.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, status, Header

from backend.database import get_db, SupabaseDB
from backend.services.payment_service import payment_service
from backend.services.sms_service import sms_service
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)


class PaymentIntentRequest(BaseModel):
    """Request to create a payment intent."""
    booking_id: int
    deposit_per_person: int = 1000  # $10.00 default


class PaymentIntentResponse(BaseModel):
    """Payment intent response."""
    status: str
    payment_intent_id: str = None
    client_secret: str = None
    amount: int = None
    currency: str = None
    message: str = None


class CheckoutSessionRequest(BaseModel):
    """Request to create a checkout session."""
    booking_id: int
    success_url: str
    cancel_url: str
    deposit_per_person: int = 1000


class CheckoutSessionResponse(BaseModel):
    """Checkout session response."""
    status: str
    session_id: str = None
    checkout_url: str = None
    message: str = None


@router.post("/create-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    request: PaymentIntentRequest,
    db: SupabaseDB = Depends(get_db)
):
    """
    Create a Stripe payment intent for a booking deposit.

    This generates a client secret that can be used with Stripe.js
    to collect payment on the frontend.
    """
    # Get booking
    booking = db.query_one("bookings", {"id": request.booking_id})
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    # Get customer and restaurant
    customer = db.query_one("customers", {"id": booking["customer_id"]})
    restaurant = db.query_one("restaurants", {"id": booking["restaurant_id"]})

    if not customer or not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer or restaurant not found"
        )

    # Calculate deposit amount
    amount_cents = payment_service.calculate_deposit_amount(
        booking["party_size"],
        request.deposit_per_person
    )

    # Create payment intent
    result = payment_service.create_payment_intent(
        booking=booking,
        customer=customer,
        restaurant=restaurant,
        amount_cents=amount_cents
    )

    if result["status"] == "success":
        # Store payment intent ID in booking (would need to add field to model)
        # For now, just return the result
        return PaymentIntentResponse(**result)
    else:
        return PaymentIntentResponse(**result)


@router.post("/create-checkout", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CheckoutSessionRequest,
    db: SupabaseDB = Depends(get_db)
):
    """
    Create a Stripe Checkout session for hosted payment page.

    This redirects customers to a Stripe-hosted payment page.
    """
    # Get booking
    booking = db.query_one("bookings", {"id": request.booking_id})
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    # Get customer and restaurant
    customer = db.query_one("customers", {"id": booking["customer_id"]})
    restaurant = db.query_one("restaurants", {"id": booking["restaurant_id"]})

    if not customer or not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer or restaurant not found"
        )

    # Calculate deposit amount
    amount_cents = payment_service.calculate_deposit_amount(
        booking["party_size"],
        request.deposit_per_person
    )

    # Create checkout session
    result = payment_service.create_checkout_session(
        booking=booking,
        customer=customer,
        restaurant=restaurant,
        amount_cents=amount_cents,
        success_url=request.success_url,
        cancel_url=request.cancel_url
    )

    if result["status"] == "success":
        return CheckoutSessionResponse(**result)
    else:
        return CheckoutSessionResponse(**result)


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db: SupabaseDB = Depends(get_db)
):
    """
    Handle Stripe webhook events.

    Important: This endpoint must be configured in your Stripe dashboard
    webhook settings.
    """
    if not stripe_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header"
        )

    # Get raw request body
    payload = await request.body()

    # Verify webhook signature
    event = payment_service.verify_webhook_signature(payload, stripe_signature)

    if not event:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature"
        )

    logger.info(f"Received Stripe webhook event: {event['type']}")

    # Handle different event types
    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        booking_id = payment_intent["metadata"].get("booking_id")

        if booking_id:
            # Update booking status
            booking = db.query_one("bookings", {"id": int(booking_id)})
            if booking:
                # Mark as confirmed
                db.update("bookings", int(booking_id), {"status": "confirmed"})

                # Send confirmation SMS
                try:
                    customer = db.query_one("customers", {"id": booking["customer_id"]})
                    restaurant = db.query_one("restaurants", {"id": booking["restaurant_id"]})
                    if customer and restaurant:
                        sms_service.send_booking_confirmation(booking, customer, restaurant)
                except Exception as e:
                    logger.error(f"Failed to send SMS: {e}")

                logger.info(f"Payment succeeded for booking {booking_id}")

    elif event["type"] == "payment_intent.payment_failed":
        payment_intent = event["data"]["object"]
        booking_id = payment_intent["metadata"].get("booking_id")

        if booking_id:
            # Update booking status
            booking = db.query_one("bookings", {"id": int(booking_id)})
            if booking:
                db.update("bookings", int(booking_id), {"status": "cancelled"})

                logger.warning(f"Payment failed for booking {booking_id}")

    elif event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        booking_id = session["metadata"].get("booking_id")

        if booking_id:
            booking = db.query_one("bookings", {"id": int(booking_id)})
            if booking:
                db.update("bookings", int(booking_id), {"status": "confirmed"})

                logger.info(f"Checkout session completed for booking {booking_id}")

    return {"status": "success"}


@router.post("/refund")
async def refund_payment(
    booking_id: int,
    payment_intent_id: str,
    amount_cents: int = None,
    db: SupabaseDB = Depends(get_db)
):
    """
    Refund a payment for a cancelled booking.

    Args:
        booking_id: Booking ID
        payment_intent_id: Stripe payment intent ID
        amount_cents: Amount to refund (None for full refund)
    """
    # Verify booking exists and is cancelled
    booking = db.query_one("bookings", {"id": booking_id})
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )

    # Process refund
    result = payment_service.refund_payment(
        payment_intent_id=payment_intent_id,
        amount_cents=amount_cents
    )

    if result["status"] == "success":
        return {
            "status": "success",
            "refund_id": result["refund_id"],
            "amount": result["amount"]
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("message", "Refund failed")
        )


@router.get("/health")
async def payment_health():
    """Health check for payment service."""
    return {
        "service": "payments",
        "enabled": payment_service.enabled,
        "status": "healthy" if payment_service.enabled else "disabled"
    }
