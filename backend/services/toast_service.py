"""
Toast POS API Service.

Handles integration with Toast POS for order sync and payment processing.
Implements OAuth2 authentication, order creation, and payment authorization.

Supports DEV_MODE for testing without real Toast credentials.
"""

import os
import logging
import hashlib
import base64
import json
import time
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

from backend.database import SupabaseDB

logger = logging.getLogger(__name__)

# Dev mode flag - simulates Toast API responses for testing
TOAST_DEV_MODE = os.getenv("TOAST_DEV_MODE", "true").lower() == "true"


@dataclass
class CircuitBreakerState:
    """Tracks circuit breaker state for Toast API."""
    failures: int = 0
    last_failure: Optional[float] = None
    is_open: bool = False
    half_open_allowed: bool = True

    # Configuration
    failure_threshold: int = 5
    recovery_timeout: float = 60.0  # seconds


class ToastService:
    """
    Service for Toast POS API integration.

    Handles:
    - OAuth2 authentication
    - Order creation and pricing
    - Payment authorization and application
    - Circuit breaker for resilience
    """

    # Toast API endpoints
    BASE_URL = "https://ws-api.toasttab.com"
    AUTH_URL = "https://ws-api.toasttab.com/authentication/v1/authentication/login"

    # Token cache: {restaurant_id: (token, expiry_time)}
    _token_cache: Dict[int, tuple] = {}

    # Circuit breaker instance
    _circuit_breaker = CircuitBreakerState()

    def __init__(self):
        """Initialize Toast service."""
        # Toast API can be configured globally or per-restaurant
        self.global_client_id = os.getenv("TOAST_CLIENT_ID")
        self.global_client_secret = os.getenv("TOAST_CLIENT_SECRET")
        self.enabled = bool(self.global_client_id)
        self.dev_mode = TOAST_DEV_MODE

        if self.dev_mode:
            logger.info("Toast service initialized in DEV MODE - API calls will be simulated")
        elif self.enabled:
            logger.info("Toast service initialized with global credentials")
        else:
            logger.info("Toast service initialized - restaurant-specific credentials required")

    def _check_circuit_breaker(self) -> bool:
        """Check if circuit breaker allows request. Returns True if allowed."""
        cb = self._circuit_breaker

        if not cb.is_open:
            return True

        # Check if recovery timeout has passed
        if cb.last_failure and (time.time() - cb.last_failure) > cb.recovery_timeout:
            # Allow one request through (half-open state)
            if cb.half_open_allowed:
                cb.half_open_allowed = False
                logger.info("Circuit breaker half-open - allowing test request")
                return True

        logger.warning("Circuit breaker open - rejecting Toast API request")
        return False

    def _record_success(self) -> None:
        """Record successful API call - reset circuit breaker."""
        cb = self._circuit_breaker
        if cb.failures > 0 or cb.is_open:
            logger.info("Toast API success - resetting circuit breaker")
            cb.failures = 0
            cb.is_open = False
            cb.half_open_allowed = True
            cb.last_failure = None

    def _record_failure(self) -> None:
        """Record failed API call - potentially open circuit breaker."""
        cb = self._circuit_breaker
        cb.failures += 1
        cb.last_failure = time.time()
        cb.half_open_allowed = True

        if cb.failures >= cb.failure_threshold:
            cb.is_open = True
            logger.error(f"Circuit breaker opened after {cb.failures} failures")

    async def get_restaurant_config(
        self,
        restaurant_id: int,
        db: SupabaseDB
    ) -> Optional[Dict[str, Any]]:
        """
        Get Toast configuration for a restaurant.

        Args:
            restaurant_id: Restaurant account ID
            db: Database instance

        Returns:
            Toast config dict or None if not configured
        """
        account = db.query_one("restaurant_accounts", {"id": restaurant_id})

        if not account:
            return None

        if not account.get("toast_enabled"):
            return None

        # In dev mode, return mock config even without all fields
        if self.dev_mode:
            logger.info(f"[DEV MODE] Returning mock Toast config for restaurant {restaurant_id}")
            return {
                "restaurant_id": restaurant_id,
                "client_id": account.get("toast_client_id") or "dev_client_id",
                "client_secret_encrypted": "dev_secret",
                "restaurant_guid": account.get("toast_restaurant_guid") or f"dev-guid-{restaurant_id}",
                "encryption_key_id": "dev_key_id",
                "public_key": "dev_public_key",
                "dev_mode": True,
            }

        # Check required fields
        required_fields = ["toast_client_id", "toast_restaurant_guid"]
        missing = [f for f in required_fields if not account.get(f)]

        if missing:
            logger.warning(f"Restaurant {restaurant_id} missing Toast fields: {missing}")
            return None

        return {
            "restaurant_id": restaurant_id,
            "client_id": account.get("toast_client_id") or self.global_client_id,
            "client_secret_encrypted": account.get("toast_client_secret_encrypted"),
            "restaurant_guid": account["toast_restaurant_guid"],
            "encryption_key_id": account.get("toast_encryption_key_id"),
            "public_key": account.get("toast_public_key"),
        }

    def _decrypt_client_secret(self, encrypted_secret: str) -> str:
        """
        Decrypt the client secret.

        In production, this would use a KMS or secrets manager.
        For now, we assume it's stored with simple base64 encoding.
        """
        # TODO: Implement proper decryption using KMS
        # For now, assume base64 encoded
        try:
            return base64.b64decode(encrypted_secret).decode("utf-8")
        except Exception:
            # If not encoded, return as-is (development mode)
            return encrypted_secret

    async def get_access_token(
        self,
        toast_config: Dict[str, Any]
    ) -> Optional[str]:
        """
        Get OAuth2 access token for Toast API.

        Implements token caching with automatic refresh.

        Args:
            toast_config: Toast configuration dict

        Returns:
            Access token string or None if failed
        """
        restaurant_id = toast_config["restaurant_id"]

        # Dev mode - return mock token
        if self.dev_mode or toast_config.get("dev_mode"):
            logger.info(f"[DEV MODE] Returning mock access token for restaurant {restaurant_id}")
            return "dev_mode_mock_token"

        # Check cache
        if restaurant_id in self._token_cache:
            token, expiry = self._token_cache[restaurant_id]
            if time.time() < expiry - 60:  # 60 second buffer
                return token

        # Check circuit breaker
        if not self._check_circuit_breaker():
            return None

        # Get credentials
        client_id = toast_config["client_id"]
        client_secret = self._decrypt_client_secret(
            toast_config.get("client_secret_encrypted", "")
        )

        if not client_secret and self.global_client_secret:
            client_secret = self.global_client_secret

        if not client_secret:
            logger.error(f"No client secret available for restaurant {restaurant_id}")
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.AUTH_URL,
                    json={
                        "clientId": client_id,
                        "clientSecret": client_secret,
                        "userAccessType": "TOAST_MACHINE_CLIENT"
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()
                    token = data.get("token", {}).get("accessToken")
                    expires_in = data.get("token", {}).get("expiresIn", 3600)

                    if token:
                        # Cache token
                        self._token_cache[restaurant_id] = (token, time.time() + expires_in)
                        self._record_success()
                        logger.info(f"Got Toast access token for restaurant {restaurant_id}")
                        return token

                logger.error(f"Toast auth failed: {response.status_code} - {response.text}")
                self._record_failure()
                return None

        except Exception as e:
            logger.error(f"Toast auth error: {e}")
            self._record_failure()
            return None

    async def calculate_prices(
        self,
        order_data: Dict[str, Any],
        toast_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate prices for an order using Toast's pricing API.

        Toast requires calling /prices before /orders to get accurate pricing.

        Args:
            order_data: Order data with items
            toast_config: Toast configuration

        Returns:
            Pricing response with calculated totals
        """
        # Dev mode - return mock pricing
        if self.dev_mode or toast_config.get("dev_mode"):
            logger.info(f"[DEV MODE] Simulating Toast prices API call")
            logger.debug(f"[DEV MODE] Order data: {json.dumps(order_data, indent=2)}")
            return {
                "success": True,
                "data": {
                    "subtotal": 0,
                    "tax": 0,
                    "total": 0,
                    "dev_mode": True
                }
            }

        if not self._check_circuit_breaker():
            return {"success": False, "error": "Circuit breaker open"}

        token = await self.get_access_token(toast_config)
        if not token:
            return {"success": False, "error": "Failed to get access token"}

        restaurant_guid = toast_config["restaurant_guid"]
        url = f"{self.BASE_URL}/orders/v2/prices"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=order_data,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Toast-Restaurant-External-ID": restaurant_guid,
                        "Content-Type": "application/json"
                    },
                    timeout=15.0
                )

                if response.status_code == 200:
                    self._record_success()
                    return {"success": True, "data": response.json()}
                else:
                    logger.error(f"Toast prices failed: {response.status_code} - {response.text}")
                    self._record_failure()
                    return {"success": False, "error": f"API error: {response.status_code}"}

        except Exception as e:
            logger.error(f"Toast prices error: {e}")
            self._record_failure()
            return {"success": False, "error": str(e)}

    async def create_order(
        self,
        order_data: Dict[str, Any],
        toast_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create an order in Toast POS.

        Args:
            order_data: Order data including items, customer info
            toast_config: Toast configuration

        Returns:
            Order creation response with GUID
        """
        # Dev mode - return mock order GUID
        if self.dev_mode or toast_config.get("dev_mode"):
            mock_guid = f"dev-order-{uuid.uuid4().hex[:12]}"
            logger.info(f"[DEV MODE] Simulating Toast order creation - GUID: {mock_guid}")
            logger.info(f"[DEV MODE] Order would be sent to Toast KDS with data:")
            logger.info(f"[DEV MODE]   Customer: {order_data.get('customer', {})}")
            logger.info(f"[DEV MODE]   Items: {len(order_data.get('checks', [{}])[0].get('selections', []))} items")
            return {
                "success": True,
                "guid": mock_guid,
                "data": {
                    "guid": mock_guid,
                    "status": "OPEN",
                    "dev_mode": True
                }
            }

        if not self._check_circuit_breaker():
            return {"success": False, "error": "Circuit breaker open"}

        token = await self.get_access_token(toast_config)
        if not token:
            return {"success": False, "error": "Failed to get access token"}

        restaurant_guid = toast_config["restaurant_guid"]
        url = f"{self.BASE_URL}/orders/v2/orders"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=order_data,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Toast-Restaurant-External-ID": restaurant_guid,
                        "Content-Type": "application/json"
                    },
                    timeout=15.0
                )

                if response.status_code in (200, 201):
                    data = response.json()
                    self._record_success()
                    return {
                        "success": True,
                        "guid": data.get("guid"),
                        "data": data
                    }
                else:
                    logger.error(f"Toast order create failed: {response.status_code} - {response.text}")
                    self._record_failure()
                    return {"success": False, "error": f"API error: {response.status_code}"}

        except Exception as e:
            logger.error(f"Toast order create error: {e}")
            self._record_failure()
            return {"success": False, "error": str(e)}

    def encrypt_card_data(
        self,
        card_number: str,
        public_key_pem: str
    ) -> Optional[str]:
        """
        Encrypt card number using Toast's public key.

        Uses RSA OAEP encryption as required by Toast's payment API.

        Args:
            card_number: Plain card number
            public_key_pem: Toast's public key in PEM format

        Returns:
            Base64-encoded encrypted card data
        """
        # Dev mode - return mock encrypted data
        if self.dev_mode or public_key_pem == "dev_public_key":
            last_four = card_number[-4:] if len(card_number) >= 4 else card_number
            logger.info(f"[DEV MODE] Simulating card encryption for card ending in {last_four}")
            return f"dev_encrypted_{last_four}"

        try:
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode(),
                backend=default_backend()
            )

            encrypted = public_key.encrypt(
                card_number.encode(),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            return base64.b64encode(encrypted).decode()

        except Exception as e:
            logger.error(f"Card encryption error: {e}")
            return None

    async def authorize_payment(
        self,
        toast_config: Dict[str, Any],
        encrypted_card: str,
        expiry: str,
        cvv: str,
        amount_cents: int,
        guest_identifier: str
    ) -> Dict[str, Any]:
        """
        Authorize a card payment through Toast.

        Creates a payment authorization that can be applied to an order
        within a 5-minute window.

        Args:
            toast_config: Toast configuration
            encrypted_card: RSA-encrypted card number
            expiry: Card expiry in MMYY format
            cvv: Card CVV
            amount_cents: Amount to authorize in cents
            guest_identifier: Unique identifier for this guest/transaction

        Returns:
            Authorization response with payment UUID
        """
        # Dev mode - simulate authorization
        if self.dev_mode or toast_config.get("dev_mode"):
            mock_payment_uuid = f"dev-payment-{uuid.uuid4().hex[:12]}"
            # Extract last 4 from encrypted card (dev mode format is dev_encrypted_XXXX)
            last_four = encrypted_card[-4:] if encrypted_card.startswith("dev_encrypted_") else "0000"

            logger.info(f"[DEV MODE] Simulating Toast payment authorization")
            logger.info(f"[DEV MODE]   Amount: ${amount_cents / 100:.2f}")
            logger.info(f"[DEV MODE]   Card ending: {last_four}")
            logger.info(f"[DEV MODE]   Payment UUID: {mock_payment_uuid}")

            return {
                "success": True,
                "payment_uuid": mock_payment_uuid,
                "card_last_four": last_four,
                "card_type": "VISA",
                "data": {
                    "status": "AUTHORIZED",
                    "paymentUuid": mock_payment_uuid,
                    "dev_mode": True
                }
            }

        if not self._check_circuit_breaker():
            return {"success": False, "error": "Circuit breaker open"}

        token = await self.get_access_token(toast_config)
        if not token:
            return {"success": False, "error": "Failed to get access token"}

        restaurant_guid = toast_config["restaurant_guid"]
        key_id = toast_config.get("encryption_key_id", "")

        url = f"{self.BASE_URL}/payments/v1/preAuthorize"

        # Parse expiry (MMYY -> MM/YY)
        exp_month = expiry[:2]
        exp_year = expiry[2:]

        payload = {
            "restaurantGuid": restaurant_guid,
            "amount": amount_cents / 100,  # Toast expects dollars
            "guestIdentifier": guest_identifier,
            "cardData": {
                "encryptedCardNumber": encrypted_card,
                "encryptionKeyId": key_id,
                "expirationMonth": exp_month,
                "expirationYear": f"20{exp_year}",
                "cvv": cvv
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Toast-Restaurant-External-ID": restaurant_guid,
                        "Content-Type": "application/json"
                    },
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    self._record_success()

                    if data.get("status") == "AUTHORIZED":
                        return {
                            "success": True,
                            "payment_uuid": data.get("paymentUuid"),
                            "card_last_four": data.get("lastFour"),
                            "card_type": data.get("cardType"),
                            "data": data
                        }
                    else:
                        return {
                            "success": False,
                            "error": data.get("message", "Payment declined"),
                            "decline_reason": data.get("declineReason")
                        }
                else:
                    logger.error(f"Toast payment auth failed: {response.status_code} - {response.text}")
                    self._record_failure()
                    return {"success": False, "error": f"API error: {response.status_code}"}

        except Exception as e:
            logger.error(f"Toast payment auth error: {e}")
            self._record_failure()
            return {"success": False, "error": str(e)}

    async def apply_payment_to_order(
        self,
        toast_config: Dict[str, Any],
        order_guid: str,
        payment_uuid: str,
        tip_amount: float = 0
    ) -> Dict[str, Any]:
        """
        Apply a pre-authorized payment to an order.

        Must be called within 5 minutes of authorization.

        Args:
            toast_config: Toast configuration
            order_guid: Toast order GUID
            payment_uuid: Pre-authorization payment UUID
            tip_amount: Optional tip amount in dollars

        Returns:
            Payment application response
        """
        # Dev mode - simulate payment application
        if self.dev_mode or toast_config.get("dev_mode"):
            logger.info(f"[DEV MODE] Simulating Toast payment application")
            logger.info(f"[DEV MODE]   Order GUID: {order_guid}")
            logger.info(f"[DEV MODE]   Payment UUID: {payment_uuid}")
            logger.info(f"[DEV MODE]   Tip: ${tip_amount:.2f}")
            return {
                "success": True,
                "data": {
                    "status": "CAPTURED",
                    "dev_mode": True
                }
            }

        if not self._check_circuit_breaker():
            return {"success": False, "error": "Circuit breaker open"}

        token = await self.get_access_token(toast_config)
        if not token:
            return {"success": False, "error": "Failed to get access token"}

        restaurant_guid = toast_config["restaurant_guid"]
        url = f"{self.BASE_URL}/orders/v2/orders/{order_guid}/payments"

        payload = {
            "paymentUuid": payment_uuid,
            "tipAmount": tip_amount
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Toast-Restaurant-External-ID": restaurant_guid,
                        "Content-Type": "application/json"
                    },
                    timeout=15.0
                )

                if response.status_code in (200, 201):
                    self._record_success()
                    return {"success": True, "data": response.json()}
                else:
                    logger.error(f"Toast apply payment failed: {response.status_code} - {response.text}")
                    self._record_failure()
                    return {"success": False, "error": f"API error: {response.status_code}"}

        except Exception as e:
            logger.error(f"Toast apply payment error: {e}")
            self._record_failure()
            return {"success": False, "error": str(e)}

    async def void_payment(
        self,
        toast_config: Dict[str, Any],
        payment_uuid: str
    ) -> Dict[str, Any]:
        """
        Void a pre-authorized payment that wasn't applied.

        Args:
            toast_config: Toast configuration
            payment_uuid: Payment UUID to void

        Returns:
            Void response
        """
        if not self._check_circuit_breaker():
            return {"success": False, "error": "Circuit breaker open"}

        token = await self.get_access_token(toast_config)
        if not token:
            return {"success": False, "error": "Failed to get access token"}

        restaurant_guid = toast_config["restaurant_guid"]
        url = f"{self.BASE_URL}/payments/v1/void/{payment_uuid}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Toast-Restaurant-External-ID": restaurant_guid,
                    },
                    timeout=15.0
                )

                if response.status_code == 200:
                    self._record_success()
                    return {"success": True}
                else:
                    logger.error(f"Toast void payment failed: {response.status_code}")
                    self._record_failure()
                    return {"success": False, "error": f"API error: {response.status_code}"}

        except Exception as e:
            logger.error(f"Toast void payment error: {e}")
            self._record_failure()
            return {"success": False, "error": str(e)}

    def build_toast_order(
        self,
        items: List[Dict[str, Any]],
        customer_name: str,
        customer_phone: str,
        scheduled_time: Optional[datetime],
        menu_item_mappings: Dict[str, str],
        restaurant_guid: str
    ) -> Dict[str, Any]:
        """
        Build a Toast-compatible order payload.

        Args:
            items: List of cart items
            customer_name: Customer name
            customer_phone: Customer phone
            scheduled_time: Pickup time
            menu_item_mappings: Map of item names to Toast GUIDs
            restaurant_guid: Toast restaurant GUID

        Returns:
            Toast order payload
        """
        # Build order selections
        selections = []
        for item in items:
            item_name = item.get("name", "")
            toast_guid = menu_item_mappings.get(item_name)

            if not toast_guid:
                logger.warning(f"No Toast mapping for item: {item_name}")
                continue

            selection = {
                "itemGuid": toast_guid,
                "quantity": item.get("quantity", 1),
                "selectionType": "NONE"
            }

            # Add special requests as modifier notes
            if item.get("special_requests"):
                selection["specialRequest"] = item["special_requests"]

            selections.append(selection)

        # Build order payload
        order = {
            "restaurantGuid": restaurant_guid,
            "orderSource": {
                "name": "VoiceAI",
                "guid": "voice-ai-source"
            },
            "diningOption": {
                "behavior": "TAKE_OUT"
            },
            "customer": {
                "firstName": customer_name.split()[0] if customer_name else "",
                "lastName": " ".join(customer_name.split()[1:]) if customer_name and len(customer_name.split()) > 1 else "",
                "phone": customer_phone
            },
            "checks": [{
                "selections": selections
            }]
        }

        # Add scheduled time if provided
        if scheduled_time:
            order["promisedDate"] = scheduled_time.isoformat()

        return order


# Global service instance
toast_service = ToastService()
