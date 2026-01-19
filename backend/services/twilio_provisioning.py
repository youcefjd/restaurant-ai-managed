"""
Twilio phone number provisioning service.

Handles automatic provisioning of Twilio phone numbers for new restaurant accounts.
"""

import os
import logging
from typing import Optional, List, Dict, Any
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from backend.core.logging import setup_logging

logger = setup_logging(__name__)


class TwilioProvisioningService:
    """Service for provisioning Twilio phone numbers for restaurants."""

    def __init__(self):
        """Initialize Twilio client."""
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.webhook_base_url = os.getenv("PUBLIC_WS_URL", "").replace("wss://", "https://").replace("ws://", "http://")

        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
            self.enabled = True
            logger.info("Twilio provisioning service initialized")
        else:
            self.client = None
            self.enabled = False
            logger.warning("Twilio credentials not found - provisioning service disabled")

    def search_available_numbers(
        self,
        country: str = "US",
        area_code: Optional[str] = None,
        contains: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for available phone numbers.

        Args:
            country: Country code (default: US)
            area_code: Optional area code filter
            contains: Optional pattern to search for
            limit: Max numbers to return

        Returns:
            List of available phone numbers with details
        """
        if not self.enabled:
            logger.warning("Twilio not enabled - cannot search numbers")
            return []

        try:
            search_params = {
                "voice_enabled": True,
                "sms_enabled": True,
                "limit": limit
            }

            if area_code:
                search_params["area_code"] = area_code
            if contains:
                search_params["contains"] = contains

            available_numbers = self.client.available_phone_numbers(country).local.list(**search_params)

            return [
                {
                    "phone_number": num.phone_number,
                    "friendly_name": num.friendly_name,
                    "locality": num.locality,
                    "region": num.region,
                    "postal_code": num.postal_code,
                    "capabilities": {
                        "voice": num.capabilities.get("voice", False),
                        "sms": num.capabilities.get("sms", False),
                    }
                }
                for num in available_numbers
            ]

        except TwilioRestException as e:
            logger.error(f"Twilio API error searching numbers: {e}")
            return []
        except Exception as e:
            logger.error(f"Error searching available numbers: {e}")
            return []

    def provision_number(
        self,
        phone_number: Optional[str] = None,
        country: str = "US",
        area_code: Optional[str] = None,
        friendly_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Provision a new phone number.

        If phone_number is provided, purchase that specific number.
        Otherwise, search for and purchase the first available number.

        Args:
            phone_number: Specific number to purchase (E.164 format)
            country: Country code for search (default: US)
            area_code: Area code preference for search
            friendly_name: Friendly name for the number

        Returns:
            The provisioned phone number in E.164 format, or None if failed
        """
        if not self.enabled:
            logger.warning("Twilio not enabled - cannot provision number")
            return None

        try:
            # If no specific number provided, search for one
            if not phone_number:
                available = self.search_available_numbers(
                    country=country,
                    area_code=area_code,
                    limit=1
                )
                if not available:
                    logger.error("No available phone numbers found")
                    return None
                phone_number = available[0]["phone_number"]

            # Configure webhooks for voice
            voice_url = f"{self.webhook_base_url}/api/voice/incoming" if self.webhook_base_url else None
            status_callback = f"{self.webhook_base_url}/api/voice/status" if self.webhook_base_url else None

            # Purchase the number
            purchase_params = {
                "phone_number": phone_number,
            }

            if friendly_name:
                purchase_params["friendly_name"] = friendly_name

            if voice_url:
                purchase_params["voice_url"] = voice_url
                purchase_params["voice_method"] = "POST"

            if status_callback:
                purchase_params["status_callback"] = status_callback
                purchase_params["status_callback_method"] = "POST"

            incoming_number = self.client.incoming_phone_numbers.create(**purchase_params)

            logger.info(f"Provisioned phone number: {incoming_number.phone_number}")
            return incoming_number.phone_number

        except TwilioRestException as e:
            logger.error(f"Twilio API error provisioning number: {e}")
            return None
        except Exception as e:
            logger.error(f"Error provisioning phone number: {e}")
            return None

    def configure_number_webhooks(self, phone_number: str, base_url: str) -> bool:
        """
        Configure webhooks for an existing phone number.

        Args:
            phone_number: The phone number to configure
            base_url: Base URL for webhooks (https://yourdomain.com)

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            # Find the phone number SID
            numbers = self.client.incoming_phone_numbers.list(phone_number=phone_number)
            if not numbers:
                logger.error(f"Phone number not found: {phone_number}")
                return False

            number_sid = numbers[0].sid

            # Update the webhooks
            self.client.incoming_phone_numbers(number_sid).update(
                voice_url=f"{base_url}/api/voice/incoming",
                voice_method="POST",
                status_callback=f"{base_url}/api/voice/status",
                status_callback_method="POST"
            )

            logger.info(f"Configured webhooks for {phone_number}")
            return True

        except TwilioRestException as e:
            logger.error(f"Twilio API error configuring webhooks: {e}")
            return False
        except Exception as e:
            logger.error(f"Error configuring webhooks: {e}")
            return False

    def release_number(self, phone_number: str) -> bool:
        """
        Release (cancel) a phone number.

        Args:
            phone_number: The phone number to release

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            numbers = self.client.incoming_phone_numbers.list(phone_number=phone_number)
            if not numbers:
                logger.warning(f"Phone number not found for release: {phone_number}")
                return True  # Already released

            self.client.incoming_phone_numbers(numbers[0].sid).delete()
            logger.info(f"Released phone number: {phone_number}")
            return True

        except TwilioRestException as e:
            logger.error(f"Twilio API error releasing number: {e}")
            return False
        except Exception as e:
            logger.error(f"Error releasing phone number: {e}")
            return False

    def is_enabled(self) -> bool:
        """Check if provisioning service is enabled."""
        return self.enabled


# Global service instance
twilio_provisioning = TwilioProvisioningService()
