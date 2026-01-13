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
        """Initialize Twilio client."""
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")

        # Initialize Twilio client if credentials are provided
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
            self.enabled = True
            logger.info("Twilio SMS service initialized")
        else:
            self.client = None
            self.enabled = False
            logger.warning("Twilio credentials not found - SMS service disabled")

    def send_sms(self, to: str, message: str) -> Optional[str]:
        """
        Send an SMS message.

        Args:
            to: Phone number to send to (E.164 format)
            message: Message content

        Returns:
            Message SID if successful, None otherwise
        """
        if not self.enabled:
            logger.warning(f"SMS disabled - would have sent to {to}: {message}")
            return None

        try:
            message_obj = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=to
            )
            logger.info(f"SMS sent to {to}, SID: {message_obj.sid}")
            return message_obj.sid
        except Exception as e:
            logger.error(f"Failed to send SMS to {to}: {str(e)}")
            return None

    def send_booking_confirmation(
        self,
        booking: Booking,
        customer: Customer,
        restaurant: Restaurant
    ) -> Optional[str]:
        """
        Send booking confirmation SMS.

        Args:
            booking: Booking object
            customer: Customer object
            restaurant: Restaurant object

        Returns:
            Message SID if successful, None otherwise
        """
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

        return self.send_sms(customer.phone, message)

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

        return self.send_sms(customer.phone, message)

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

        return self.send_sms(customer.phone, message)

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

        return self.send_sms(customer.phone, message)

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
