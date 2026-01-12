"""
Stripe Connect service for marketplace payments.

Handles restaurant onboarding to Stripe Connect and marketplace payment
processing with automatic commission splits.
"""

import os
import logging
from typing import Dict, Any, Optional
import stripe

logger = logging.getLogger(__name__)


class StripeConnectService:
    """Service for Stripe Connect marketplace functionality."""

    def __init__(self):
        """Initialize Stripe Connect service."""
        self.secret_key = os.getenv("STRIPE_SECRET_KEY")

        if self.secret_key and self.secret_key.startswith("sk_"):
            stripe.api_key = self.secret_key
            self.enabled = True
        else:
            self.enabled = False
            logger.warning("Stripe Connect disabled - Stripe credentials not configured")

    def create_account_link(
        self,
        account_id: str,
        refresh_url: str,
        return_url: str
    ) -> Dict[str, Any]:
        """
        Create an account link for restaurant to complete Stripe Connect onboarding.

        Args:
            account_id: Stripe Connect account ID
            refresh_url: URL to redirect if link expires
            return_url: URL to redirect after completion

        Returns:
            Dict with account link URL
        """
        if not self.enabled:
            return {"status": "disabled", "message": "Stripe Connect not available"}

        try:
            account_link = stripe.AccountLink.create(
                account=account_id,
                refresh_url=refresh_url,
                return_url=return_url,
                type="account_onboarding"
            )

            return {
                "status": "success",
                "url": account_link.url
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error creating account link: {str(e)}")
            return {"status": "error", "message": str(e)}

    def create_connected_account(
        self,
        business_name: str,
        owner_email: str,
        country: str = "US"
    ) -> Dict[str, Any]:
        """
        Create a Stripe Connect account for a restaurant.

        Args:
            business_name: Restaurant business name
            owner_email: Owner's email address
            country: Country code (default: US)

        Returns:
            Dict with Stripe account ID and onboarding status
        """
        if not self.enabled:
            return {"status": "disabled", "message": "Stripe Connect not available"}

        try:
            # Create Express account (easier onboarding for restaurants)
            account = stripe.Account.create(
                type="express",
                country=country,
                email=owner_email,
                capabilities={
                    "card_payments": {"requested": True},
                    "transfers": {"requested": True},
                },
                business_type="company",
                company={
                    "name": business_name
                }
            )

            logger.info(f"Created Stripe Connect account: {account.id} for {business_name}")

            return {
                "status": "success",
                "account_id": account.id,
                "charges_enabled": account.charges_enabled,
                "details_submitted": account.details_submitted
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error creating connected account: {str(e)}")
            return {"status": "error", "message": str(e)}

    def create_payment_intent_with_transfer(
        self,
        amount_cents: int,
        connected_account_id: str,
        platform_fee_cents: int,
        description: str,
        metadata: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Create a payment intent with automatic transfer to connected account.

        Platform takes commission, restaurant gets the rest.

        Args:
            amount_cents: Total amount to charge customer
            connected_account_id: Restaurant's Stripe Connect account ID
            platform_fee_cents: Platform commission amount
            description: Payment description
            metadata: Additional metadata

        Returns:
            Dict with payment intent details
        """
        if not self.enabled:
            return {"status": "disabled", "message": "Stripe Connect not available"}

        try:
            # Create payment intent
            # Customer pays full amount, platform takes fee, restaurant gets remainder
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency="usd",
                description=description,
                metadata=metadata,
                application_fee_amount=platform_fee_cents,  # Platform commission
                transfer_data={
                    "destination": connected_account_id  # Restaurant's account
                }
            )

            logger.info(
                f"Created payment intent {payment_intent.id}: "
                f"${amount_cents/100:.2f} total, ${platform_fee_cents/100:.2f} platform fee"
            )

            return {
                "status": "success",
                "payment_intent_id": payment_intent.id,
                "client_secret": payment_intent.client_secret,
                "amount": amount_cents,
                "platform_fee": platform_fee_cents,
                "restaurant_receives": amount_cents - platform_fee_cents
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error creating payment intent: {str(e)}")
            return {"status": "error", "message": str(e)}

    def create_checkout_session_with_connect(
        self,
        amount_cents: int,
        connected_account_id: str,
        platform_fee_cents: int,
        success_url: str,
        cancel_url: str,
        line_items: list,
        metadata: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Create Stripe Checkout session with Connect marketplace payment.

        Args:
            amount_cents: Total amount
            connected_account_id: Restaurant's Stripe account
            platform_fee_cents: Platform commission
            success_url: Redirect URL on success
            cancel_url: Redirect URL on cancel
            line_items: Checkout line items
            metadata: Payment metadata

        Returns:
            Dict with checkout session details
        """
        if not self.enabled:
            return {"status": "disabled", "message": "Stripe Connect not available"}

        try:
            session = stripe.checkout.Session.create(
                mode="payment",
                line_items=line_items,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata,
                payment_intent_data={
                    "application_fee_amount": platform_fee_cents,
                    "transfer_data": {
                        "destination": connected_account_id
                    }
                }
            )

            logger.info(f"Created checkout session {session.id} with Connect transfer")

            return {
                "status": "success",
                "session_id": session.id,
                "checkout_url": session.url
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error creating checkout session: {str(e)}")
            return {"status": "error", "message": str(e)}

    def get_account_status(self, account_id: str) -> Dict[str, Any]:
        """
        Get the onboarding status of a connected account.

        Args:
            account_id: Stripe Connect account ID

        Returns:
            Dict with account status
        """
        if not self.enabled:
            return {"status": "disabled"}

        try:
            account = stripe.Account.retrieve(account_id)

            return {
                "status": "success",
                "account_id": account.id,
                "charges_enabled": account.charges_enabled,
                "payouts_enabled": account.payouts_enabled,
                "details_submitted": account.details_submitted,
                "requirements": {
                    "currently_due": account.requirements.currently_due,
                    "eventually_due": account.requirements.eventually_due,
                    "past_due": account.requirements.past_due
                }
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving account: {str(e)}")
            return {"status": "error", "message": str(e)}

    def create_payout(
        self,
        connected_account_id: str,
        amount_cents: int,
        description: str
    ) -> Dict[str, Any]:
        """
        Create a manual payout to a connected account.

        Note: This is usually automatic with transfer_data,
        but can be used for manual adjustments.

        Args:
            connected_account_id: Restaurant's Stripe account
            amount_cents: Amount to pay out
            description: Payout description

        Returns:
            Dict with payout details
        """
        if not self.enabled:
            return {"status": "disabled"}

        try:
            transfer = stripe.Transfer.create(
                amount=amount_cents,
                currency="usd",
                destination=connected_account_id,
                description=description
            )

            logger.info(f"Created transfer {transfer.id}: ${amount_cents/100:.2f}")

            return {
                "status": "success",
                "transfer_id": transfer.id,
                "amount": amount_cents
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error creating transfer: {str(e)}")
            return {"status": "error", "message": str(e)}

    def get_balance(self, connected_account_id: str) -> Dict[str, Any]:
        """
        Get the balance of a connected account.

        Args:
            connected_account_id: Restaurant's Stripe account

        Returns:
            Dict with balance information
        """
        if not self.enabled:
            return {"status": "disabled"}

        try:
            balance = stripe.Balance.retrieve(
                stripe_account=connected_account_id
            )

            available_cents = sum(b.amount for b in balance.available)
            pending_cents = sum(b.amount for b in balance.pending)

            return {
                "status": "success",
                "available_cents": available_cents,
                "pending_cents": pending_cents,
                "available_display": f"${available_cents/100:.2f}",
                "pending_display": f"${pending_cents/100:.2f}"
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving balance: {str(e)}")
            return {"status": "error", "message": str(e)}


# Global Stripe Connect service instance
stripe_connect_service = StripeConnectService()
