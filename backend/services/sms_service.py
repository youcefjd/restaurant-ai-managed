"""SMS service using Twilio for sending booking notifications."""

import os
from typing import Optional
from datetime import datetime
from twilio.rest import Client
from backend.models import Booking, Customer, Restaurant
from backend.core.logging import setup_logging

logger = setup_logging(__name__)


class SMSService:
    """Service for sending SMS notifications via Twilio."""

    def __init__(self):
        """
        Initialize Twilio client.
        
        Note: TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN are required for the platform
        to make Twilio API calls (send SMS, handle webhooks).
        
        Each restaurant must have their own phone number set in the database.
        No fallback phone number is used.
        """
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")

        # Initialize Twilio client if credentials are provided
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
            self.enabled = True
            logger.info("Twilio SMS service initialized")
        else:
            self.client = None
            self.enabled = False
            logger.warning("Twilio credentials not found - SMS service disabled")

    def send_sms(self, to: str, message: str, from_number: str) -> Optional[str]:
        """
        Send an SMS message.

        Args:
            to: Phone number to send to (E.164 format)
            message: Message content
            from_number: Phone number to send from (REQUIRED - must be restaurant's Twilio number)

        Returns:
            Message SID if successful, None otherwise
        """
        if not self.enabled:
            logger.warning(f"SMS disabled - would have sent to {to}: {message}")
            return None

        if not from_number:
            logger.error("No 'from' phone number provided - SMS requires restaurant's Twilio phone number")
            return None

        try:
            message_obj = self.client.messages.create(
                body=message,
                from_=from_number,
                to=to
            )
            logger.info(f"SMS sent to {to} from {from_number}, SID: {message_obj.sid}")
            return message_obj.sid
        except Exception as e:
            logger.error(f"Failed to send SMS to {to}: {str(e)}")
            return None

    def send_booking_confirmation(
        self,
        booking: Booking,
        customer: Customer,
        restaurant: Restaurant,
        from_number: Optional[str] = None
    ) -> Optional[str]:
        """
        Send booking confirmation SMS.

        Args:
            booking: Booking object
            customer: Customer object
            restaurant: Restaurant object
            from_number: Restaurant's Twilio phone number (required)

        Returns:
            Message SID if successful, None otherwise
        """
        # Get restaurant's Twilio phone number
        if not from_number:
            if hasattr(restaurant, 'account') and restaurant.account:
                from_number = restaurant.account.twilio_phone_number
        
        if not from_number:
            logger.warning(f"Cannot send booking confirmation SMS - restaurant {restaurant.id} has no Twilio phone number configured")
            return None

        message = f"""
🎉 Booking Confirmed!

Restaurant: {restaurant.name}
Date: {booking.booking_date.strftime('%B %d, %Y')}
Time: {booking.booking_time.strftime('%I:%M %p')}
Party Size: {booking.party_size} guests
Duration: {booking.duration_minutes} minutes

Confirmation #: {booking.id}

{restaurant.address}
{restaurant.phone}

See you soon! Reply CANCEL to cancel your booking.
        """.strip()

        return self.send_sms(customer.phone, message, from_number=from_number)

    def send_booking_reminder(
        self,
        booking: Booking,
        customer: Customer,
        restaurant: Restaurant,
        hours_before: int = 24
    ) -> Optional[str]:
        """
        Send booking reminder SMS.

        Args:
            booking: Booking object
            customer: Customer object
            restaurant: Restaurant object
            hours_before: How many hours before the booking

        Returns:
            Message SID if successful, None otherwise
        """
        message = f"""
⏰ Reminder: Your reservation is in {hours_before} hours!

{restaurant.name}
Date: {booking.booking_date.strftime('%B %d, %Y')}
Time: {booking.booking_time.strftime('%I:%M %p')}
Party Size: {booking.party_size} guests

Confirmation #: {booking.id}

Reply CONFIRM if you're coming or CANCEL to cancel.
        """.strip()

        # Get restaurant's Twilio phone number
        from_number = None
        if hasattr(restaurant, 'account') and restaurant.account:
            from_number = restaurant.account.twilio_phone_number
        
        if not from_number:
            logger.warning(f"Cannot send reminder SMS - restaurant {restaurant.id} has no Twilio phone number configured")
            return None
        
        return self.send_sms(customer.phone, message, from_number=from_number)

    def send_cancellation_confirmation(
        self,
        booking: Booking,
        customer: Customer,
        restaurant: Restaurant
    ) -> Optional[str]:
        """
        Send booking cancellation confirmation SMS.

        Args:
            booking: Booking object
            customer: Customer object
            restaurant: Restaurant object

        Returns:
            Message SID if successful, None otherwise
        """
        message = f"""
❌ Booking Cancelled

Your reservation at {restaurant.name} has been cancelled.

Original Details:
Date: {booking.booking_date.strftime('%B %d, %Y')}
Time: {booking.booking_time.strftime('%I:%M %p')}

Confirmation #: {booking.id}

We hope to see you another time! To make a new reservation, visit our website.
        """.strip()

        # Get restaurant's Twilio phone number
        from_number = None
        if hasattr(restaurant, 'account') and restaurant.account:
            from_number = restaurant.account.twilio_phone_number
        
        if not from_number:
            logger.warning(f"Cannot send cancellation SMS - restaurant {restaurant.id} has no Twilio phone number configured")
            return None
        
        return self.send_sms(customer.phone, message, from_number=from_number)

    def send_booking_update(
        self,
        booking: Booking,
        customer: Customer,
        restaurant: Restaurant,
        changes: str
    ) -> Optional[str]:
        """
        Send booking update notification SMS.

        Args:
            booking: Updated booking object
            customer: Customer object
            restaurant: Restaurant object
            changes: Description of what changed

        Returns:
            Message SID if successful, None otherwise
        """
        message = f"""
🔄 Booking Updated

{restaurant.name}
Confirmation #: {booking.id}

Changes: {changes}

New Details:
Date: {booking.booking_date.strftime('%B %d, %Y')}
Time: {booking.booking_time.strftime('%I:%M %p')}
Party Size: {booking.party_size} guests

Reply CONFIRM to acknowledge.
        """.strip()

        # Get restaurant's Twilio phone number
        from_number = None
        if hasattr(restaurant, 'account') and restaurant.account:
            from_number = restaurant.account.twilio_phone_number
        
        if not from_number:
            logger.warning(f"Cannot send booking update SMS - restaurant {restaurant.id} has no Twilio phone number configured")
            return None
        
        return self.send_sms(customer.phone, message, from_number=from_number)

    def create_twiml_response(self, message: str) -> str:
        """
        Create TwiML response for replying to incoming SMS.

        Args:
            message: Text message to send back

        Returns:
            TwiML XML string
        """
        from twilio.twiml.messaging_response import MessagingResponse

        response = MessagingResponse()
        response.message(message)
        return str(response)


# Global SMS service instance
sms_service = SMSService()
