"""
Voice call handling service using Twilio Voice API.

This service handles incoming phone calls, converts speech to text,
processes booking requests, and responds with text-to-speech.
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, time, date
from twilio.twiml.voice_response import VoiceResponse, Gather

logger = logging.getLogger(__name__)


class VoiceService:
    """Service for handling voice calls via Twilio."""

    def __init__(self):
        """Initialize voice service."""
        self.enabled = bool(os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN"))
        if not self.enabled:
            logger.warning("Voice service disabled - Twilio credentials not configured")

    def create_welcome_response(self, restaurant_name: str = "our restaurant") -> VoiceResponse:
        """
        Create initial welcome message when call is received.

        Args:
            restaurant_name: Name of the restaurant to include in greeting

        Returns:
            VoiceResponse with welcome message and speech gathering
        """
        response = VoiceResponse()

        gather = Gather(
            input='speech',
            action='/api/voice/process',
            method='POST',
            timeout=3,
            speech_timeout='auto',
            language='en-US'
        )

        gather.say(
            f"Thank you for calling {restaurant_name}! "
            "I'm your AI assistant. How can I help you today? "
            "You can ask about our menu, place an order, or make a reservation.",
            voice='alice',
            language='en-US'
        )

        response.append(gather)

        # If no input, redirect
        response.redirect('/api/voice/welcome')

        return response

    def create_error_response(self, message: str = "I'm sorry, I didn't understand that.") -> VoiceResponse:
        """
        Create error response.

        Args:
            message: Error message to speak

        Returns:
            VoiceResponse with error message
        """
        response = VoiceResponse()
        response.say(message, voice='alice', language='en-US')
        response.redirect('/api/voice/welcome')
        return response

    def create_gather_response(
        self,
        prompt: str,
        action: str = '/api/voice/process',
        timeout: int = 3
    ) -> VoiceResponse:
        """
        Create response that gathers speech input.

        Args:
            prompt: What to say to the user
            action: Webhook URL to send speech result
            timeout: Timeout in seconds

        Returns:
            VoiceResponse with gather
        """
        response = VoiceResponse()

        gather = Gather(
            input='speech',
            action=action,
            method='POST',
            timeout=timeout,
            speech_timeout='auto',
            language='en-US'
        )

        gather.say(prompt, voice='alice', language='en-US')
        response.append(gather)
        response.redirect('/api/voice/welcome')

        return response

    def create_confirmation_response(
        self,
        restaurant_name: str,
        booking_date: date,
        booking_time: time,
        party_size: int,
        customer_name: str,
        confirmation_id: int
    ) -> VoiceResponse:
        """
        Create booking confirmation response.

        Args:
            restaurant_name: Name of restaurant
            booking_date: Date of booking
            booking_time: Time of booking
            party_size: Number of guests
            customer_name: Customer name
            confirmation_id: Booking confirmation ID

        Returns:
            VoiceResponse with confirmation message
        """
        response = VoiceResponse()

        # Format date and time for speech
        formatted_date = booking_date.strftime('%A, %B %d')
        formatted_time = booking_time.strftime('%I:%M %p')

        message = (
            f"Great! Your reservation at {restaurant_name} has been confirmed. "
            f"Party of {party_size} on {formatted_date} at {formatted_time}. "
            f"Your confirmation number is {confirmation_id}. "
            f"A text message with the details has been sent to your phone. "
            f"Is there anything else I can help you with?"
        )

        response.say(message, voice='alice', language='en-US')

        # Give them option to do more or hang up
        gather = Gather(
            input='speech',
            action='/api/voice/process',
            method='POST',
            timeout=3,
            speech_timeout='auto',
            language='en-US'
        )
        gather.say("Say yes for more assistance, or no to end the call.", voice='alice', language='en-US')
        response.append(gather)

        # If no response, say goodbye
        response.say("Thank you for calling. Goodbye!", voice='alice', language='en-US')
        response.hangup()

        return response

    def create_availability_response(
        self,
        available_times: list,
        requested_date: date,
        party_size: int
    ) -> VoiceResponse:
        """
        Create availability check response.

        Args:
            available_times: List of available time slots
            requested_date: Requested date
            party_size: Number of guests

        Returns:
            VoiceResponse with availability information
        """
        response = VoiceResponse()

        formatted_date = requested_date.strftime('%A, %B %d')

        if not available_times:
            message = (
                f"I'm sorry, we don't have availability for {party_size} guests "
                f"on {formatted_date}. Would you like to check a different date?"
            )
        else:
            # Format times for speech
            times_str = ', '.join([t.strftime('%I:%M %p') for t in available_times[:3]])
            message = (
                f"We have availability for {party_size} guests on {formatted_date} "
                f"at the following times: {times_str}. "
                f"Would you like to make a reservation for one of these times?"
            )

        response.say(message, voice='alice', language='en-US')

        gather = Gather(
            input='speech',
            action='/api/voice/process',
            method='POST',
            timeout=3,
            speech_timeout='auto',
            language='en-US'
        )
        gather.say("Please tell me your choice.", voice='alice', language='en-US')
        response.append(gather)

        response.redirect('/api/voice/welcome')

        return response

    def create_goodbye_response(self) -> VoiceResponse:
        """
        Create goodbye response.

        Returns:
            VoiceResponse with goodbye message
        """
        response = VoiceResponse()
        response.say(
            "Thank you for calling. We look forward to seeing you soon. Goodbye!",
            voice='alice',
            language='en-US'
        )
        response.hangup()
        return response


# Global voice service instance
voice_service = VoiceService()
