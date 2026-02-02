"""
Payment Orchestrator Service.

Routes payments to the appropriate provider based on restaurant configuration:
1. Toast POS (if enabled) - for POS sync + payment
2. Stripe (if connected) - for payment only
3. Pay at pickup (fallback) - no card collection

Handles DTMF card collection state machine and payment authorization.
"""

import os
import logging
import hashlib
import base64
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

import stripe

from backend.database import SupabaseDB
from backend.services.toast_service import toast_service

logger = logging.getLogger(__name__)


class PaymentProvider(str, Enum):
    """Available payment providers."""
    TOAST = "toast"
    STRIPE = "stripe"
    PAY_AT_PICKUP = "pay_at_pickup"


class PaymentOrchestrator:
    """
    Orchestrates payment processing across multiple providers.

    Determines the appropriate payment provider for each restaurant
    and routes payments accordingly.
    """

    def __init__(self):
        """Initialize payment orchestrator."""
        self.stripe_secret = os.getenv("STRIPE_SECRET_KEY")
        self.stripe_enabled = bool(self.stripe_secret and self.stripe_secret.startswith("sk_"))

        if self.stripe_enabled:
            stripe.api_key = self.stripe_secret

        logger.info(f"Payment orchestrator initialized: Stripe={self.stripe_enabled}")

    async def get_payment_provider(
        self,
        restaurant_id: int,
        db: SupabaseDB
    ) -> PaymentProvider:
        """
        Determine the payment provider for a restaurant.

        Priority:
        1. Toast if enabled with valid config
        2. Stripe if connected
        3. Pay at pickup (fallback)

        Args:
            restaurant_id: Restaurant account ID
            db: Database instance

        Returns:
            PaymentProvider enum value
        """
        account = db.query_one("restaurant_accounts", {"id": restaurant_id})

        if not account:
            return PaymentProvider.PAY_AT_PICKUP

        # Check Toast
        if account.get("toast_enabled") and account.get("toast_restaurant_guid"):
            toast_config = await toast_service.get_restaurant_config(restaurant_id, db)
            if toast_config:
                return PaymentProvider.TOAST

        # Check Stripe Connect
        if account.get("stripe_account_id"):
            return PaymentProvider.STRIPE

        return PaymentProvider.PAY_AT_PICKUP

    async def can_collect_payment(
        self,
        restaurant_id: int,
        db: SupabaseDB
    ) -> Dict[str, Any]:
        """
        Check if restaurant can collect card payments via DTMF.

        Args:
            restaurant_id: Restaurant account ID
            db: Database instance

        Returns:
            Dict with can_collect flag and provider info
        """
        provider = await self.get_payment_provider(restaurant_id, db)

        if provider == PaymentProvider.PAY_AT_PICKUP:
            return {
                "can_collect": False,
                "provider": provider.value,
                "reason": "No payment provider configured"
            }

        return {
            "can_collect": True,
            "provider": provider.value
        }

    def create_payment_session(
        self,
        call_id: str,
        session_id: str,
        restaurant_id: int,
        amount_cents: int,
        db: SupabaseDB
    ) -> Dict[str, Any]:
        """
        Create a new payment session for DTMF collection.

        Args:
            call_id: Retell call ID
            session_id: LLM session ID for cart isolation
            restaurant_id: Restaurant account ID
            amount_cents: Amount to charge in cents
            db: Database instance

        Returns:
            Created session dict
        """
        # Check for existing session
        existing = db.query_one("payment_sessions", {"call_id": call_id})
        if existing:
            # Update existing session
            updated = db.update("payment_sessions", existing["id"], {
                "status": "collecting_card",
                "amount_cents": amount_cents,
                "error_message": None,
                "expires_at": (datetime.now() + timedelta(minutes=10)).isoformat()
            })
            logger.info(f"Reset existing payment session {existing['id']} for call {call_id}")
            return updated

        # Create new session
        session_data = {
            "call_id": call_id,
            "session_id": session_id,
            "restaurant_id": restaurant_id,
            "status": "collecting_card",
            "amount_cents": amount_cents,
            "guest_identifier": str(uuid.uuid4()),
            "expires_at": (datetime.now() + timedelta(minutes=10)).isoformat()
        }

        session = db.insert("payment_sessions", session_data)
        logger.info(f"Created payment session {session['id']} for call {call_id}")
        return session

    def get_payment_session(
        self,
        call_id: str,
        db: SupabaseDB
    ) -> Optional[Dict[str, Any]]:
        """Get payment session by call ID."""
        return db.query_one("payment_sessions", {"call_id": call_id})

    def update_payment_session(
        self,
        session_id: int,
        updates: Dict[str, Any],
        db: SupabaseDB
    ) -> Dict[str, Any]:
        """Update payment session."""
        return db.update("payment_sessions", session_id, updates)

    def encrypt_for_storage(self, data: str) -> str:
        """
        Encrypt data for temporary storage.

        In production, this should use proper encryption (AES-256).
        For now, we use base64 encoding as a placeholder.
        """
        # TODO: Implement AES-256 encryption with KMS key
        # For now, base64 encode (NOT SECURE - development only)
        return base64.b64encode(data.encode()).decode()

    def decrypt_from_storage(self, encrypted: str) -> str:
        """Decrypt data from storage."""
        # TODO: Implement AES-256 decryption
        return base64.b64decode(encrypted).decode()

    def hash_cvv(self, cvv: str) -> str:
        """Hash CVV for temporary verification (never stored)."""
        return hashlib.sha256(cvv.encode()).hexdigest()

    def validate_card_number(self, digits: str) -> Dict[str, Any]:
        """
        Validate card number format.

        Args:
            digits: Card number digits

        Returns:
            Dict with valid flag and message
        """
        # Remove any spaces or dashes
        clean_digits = "".join(filter(str.isdigit, digits))

        if len(clean_digits) < 13 or len(clean_digits) > 19:
            return {
                "valid": False,
                "message": "Card number should be 13-19 digits. Please try again."
            }

        # Luhn algorithm check
        def luhn_check(card_number: str) -> bool:
            total = 0
            reverse_digits = card_number[::-1]
            for i, digit in enumerate(reverse_digits):
                n = int(digit)
                if i % 2 == 1:
                    n *= 2
                    if n > 9:
                        n -= 9
                total += n
            return total % 10 == 0

        if not luhn_check(clean_digits):
            return {
                "valid": False,
                "message": "That card number doesn't look right. Please try again."
            }

        return {"valid": True, "clean_digits": clean_digits}

    def validate_expiry(self, digits: str) -> Dict[str, Any]:
        """
        Validate expiry date format (MMYY).

        Args:
            digits: Expiry digits

        Returns:
            Dict with valid flag and message
        """
        clean_digits = "".join(filter(str.isdigit, digits))

        if len(clean_digits) != 4:
            return {
                "valid": False,
                "message": "Please enter your expiry as 4 digits, like 0525 for May 2025."
            }

        month = int(clean_digits[:2])
        year = int(clean_digits[2:])

        if month < 1 or month > 12:
            return {
                "valid": False,
                "message": "Invalid month. Please enter as MMYY, like 0525."
            }

        # Check if expired
        current_year = datetime.now().year % 100
        current_month = datetime.now().month

        if year < current_year or (year == current_year and month < current_month):
            return {
                "valid": False,
                "message": "That card appears to be expired. Please use a different card."
            }

        return {"valid": True, "clean_digits": clean_digits}

    def validate_cvv(self, digits: str) -> Dict[str, Any]:
        """
        Validate CVV format.

        Args:
            digits: CVV digits

        Returns:
            Dict with valid flag and message
        """
        clean_digits = "".join(filter(str.isdigit, digits))

        if len(clean_digits) < 3 or len(clean_digits) > 4:
            return {
                "valid": False,
                "message": "CVV should be 3 or 4 digits. Please try again."
            }

        return {"valid": True, "clean_digits": clean_digits}

    async def authorize_payment(
        self,
        restaurant_id: int,
        amount_cents: int,
        card_number: str,
        expiry: str,
        cvv: str,
        guest_identifier: str,
        db: SupabaseDB
    ) -> Dict[str, Any]:
        """
        Authorize payment through the appropriate provider.

        Routes to Toast or Stripe based on restaurant configuration.

        Args:
            restaurant_id: Restaurant account ID
            amount_cents: Amount in cents
            card_number: Plain card number
            expiry: Expiry in MMYY format
            cvv: CVV
            guest_identifier: Unique guest ID
            db: Database instance

        Returns:
            Authorization result
        """
        provider = await self.get_payment_provider(restaurant_id, db)

        if provider == PaymentProvider.TOAST:
            return await self._authorize_with_toast(
                restaurant_id, amount_cents, card_number, expiry, cvv, guest_identifier, db
            )
        elif provider == PaymentProvider.STRIPE:
            return await self._authorize_with_stripe(
                restaurant_id, amount_cents, card_number, expiry, cvv, db
            )
        else:
            return {
                "success": False,
                "error": "No payment provider configured"
            }

    async def _authorize_with_toast(
        self,
        restaurant_id: int,
        amount_cents: int,
        card_number: str,
        expiry: str,
        cvv: str,
        guest_identifier: str,
        db: SupabaseDB
    ) -> Dict[str, Any]:
        """Authorize payment through Toast."""
        toast_config = await toast_service.get_restaurant_config(restaurant_id, db)

        if not toast_config:
            return {"success": False, "error": "Toast not configured"}

        # Encrypt card data (dev mode returns mock encryption)
        public_key = toast_config.get("public_key", "")
        if not public_key and not toast_config.get("dev_mode"):
            return {"success": False, "error": "Toast encryption key not configured"}

        encrypted_card = toast_service.encrypt_card_data(card_number, public_key or "dev_public_key")
        if not encrypted_card:
            return {"success": False, "error": "Failed to encrypt card data"}

        # Call Toast authorization
        result = await toast_service.authorize_payment(
            toast_config=toast_config,
            encrypted_card=encrypted_card,
            expiry=expiry,
            cvv=cvv,
            amount_cents=amount_cents,
            guest_identifier=guest_identifier
        )

        if result.get("success"):
            return {
                "success": True,
                "provider": PaymentProvider.TOAST.value,
                "payment_uuid": result.get("payment_uuid"),
                "card_last_four": result.get("card_last_four"),
                "card_type": result.get("card_type")
            }
        else:
            return {
                "success": False,
                "provider": PaymentProvider.TOAST.value,
                "error": result.get("error", "Payment declined")
            }

    async def _authorize_with_stripe(
        self,
        restaurant_id: int,
        amount_cents: int,
        card_number: str,
        expiry: str,
        cvv: str,
        db: SupabaseDB
    ) -> Dict[str, Any]:
        """Authorize payment through Stripe."""
        if not self.stripe_enabled:
            return {"success": False, "error": "Stripe not enabled"}

        account = db.query_one("restaurant_accounts", {"id": restaurant_id})
        if not account or not account.get("stripe_account_id"):
            return {"success": False, "error": "Stripe Connect not configured"}

        try:
            # Parse expiry
            exp_month = int(expiry[:2])
            exp_year = 2000 + int(expiry[2:])

            # Create payment method
            payment_method = stripe.PaymentMethod.create(
                type="card",
                card={
                    "number": card_number,
                    "exp_month": exp_month,
                    "exp_year": exp_year,
                    "cvc": cvv,
                },
            )

            # Calculate platform fee
            commission_rate = float(account.get("platform_commission_rate", 5))
            platform_fee = int(amount_cents * (commission_rate / 100))

            # Create payment intent with manual capture for authorization
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency="usd",
                payment_method=payment_method.id,
                confirm=True,
                capture_method="manual",  # Authorization only, capture later
                application_fee_amount=platform_fee,
                transfer_data={
                    "destination": account["stripe_account_id"]
                },
                metadata={
                    "restaurant_id": str(restaurant_id),
                    "collection_method": "dtmf"
                }
            )

            if payment_intent.status in ("requires_capture", "succeeded"):
                return {
                    "success": True,
                    "provider": PaymentProvider.STRIPE.value,
                    "payment_intent_id": payment_intent.id,
                    "card_last_four": payment_method.card.last4,
                    "card_type": payment_method.card.brand
                }
            else:
                return {
                    "success": False,
                    "provider": PaymentProvider.STRIPE.value,
                    "error": f"Payment failed: {payment_intent.status}"
                }

        except stripe.error.CardError as e:
            logger.error(f"Stripe card error: {e}")
            return {
                "success": False,
                "provider": PaymentProvider.STRIPE.value,
                "error": e.user_message or "Card declined"
            }
        except Exception as e:
            logger.error(f"Stripe payment error: {e}")
            return {
                "success": False,
                "provider": PaymentProvider.STRIPE.value,
                "error": "Payment processing failed"
            }

    async def apply_payment_to_order(
        self,
        order_id: int,
        session_id: int,
        db: SupabaseDB
    ) -> Dict[str, Any]:
        """
        Apply an authorized payment to an order.

        For Toast: applies payment to Toast order
        For Stripe: captures the payment intent

        Args:
            order_id: Local order ID
            session_id: Payment session ID
            db: Database instance

        Returns:
            Application result
        """
        session = db.query_one("payment_sessions", {"id": session_id})
        if not session:
            return {"success": False, "error": "Payment session not found"}

        order = db.query_one("orders", {"id": order_id})
        if not order:
            return {"success": False, "error": "Order not found"}

        provider = await self.get_payment_provider(session["restaurant_id"], db)

        if provider == PaymentProvider.TOAST and session.get("toast_payment_uuid"):
            return await self._apply_toast_payment(order, session, db)
        elif provider == PaymentProvider.STRIPE and session.get("stripe_payment_intent_id"):
            return await self._capture_stripe_payment(order, session, db)
        else:
            return {"success": False, "error": "No authorized payment to apply"}

    async def _apply_toast_payment(
        self,
        order: Dict[str, Any],
        session: Dict[str, Any],
        db: SupabaseDB
    ) -> Dict[str, Any]:
        """Apply Toast payment to order."""
        if not order.get("toast_order_guid"):
            return {"success": False, "error": "Order not synced to Toast"}

        toast_config = await toast_service.get_restaurant_config(
            session["restaurant_id"], db
        )

        if not toast_config:
            return {"success": False, "error": "Toast not configured"}

        result = await toast_service.apply_payment_to_order(
            toast_config=toast_config,
            order_guid=order["toast_order_guid"],
            payment_uuid=session["toast_payment_uuid"]
        )

        if result.get("success"):
            # Update order payment status
            db.update("orders", order["id"], {
                "payment_status": "paid",
                "toast_payment_uuid": session["toast_payment_uuid"]
            })

            # Mark session as completed
            db.update("payment_sessions", session["id"], {
                "status": "completed"
            })

            return {"success": True, "provider": "toast"}
        else:
            return result

    async def _capture_stripe_payment(
        self,
        order: Dict[str, Any],
        session: Dict[str, Any],
        db: SupabaseDB
    ) -> Dict[str, Any]:
        """Capture Stripe payment intent."""
        if not self.stripe_enabled:
            return {"success": False, "error": "Stripe not enabled"}

        try:
            payment_intent = stripe.PaymentIntent.capture(
                session["stripe_payment_intent_id"]
            )

            if payment_intent.status == "succeeded":
                # Update order payment status
                db.update("orders", order["id"], {
                    "payment_status": "paid",
                    "payment_intent_id": session["stripe_payment_intent_id"]
                })

                # Mark session as completed
                db.update("payment_sessions", session["id"], {
                    "status": "completed"
                })

                return {"success": True, "provider": "stripe"}
            else:
                return {"success": False, "error": f"Capture failed: {payment_intent.status}"}

        except Exception as e:
            logger.error(f"Stripe capture error: {e}")
            return {"success": False, "error": str(e)}

    def delete_payment_session(
        self,
        call_id: str,
        db: SupabaseDB
    ) -> bool:
        """Delete a payment session."""
        session = db.query_one("payment_sessions", {"call_id": call_id})
        if session:
            db.delete("payment_sessions", session["id"])
            logger.info(f"Deleted payment session for call {call_id}")
            return True
        return False


# Global service instance
payment_orchestrator = PaymentOrchestrator()
