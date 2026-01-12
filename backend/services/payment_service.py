"""
Payment processing service using Stripe API.

Handles payment intent creation, confirmation, and refunds for
restaurant reservations.
"""

import os
import logging
from typing import Dict, Any, Optional
from decimal import Decimal
import stripe

from backend.models import Booking, Customer, Restaurant

logger = logging.getLogger(__name__)


class PaymentService:
    """Service for processing payments via Stripe."""

    def __init__(self):
        """Initialize payment service."""
        self.secret_key = os.getenv("STRIPE_SECRET_KEY")
        self.publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY")

        if self.secret_key and self.secret_key.startswith("sk_"):
            stripe.api_key = self.secret_key
            self.enabled = True
        else:
            self.enabled = False
            logger.warning("Payment service disabled - Stripe credentials not configured")

    def create_payment_intent(
        self,
        booking: Booking,
        customer: Customer,
        restaurant: Restaurant,
        amount_cents: int,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a Stripe payment intent for a booking.

        Args:
            booking: Booking object
            customer: Customer object
            restaurant: Restaurant object
            amount_cents: Amount to charge in cents
            description: Payment description

        Returns:
            Dict with payment intent details (client_secret, payment_intent_id, etc.)
        """
        if not self.enabled:
            logger.warning("Payment intent creation skipped - Stripe not configured")
            return {
                "status": "disabled",
                "message": "Payment processing not available"
            }

        try:
            # Create payment description
            if not description:
                description = (
                    f"Reservation deposit for {restaurant.name} - "
                    f"{booking.booking_date} at {booking.booking_time}"
                )

            # Create payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency="usd",
                description=description,
                metadata={
                    "booking_id": str(booking.id),
                    "customer_id": str(customer.id),
                    "customer_phone": customer.phone,
                    "restaurant_id": str(restaurant.id),
                    "restaurant_name": restaurant.name,
                    "booking_date": str(booking.booking_date),
                    "booking_time": str(booking.booking_time),
                    "party_size": str(booking.party_size)
                },
                # Optionally connect to restaurant's Stripe account for marketplace model
                # application_fee_amount=int(amount_cents * 0.1),  # 10% platform fee
            )

            logger.info(f"Payment intent created: {payment_intent.id} for booking {booking.id}")

            return {
                "status": "success",
                "payment_intent_id": payment_intent.id,
                "client_secret": payment_intent.client_secret,
                "amount": amount_cents,
                "currency": "usd"
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment intent: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error creating payment intent: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": "Payment processing failed"
            }

    def confirm_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Confirm a payment was successful.

        Args:
            payment_intent_id: Stripe payment intent ID

        Returns:
            Dict with payment status
        """
        if not self.enabled:
            return {"status": "disabled"}

        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            return {
                "status": "success",
                "payment_status": payment_intent.status,
                "amount_received": payment_intent.amount_received,
                "booking_id": payment_intent.metadata.get("booking_id")
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error confirming payment: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

    def refund_payment(
        self,
        payment_intent_id: str,
        amount_cents: Optional[int] = None,
        reason: str = "requested_by_customer"
    ) -> Dict[str, Any]:
        """
        Refund a payment.

        Args:
            payment_intent_id: Stripe payment intent ID
            amount_cents: Amount to refund (None for full refund)
            reason: Refund reason (duplicate, fraudulent, requested_by_customer)

        Returns:
            Dict with refund status
        """
        if not self.enabled:
            logger.warning("Refund skipped - Stripe not configured")
            return {"status": "disabled"}

        try:
            refund_params = {
                "payment_intent": payment_intent_id,
                "reason": reason
            }

            if amount_cents:
                refund_params["amount"] = amount_cents

            refund = stripe.Refund.create(**refund_params)

            logger.info(f"Refund created: {refund.id} for payment {payment_intent_id}")

            return {
                "status": "success",
                "refund_id": refund.id,
                "amount": refund.amount,
                "refund_status": refund.status
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error creating refund: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

    def calculate_deposit_amount(
        self,
        party_size: int,
        deposit_per_person: int = 1000  # $10.00 per person
    ) -> int:
        """
        Calculate deposit amount based on party size.

        Args:
            party_size: Number of guests
            deposit_per_person: Deposit amount per person in cents

        Returns:
            Total deposit amount in cents
        """
        return party_size * deposit_per_person

    def create_checkout_session(
        self,
        booking: Booking,
        customer: Customer,
        restaurant: Restaurant,
        amount_cents: int,
        success_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """
        Create a Stripe Checkout session for hosted payment page.

        Args:
            booking: Booking object
            customer: Customer object
            restaurant: Restaurant object
            amount_cents: Amount to charge in cents
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect if payment is cancelled

        Returns:
            Dict with checkout session details
        """
        if not self.enabled:
            return {"status": "disabled"}

        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": "usd",
                            "product_data": {
                                "name": f"Reservation Deposit - {restaurant.name}",
                                "description": (
                                    f"Party of {booking.party_size} on "
                                    f"{booking.booking_date} at {booking.booking_time}"
                                ),
                            },
                            "unit_amount": amount_cents,
                        },
                        "quantity": 1,
                    },
                ],
                mode="payment",
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=customer.email,
                metadata={
                    "booking_id": str(booking.id),
                    "customer_id": str(customer.id),
                    "restaurant_id": str(restaurant.id)
                }
            )

            logger.info(f"Checkout session created: {checkout_session.id} for booking {booking.id}")

            return {
                "status": "success",
                "session_id": checkout_session.id,
                "checkout_url": checkout_session.url
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error creating checkout session: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        webhook_secret: Optional[str] = None
    ) -> Optional[stripe.Event]:
        """
        Verify Stripe webhook signature.

        Args:
            payload: Request body
            signature: Stripe-Signature header value
            webhook_secret: Webhook signing secret

        Returns:
            Stripe Event object if valid, None otherwise
        """
        if not webhook_secret:
            webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

        if not webhook_secret:
            logger.warning("Webhook verification skipped - no secret configured")
            return None

        try:
            event = stripe.Webhook.construct_event(
                payload, signature, webhook_secret
            )
            return event
        except ValueError:
            logger.error("Invalid webhook payload")
            return None
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid webhook signature")
            return None


# Global payment service instance
payment_service = PaymentService()
