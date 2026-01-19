"""
Voice call webhook endpoints for Twilio Voice API with Retell AI integration.

Simplified implementation using Retell AI for voice processing (ASR, LLM, TTS).
Retell handles all voice processing - we just route calls to Retell agents.
"""

import os
import logging
from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import Response
from sqlalchemy.orm import Session
from twilio.twiml.voice_response import VoiceResponse, Dial, Say

from backend.database import get_db
from backend.models_platform import RestaurantAccount
from backend.services.sms_service import sms_service
from backend.services.conversation_handler import conversation_handler
from backend.services.transcript_service import transcript_service

router = APIRouter()
logger = logging.getLogger(__name__)

# SMS conversation state (still needed for SMS handling)
sms_conversation_state: Dict[str, Dict[str, Any]] = {}


def normalize_phone(phone: str) -> str:
    """Normalize phone number to E.164 format."""
    if not phone:
        return ""
    phone = phone.strip()
    if not phone.startswith('+'):
        phone = '+' + phone
    return phone


@router.post("/welcome")
@router.get("/welcome")
async def voice_welcome(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Initial webhook when call is received.
    Routes call to Retell AI agent for voice processing.
    
    Handles both POST (form data) and GET (query params) for Twilio compatibility.
    """
    # Extract parameters from either form data (POST) or query params (GET)
    if request.method == "POST":
        form_data = await request.form()
        To = form_data.get("To")
        From = form_data.get("From")
        CallSid = form_data.get("CallSid")
    else:  # GET
        To = request.query_params.get("To")
        From = request.query_params.get("From")
        CallSid = request.query_params.get("CallSid")
    
    logger.info(f"Voice call received from {From} to {To}, CallSid: {CallSid}")

    # Normalize phone number
    to_normalized = normalize_phone(To) if To else None

    # Look up which restaurant owns this Twilio number
    restaurant = db.query(RestaurantAccount).filter(
        RestaurantAccount.twilio_phone_number == to_normalized
    ).first()
    
    if not restaurant:
        logger.warning(f"No restaurant found for Twilio number {To}")
        response = VoiceResponse()
        response.say(
            "This number is not configured. Please contact support.",
            voice='alice',
            language='en-US'
        )
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    # Check if Retell agent is configured
    retell_agent_id = restaurant.retell_agent_id
    retell_api_key = os.getenv("RETELL_API_KEY")
    
    if not retell_agent_id or not retell_api_key:
        logger.warning(f"Retell not configured for restaurant {restaurant.id}")
        # Send SMS fallback
        try:
            sms_message = (
                f"Sorry, we're not currently handling voice orders. "
                f"Please text us your order or call back later. "
                f"You can also visit our website. - {restaurant.business_name}"
            )
            sms_service.send_sms(
                to=From or "",
                message=sms_message,
                from_number=restaurant.twilio_phone_number
            )
        except Exception as e:
            logger.error(f"Failed to send SMS fallback: {str(e)}")
        
        # Return error TwiML
        response = VoiceResponse()
        response.say(
            "Sorry, we're not currently handling voice orders. "
            "Please text us your order or call back later. Thank you.",
            voice='alice',
            language='en-US'
        )
        response.hangup()
        return Response(content=str(response), media_type="application/xml")

    # Route call to Retell AI
    # Retell provides a webhook URL that handles the voice connection
    # Format: https://api.retellai.com/voice/{agent_id}
    # OR use Retell's phone number if configured
    
    response = VoiceResponse()
    
    # Option 1: Connect to Retell via webhook URL (recommended)
    # Retell will handle the voice processing and call our custom functions webhook
    retell_webhook_url = f"https://api.retellai.com/voice/{retell_agent_id}"
    
    # Option 2: If Retell provides a phone number, use Dial:
    # dial = Dial(retell_phone_number)
    # response.append(dial)
    
    # For now, we'll redirect to Retell's webhook
    # Note: Retell's actual integration may vary - consult Retell docs for exact URL format
    # This is a placeholder that should be updated based on Retell's API documentation
    response.redirect(retell_webhook_url)
    
    logger.info(f"Routing call {CallSid} to Retell agent {retell_agent_id} for restaurant {restaurant.id}")
    
    return Response(content=str(response), media_type="application/xml")


@router.post("/status")
async def voice_status(
    CallSid: str = Form(None),
    CallStatus: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Handle call status updates from Twilio.
    
    This can be used to track call duration, status changes, etc.
    Retell may also send webhooks for call events.
    """
    logger.info(f"Call status update: CallSid={CallSid}, Status={CallStatus}")
    
    # Log call completion, save transcripts if needed, etc.
    # Retell may handle transcripts separately via their webhooks
    
    return {"status": "ok"}


@router.post("/sms/incoming")
async def sms_incoming(
    From: str = Form(None),
    To: str = Form(None),
    Body: str = Form(None),
    MessageSid: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Handle incoming SMS messages.

    Args:
        To: Twilio phone number that received the SMS (identifies restaurant)
        From: Customer's phone number
        Body: SMS message content
        MessageSid: Unique message identifier
        db: Database session

    Returns:
        TwiML response with reply message
    """
    logger.info(f"SMS received from {From} to {To}: {Body}")

    # Look up which restaurant owns this Twilio number
    restaurant = db.query(RestaurantAccount).filter(
        RestaurantAccount.twilio_phone_number == To
    ).first()

    if not restaurant:
        logger.warning(f"No restaurant found for Twilio number {To}")
        response = sms_service.create_twiml_response(
            "This number is not configured. Please contact support."
        )
        return Response(content=response, media_type="application/xml")

    # Handle missing body
    if not Body:
        response = sms_service.create_twiml_response(
            "I didn't receive your message. Could you please try again?"
        )
        return Response(content=response, media_type="application/xml")

    # Get or create conversation state for this phone number
    state_key = f"{From}_{To}"  # Unique per customer-restaurant pair
    if state_key not in sms_conversation_state:
        sms_conversation_state[state_key] = {
            "phone": From,
            "restaurant_id": restaurant.id,
            "context": {},
            "step": "initial",
            "last_activity": datetime.now(),
            "messages": [],
            "conversation_id": MessageSid or f"sms_{From}_{To}_{datetime.now().timestamp()}"
        }

    state = sms_conversation_state[state_key]
    state["last_activity"] = datetime.now()
    
    # Add user message to transcript
    if Body:
        state["messages"].append({
            "role": "user",
            "content": Body,
            "timestamp": datetime.now().isoformat()
        })

    try:
        # Process the message with AI conversation handler
        result = await conversation_handler.process_message(
            message=Body,
            phone=From,
            restaurant_id=restaurant.id,
            context=state["context"],
            db=db
        )

        # Update state
        state["context"] = result.get("context", {})
        state["step"] = result.get("next_step", "initial")

        # Get the response message
        response_message = result.get("message", "I'm not sure I understand. Could you rephrase that?")
        
        # Add assistant response to transcript
        state["messages"].append({
            "role": "assistant",
            "content": response_message,
            "timestamp": datetime.now().isoformat()
        })

        # Handle different response types
        response_type = result.get("type")

        if response_type == "confirmation":
            # Order/booking was made successfully
            if "booking" in result:
                booking_data = result.get("booking")
                response_message = f"""✅ Reservation Confirmed!

{restaurant.business_name}
Date: {booking_data['booking_date']}
Time: {booking_data['booking_time']}
Party Size: {booking_data['party_size']}
Name: {booking_data['customer_name']}

Confirmation #: {booking_data['confirmation_id']}

We'll see you then!"""
            elif "order" in result:
                order_data = result.get("order")
                response_message = f"""✅ Order Confirmed!

{restaurant.business_name}
Order #: {order_data.get('order_id', 'N/A')}
Total: ${order_data.get('total', 0):.2f}

{order_data.get('message', 'Your order will be ready soon!')}"""

        elif response_type == "goodbye":
            # End conversation
            response_message = result.get("message", "Thanks for contacting us!")
            # Save transcript before cleaning up
            if state_key in sms_conversation_state:
                try:
                    outcome = None
                    if "booking" in result:
                        outcome = "booking_created"
                    elif "order" in result:
                        outcome = "order_placed"
                    
                    transcript_service.save_transcript(
                        db=db,
                        account_id=restaurant.id,
                        transcript_type="sms",
                        customer_phone=From,
                        conversation_id=state.get("conversation_id", MessageSid or ""),
                        messages=state.get("messages", []),
                        twilio_phone=To,
                        outcome=outcome
                    )
                except Exception as e:
                    logger.error(f"Failed to save SMS transcript: {str(e)}")
                del sms_conversation_state[state_key]

        # Create TwiML response
        response = sms_service.create_twiml_response(response_message)
        return Response(content=response, media_type="application/xml")

    except Exception as e:
        logger.error(f"Error processing SMS: {str(e)}", exc_info=True)
        response = sms_service.create_twiml_response(
            f"Sorry, I encountered an error. Please call us at {restaurant.phone or 'our restaurant'} or try again later."
        )
        return Response(content=response, media_type="application/xml")


@router.get("/sms/health")
async def sms_health():
    """Health check for SMS service."""
    return {
        "service": "sms",
        "enabled": sms_service.enabled,
        "status": "healthy" if sms_service.enabled else "disabled"
    }
