"""
Stripe Connect API endpoints for marketplace payments.

Handles restaurant onboarding to Stripe and marketplace payment processing.
Most endpoints require authentication (either admin or restaurant owner).
"""

import logging
from typing import Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field

from backend.database import get_db, SupabaseDB
from backend.services.stripe_connect_service import stripe_connect_service
from backend.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


# Pydantic schemas

class ConnectOnboardingRequest(BaseModel):
    """Request to start Stripe Connect onboarding."""
    account_id: int = Field(..., description="Restaurant account ID")
    refresh_url: str = Field(..., description="URL to redirect if link expires")
    return_url: str = Field(..., description="URL to redirect after completion")


class ConnectPaymentRequest(BaseModel):
    """Request to create a marketplace payment."""
    order_id: int = Field(..., description="Order ID to charge for")
    customer_email: str = Field(..., description="Customer email for receipt")


class BalanceResponse(BaseModel):
    """Restaurant balance response."""
    available_cents: int
    pending_cents: int
    available_display: str
    pending_display: str


# Endpoints

@router.post("/onboard")
async def onboard_to_stripe(
    request_data: ConnectOnboardingRequest,
    db: SupabaseDB = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Start Stripe Connect onboarding for a restaurant.

    Creates a Stripe Connect account and returns an onboarding link.
    Restaurant owner completes verification through Stripe's hosted flow.
    """
    # Get restaurant account
    account = db.query_one("restaurant_accounts", {"id": request_data.account_id})

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant account not found"
        )

    # Check if already has Stripe account
    if account.get("stripe_account_id"):
        # Just create a new onboarding link
        result = stripe_connect_service.create_account_link(
            account_id=account["stripe_account_id"],
            refresh_url=request_data.refresh_url,
            return_url=request_data.return_url
        )

        if result["status"] == "success":
            return {
                "status": "existing_account",
                "onboarding_url": result["url"],
                "stripe_account_id": account["stripe_account_id"]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Failed to create onboarding link")
            )

    # Create new Stripe Connect account
    result = stripe_connect_service.create_connected_account(
        business_name=account["business_name"],
        owner_email=account["owner_email"],
        country="US"
    )

    if result["status"] != "success":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("message", "Failed to create Stripe account")
        )

    # Save Stripe account ID
    db.update("restaurant_accounts", account["id"], {"stripe_account_id": result["account_id"]})

    logger.info(f"Created Stripe Connect account for {account['business_name']}: {result['account_id']}")

    # Create onboarding link
    link_result = stripe_connect_service.create_account_link(
        account_id=result["account_id"],
        refresh_url=request_data.refresh_url,
        return_url=request_data.return_url
    )

    if link_result["status"] == "success":
        return {
            "status": "success",
            "onboarding_url": link_result["url"],
            "stripe_account_id": result["account_id"]
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create onboarding link"
        )


@router.get("/status/{account_id}")
async def get_stripe_status(
    account_id: int,
    db: SupabaseDB = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get Stripe Connect onboarding status for a restaurant.

    Shows whether they can accept payments and what requirements remain.
    """
    # Get restaurant account
    account = db.query_one("restaurant_accounts", {"id": account_id})

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant account not found"
        )

    if not account.get("stripe_account_id"):
        return {
            "status": "not_onboarded",
            "message": "Restaurant has not started Stripe Connect onboarding"
        }

    # Get account status from Stripe
    result = stripe_connect_service.get_account_status(account["stripe_account_id"])

    if result["status"] == "success":
        return {
            "status": "onboarded",
            "stripe_account_id": account["stripe_account_id"],
            "charges_enabled": result["charges_enabled"],
            "payouts_enabled": result["payouts_enabled"],
            "details_submitted": result["details_submitted"],
            "requirements": result["requirements"]
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("message", "Failed to retrieve account status")
        )


@router.post("/charge")
async def create_marketplace_charge(
    payment_request: ConnectPaymentRequest,
    db: SupabaseDB = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Create a marketplace payment with automatic commission split.

    Customer pays full amount, platform takes commission,
    restaurant receives remainder automatically.
    """
    # Get order
    order = db.query_one("orders", {"id": payment_request.order_id})
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )

    # Get restaurant and account
    restaurant = db.query_one("restaurants", {"id": order["restaurant_id"]})
    if not restaurant or not restaurant.get("account_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Restaurant not properly configured"
        )

    account = db.query_one("restaurant_accounts", {"id": restaurant["account_id"]})

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant account not found"
        )

    if not account.get("stripe_account_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Restaurant has not completed Stripe Connect onboarding"
        )

    # Calculate commission
    platform_fee = int(order["total"] * (account["platform_commission_rate"] / 100))

    # Create payment intent with transfer
    result = stripe_connect_service.create_payment_intent_with_transfer(
        amount_cents=order["total"],
        connected_account_id=account["stripe_account_id"],
        platform_fee_cents=platform_fee,
        description=f"Order #{order['id']} - {account['business_name']}",
        metadata={
            "order_id": str(order["id"]),
            "restaurant_account_id": str(account["id"]),
            "customer_id": str(order["customer_id"])
        }
    )

    if result["status"] == "success":
        return {
            "status": "success",
            "payment_intent_id": result["payment_intent_id"],
            "client_secret": result["client_secret"],
            "breakdown": {
                "total_cents": order["total"],
                "total_display": f"${order['total'] / 100:.2f}",
                "platform_commission_cents": platform_fee,
                "platform_commission_display": f"${platform_fee / 100:.2f}",
                "restaurant_receives_cents": order["total"] - platform_fee,
                "restaurant_receives_display": f"${(order['total'] - platform_fee) / 100:.2f}"
            }
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("message", "Failed to create payment")
        )


@router.get("/balance/{account_id}", response_model=BalanceResponse)
async def get_restaurant_balance(
    account_id: int,
    db: SupabaseDB = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get a restaurant's available and pending balance.

    Shows how much money they have available for payout.
    """
    # Get restaurant account
    account = db.query_one("restaurant_accounts", {"id": account_id})

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant account not found"
        )

    if not account.get("stripe_account_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Restaurant has not completed Stripe Connect onboarding"
        )

    # Get balance from Stripe
    result = stripe_connect_service.get_balance(account["stripe_account_id"])

    if result["status"] == "success":
        return BalanceResponse(
            available_cents=result["available_cents"],
            pending_cents=result["pending_cents"],
            available_display=result["available_display"],
            pending_display=result["pending_display"]
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("message", "Failed to retrieve balance")
        )


@router.post("/webhook")
async def stripe_connect_webhook(
    request: Request,
    db: SupabaseDB = Depends(get_db)
):
    """
    Handle Stripe Connect webhook events.

    Important events:
    - account.updated: When restaurant completes onboarding
    - payment_intent.succeeded: When customer payment succeeds
    - transfer.created: When money is transferred to restaurant
    """
    import stripe
    import os

    # Get webhook signature
    signature = request.headers.get("stripe-signature")
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header"
        )

    # Get raw body
    payload = await request.body()

    # Verify webhook signature
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if not webhook_secret:
        logger.error("STRIPE_WEBHOOK_SECRET not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook verification not configured"
        )

    try:
        event = stripe.Webhook.construct_event(
            payload, signature, webhook_secret
        )
        event_type = event.get("type")
        event_data = event.get("data", {}).get("object", {})
        logger.info(f"Received Stripe Connect webhook: {event_type}")

        if event_type == "account.updated":
            # Restaurant completed onboarding or updated details
            account_id = event_data.get("id")
            logger.info(f"Stripe account updated: {account_id}")

        elif event_type == "payment_intent.succeeded":
            # Customer payment succeeded
            order_id = event_data.get("metadata", {}).get("order_id")
            if order_id:
                logger.info(f"Payment succeeded for order {order_id}")

        elif event_type == "transfer.created":
            # Money transferred to restaurant
            amount = event_data.get("amount", 0)
            logger.info(f"Transfer created: ${amount/100:.2f}")

        return {"status": "success"}

    except stripe.error.SignatureVerificationError as e:
        logger.warning(f"Invalid Stripe webhook signature: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid signature"
        )
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook payload"
        )


@router.get("/dashboard-link/{account_id}")
async def get_stripe_dashboard_link(
    account_id: int,
    db: SupabaseDB = Depends(get_db),
    current_user: Dict = Depends(get_current_user)
):
    """
    Get a login link to restaurant's Stripe Express dashboard.

    Restaurants can view their payouts, transactions, and settings.
    """
    # Get restaurant account
    account = db.query_one("restaurant_accounts", {"id": account_id})

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant account not found"
        )

    if not account.get("stripe_account_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Restaurant has not completed Stripe Connect onboarding"
        )

    try:
        import stripe
        # Create login link for Express dashboard
        login_link = stripe.Account.create_login_link(account["stripe_account_id"])

        return {
            "status": "success",
            "dashboard_url": login_link.url
        }

    except Exception as e:
        logger.error(f"Error creating dashboard link: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create dashboard link"
        )
