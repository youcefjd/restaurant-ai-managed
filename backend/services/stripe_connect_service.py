"""
Stripe Connect service for marketplace payments.

Handles restaurant onboarding to Stripe Connect and marketplace payment
processing with automatic commission splits.

Uses Supabase for database operations.
"""

import os
import logging
from typing import Dict, Any, Optional
import stripe

from backend.database import SupabaseDB, get_db_context

logger = logging.getLogger(__name__)


class StripeConnectService:
    """Service for Stripe Connect marketplace functionality."""

    def __init__(self, db: Optional[SupabaseDB] = None):
        """Initialize Stripe Connect service."""
        self.secret_key = os.getenv("STRIPE_SECRET_KEY")
        self._db = db

        if self.secret_key and self.secret_key.startswith("sk_"):
            stripe.api_key = self.secret_key
            self.enabled = True
        else:
            self.enabled = False
            logger.warning("Stripe Connect disabled - Stripe credentials not configured")

    def _get_db(self) -> SupabaseDB:
        """Get database instance, creating one if not provided."""
        if self._db is None:
            self._db = SupabaseDB()
        return self._db

    def get_restaurant_account(
        self,
        db: SupabaseDB,
        account_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get a restaurant account by ID.

        Args:
            db: SupabaseDB instance
            account_id: Restaurant account ID

        Returns:
            Restaurant account dict or None
        """
        return db.query_one("restaurant_accounts", {"id": account_id})

    def get_restaurant_account_by_stripe_id(
        self,
        db: SupabaseDB,
        stripe_account_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a restaurant account by Stripe Connect account ID.

        Args:
            db: SupabaseDB instance
            stripe_account_id: Stripe Connect account ID

        Returns:
            Restaurant account dict or None
        """
        return db.query_one("restaurant_accounts", {"stripe_account_id": stripe_account_id})

    def update_stripe_account_id(
        self,
        db: SupabaseDB,
        account_id: int,
        stripe_account_id: str
    ) -> Dict[str, Any]:
        """
        Update the Stripe account ID for a restaurant account.

        Args:
            db: SupabaseDB instance
            account_id: Restaurant account ID
            stripe_account_id: Stripe Connect account ID

        Returns:
            Updated restaurant account dict
        """
        return db.update("restaurant_accounts", account_id, {"stripe_account_id": stripe_account_id})

    def get_order(
        self,
        db: SupabaseDB,
        order_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get an order by ID.

        Args:
            db: SupabaseDB instance
            order_id: Order ID

        Returns:
            Order dict or None
        """
        return db.query_one("orders", {"id": order_id})

    def update_order_payment_status(
        self,
        db: SupabaseDB,
        order_id: int,
        payment_intent_id: str,
        payment_status: str
    ) -> Dict[str, Any]:
        """
        Update the payment status of an order.

        Args:
            db: SupabaseDB instance
            order_id: Order ID
            payment_intent_id: Stripe payment intent ID
            payment_status: Payment status (pending, succeeded, failed)

        Returns:
            Updated order dict
        """
        return db.update("orders", order_id, {
            "payment_intent_id": payment_intent_id,
            "payment_status": payment_status
        })

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

    def create_connected_account_and_save(
        self,
        db: SupabaseDB,
        restaurant_account_id: int,
        business_name: str,
        owner_email: str,
        country: str = "US"
    ) -> Dict[str, Any]:
        """
        Create a Stripe Connect account and save the ID to the database.

        Args:
            db: SupabaseDB instance
            restaurant_account_id: Restaurant account ID in database
            business_name: Restaurant business name
            owner_email: Owner's email address
            country: Country code (default: US)

        Returns:
            Dict with Stripe account ID and onboarding status
        """
        result = self.create_connected_account(business_name, owner_email, country)

        if result["status"] == "success":
            # Save Stripe account ID to database
            self.update_stripe_account_id(db, restaurant_account_id, result["account_id"])
            logger.info(f"Saved Stripe account {result['account_id']} to restaurant account {restaurant_account_id}")

        return result

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

    def create_payment_for_order(
        self,
        db: SupabaseDB,
        order_id: int
    ) -> Dict[str, Any]:
        """
        Create a marketplace payment for an order.

        Looks up the order and restaurant account, calculates commission,
        and creates the payment intent.

        Args:
            db: SupabaseDB instance
            order_id: Order ID to charge for

        Returns:
            Dict with payment intent details and breakdown
        """
        if not self.enabled:
            return {"status": "disabled", "message": "Stripe Connect not available"}

        # Get order
        order = self.get_order(db, order_id)
        if not order:
            return {"status": "error", "message": "Order not found"}

        # Get restaurant
        restaurant = db.query_one("restaurants", {"id": order["restaurant_id"]})
        if not restaurant or not restaurant.get("account_id"):
            return {"status": "error", "message": "Restaurant not properly configured"}

        # Get restaurant account
        account = self.get_restaurant_account(db, restaurant["account_id"])
        if not account:
            return {"status": "error", "message": "Restaurant account not found"}

        if not account.get("stripe_account_id"):
            return {"status": "error", "message": "Restaurant has not completed Stripe Connect onboarding"}

        # Calculate commission
        commission_rate = account.get("platform_commission_rate", 5)  # Default 5%
        platform_fee = int(order["total"] * (commission_rate / 100))

        # Create payment intent
        result = self.create_payment_intent_with_transfer(
            amount_cents=order["total"],
            connected_account_id=account["stripe_account_id"],
            platform_fee_cents=platform_fee,
            description=f"Order #{order['id']} - {account['business_name']}",
            metadata={
                "order_id": str(order["id"]),
                "restaurant_account_id": str(account["id"]),
                "customer_id": str(order.get("customer_id", ""))
            }
        )

        if result["status"] == "success":
            # Update order with payment intent ID
            self.update_order_payment_status(db, order_id, result["payment_intent_id"], "pending")

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

        return result

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

    def get_account_status_for_restaurant(
        self,
        db: SupabaseDB,
        restaurant_account_id: int
    ) -> Dict[str, Any]:
        """
        Get the Stripe Connect status for a restaurant account.

        Args:
            db: SupabaseDB instance
            restaurant_account_id: Restaurant account ID in database

        Returns:
            Dict with account status
        """
        account = self.get_restaurant_account(db, restaurant_account_id)

        if not account:
            return {"status": "error", "message": "Restaurant account not found"}

        if not account.get("stripe_account_id"):
            return {
                "status": "not_onboarded",
                "message": "Restaurant has not started Stripe Connect onboarding"
            }

        result = self.get_account_status(account["stripe_account_id"])

        if result["status"] == "success":
            result["restaurant_account_id"] = restaurant_account_id
            result["business_name"] = account.get("business_name")

        return result

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

    def get_balance_for_restaurant(
        self,
        db: SupabaseDB,
        restaurant_account_id: int
    ) -> Dict[str, Any]:
        """
        Get the Stripe balance for a restaurant account.

        Args:
            db: SupabaseDB instance
            restaurant_account_id: Restaurant account ID in database

        Returns:
            Dict with balance information
        """
        account = self.get_restaurant_account(db, restaurant_account_id)

        if not account:
            return {"status": "error", "message": "Restaurant account not found"}

        if not account.get("stripe_account_id"):
            return {"status": "error", "message": "Restaurant has not completed Stripe Connect onboarding"}

        result = self.get_balance(account["stripe_account_id"])

        if result["status"] == "success":
            result["restaurant_account_id"] = restaurant_account_id
            result["business_name"] = account.get("business_name")

        return result

    def handle_webhook_event(
        self,
        db: SupabaseDB,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle a Stripe Connect webhook event.

        Args:
            db: SupabaseDB instance
            event_type: Stripe event type
            event_data: Event data from Stripe

        Returns:
            Dict with handling result
        """
        logger.info(f"Processing Stripe Connect webhook: {event_type}")

        if event_type == "account.updated":
            # Restaurant completed onboarding or updated details
            stripe_account_id = event_data["data"]["object"]["id"]
            account = self.get_restaurant_account_by_stripe_id(db, stripe_account_id)

            if account:
                charges_enabled = event_data["data"]["object"].get("charges_enabled", False)
                payouts_enabled = event_data["data"]["object"].get("payouts_enabled", False)

                # Update account status in database if needed
                db.update("restaurant_accounts", account["id"], {
                    "stripe_charges_enabled": charges_enabled,
                    "stripe_payouts_enabled": payouts_enabled
                })

                logger.info(f"Updated Stripe status for account {account['id']}: charges={charges_enabled}, payouts={payouts_enabled}")

            return {"status": "success", "event": "account.updated"}

        elif event_type == "payment_intent.succeeded":
            # Customer payment succeeded
            payment_intent = event_data["data"]["object"]
            order_id = payment_intent["metadata"].get("order_id")

            if order_id:
                self.update_order_payment_status(db, int(order_id), payment_intent["id"], "succeeded")
                logger.info(f"Payment succeeded for order {order_id}")

            return {"status": "success", "event": "payment_intent.succeeded", "order_id": order_id}

        elif event_type == "payment_intent.payment_failed":
            # Customer payment failed
            payment_intent = event_data["data"]["object"]
            order_id = payment_intent["metadata"].get("order_id")

            if order_id:
                self.update_order_payment_status(db, int(order_id), payment_intent["id"], "failed")
                logger.info(f"Payment failed for order {order_id}")

            return {"status": "success", "event": "payment_intent.payment_failed", "order_id": order_id}

        elif event_type == "transfer.created":
            # Money transferred to restaurant
            transfer = event_data["data"]["object"]
            amount = transfer["amount"]
            logger.info(f"Transfer created: ${amount/100:.2f}")

            return {"status": "success", "event": "transfer.created", "amount": amount}

        else:
            logger.info(f"Unhandled webhook event type: {event_type}")
            return {"status": "success", "event": event_type, "handled": False}


# Global Stripe Connect service instance
stripe_connect_service = StripeConnectService()
