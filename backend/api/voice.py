"""
Voice call webhook endpoints for Twilio Voice API.

Handles incoming calls, processes speech-to-text, and manages
the conversation flow for making reservations.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, date, time, timedelta
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import Response
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Restaurant, Table, Customer, Booking, BookingStatus
from backend.services.voice_service import voice_service
from backend.services.sms_service import sms_service
from backend.services.conversation_handler import conversation_handler
from backend.services.transcript_service import transcript_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Store conversation state (in production, use Redis or similar)
conversation_state: Dict[str, Dict[str, Any]] = {}


def get_base_url(request: Request) -> str:
    """Extract base URL from request, handling ngrok/proxy headers."""
    base_url = str(request.base_url).rstrip('/')

    # Check for ngrok/proxy headers
    if 'x-forwarded-proto' in request.headers:
        protocol = request.headers['x-forwarded-proto']
        # ngrok uses the Host header, not X-Forwarded-Host
        host = request.headers.get('x-forwarded-host') or request.headers.get('host', '')
        if host and host != 'localhost:8000' and not host.startswith('127.0.0.1'):
            base_url = f"{protocol}://{host}"

    return base_url


@router.post("/welcome")
async def voice_welcome(
    request: Request,
    To: Optional[str] = Form(None),
    From: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Initial webhook when call is received.
    Returns TwiML with welcome message.

    Args:
        request: FastAPI request object (to get base URL)
        To: Twilio phone number that was called (identifies restaurant)
        From: Caller's phone number
        db: Database session
    """
    logger.info(f"Voice call received from {From} to {To}")

    # Get base URL from request
    base_url = get_base_url(request)
    logger.info(f"Using base URL: {base_url}")

    # Normalize phone number (remove spaces, ensure + prefix)
    to_normalized = To.strip() if To else None
    if to_normalized and not to_normalized.startswith('+'):
        to_normalized = '+' + to_normalized

    # Look up which restaurant owns this Twilio number
    from backend.models_platform import RestaurantAccount
    restaurant = db.query(RestaurantAccount).filter(
        RestaurantAccount.twilio_phone_number == to_normalized
    ).first()

    if not restaurant:
        logger.warning(f"No restaurant found for Twilio number {To}")
        response = voice_service.create_error_response(
            "This number is not configured. Please contact support.",
            base_url=base_url
        )
        return Response(content=str(response), media_type="application/xml")

    # Create welcome with restaurant's business name
    response = voice_service.create_welcome_response(
        restaurant_name=restaurant.business_name,
        base_url=base_url
    )
    twiml_str = str(response)
    logger.info(f"Returning TwiML: {twiml_str[:200]}")
    return Response(content=twiml_str, media_type="application/xml")


@router.post("/process")
async def process_speech(
    request: Request,
    SpeechResult: Optional[str] = Form(None),
    CallSid: Optional[str] = Form(None),
    From: Optional[str] = Form(None),
    To: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Process speech input from customer.

    Args:
        SpeechResult: Transcribed speech from Twilio
        CallSid: Unique call identifier
        From: Caller's phone number
        To: Twilio phone number called (identifies restaurant)
        db: Database session

    Returns:
        TwiML response
    """
    logger.info(f"Processing speech from {From} to {To}: {SpeechResult}")

    # Normalize phone number (remove spaces, ensure + prefix)
    to_normalized = To.strip() if To else None
    if to_normalized and not to_normalized.startswith('+'):
        to_normalized = '+' + to_normalized

    # Look up which restaurant owns this Twilio number
    from backend.models_platform import RestaurantAccount
    restaurant = db.query(RestaurantAccount).filter(
        RestaurantAccount.twilio_phone_number == to_normalized
    ).first()

    if not restaurant:
        logger.warning(f"No restaurant found for Twilio number {To}")
        response = voice_service.create_error_response(
            "This number is not configured. Please contact support."
        )
        return Response(content=str(response), media_type="application/xml")

    # Handle missing speech
    if not SpeechResult:
        base_url = get_base_url(request)
        response = voice_service.create_error_response(
            "I didn't catch that. Could you please repeat?",
            base_url=base_url
        )
        return Response(content=str(response), media_type="application/xml")

    # Get or create conversation state
    if CallSid not in conversation_state:
        conversation_state[CallSid] = {
            "phone": From,
            "restaurant_id": restaurant.id,
            "context": {},
            "step": "initial",
            "messages": []
        }

    state = conversation_state[CallSid]
    
    # Add user message to transcript
    if SpeechResult:
        state["messages"].append({
            "role": "user",
            "content": SpeechResult,
            "timestamp": datetime.now().isoformat()
        })

    try:
        # Process the speech with AI conversation handler
        result = await conversation_handler.process_message(
            message=SpeechResult,
            phone=From,
            restaurant_id=restaurant.id,
            context=state["context"],
            db=db
        )

        # Update state
        state["context"] = result.get("context", {})
        state["step"] = result.get("next_step", "initial")
        
        # Get response message for transcript
        response_message = result.get("message", "")
        
        # Add assistant response to transcript
        if response_message:
            state["messages"].append({
                "role": "assistant",
                "content": response_message,
                "timestamp": datetime.now().isoformat()
            })

        # Handle different response types
        response_type = result.get("type")

        if response_type == "confirmation":
            # Booking was made successfully
            booking_data = result.get("booking")
            response = voice_service.create_confirmation_response(
                restaurant_name=booking_data["restaurant_name"],
                booking_date=booking_data["booking_date"],
                booking_time=booking_data["booking_time"],
                party_size=booking_data["party_size"],
                customer_name=booking_data["customer_name"],
                confirmation_id=booking_data["confirmation_id"]
            )

        elif response_type == "availability":
            # Show available time slots
            response = voice_service.create_availability_response(
                available_times=result.get("available_times", []),
                requested_date=result.get("requested_date"),
                party_size=result.get("party_size")
            )

        elif response_type == "gather":
            # Need more information from customer
            base_url = get_base_url(request)
            response = voice_service.create_gather_response(
                prompt=result.get("message", "How can I help you?"),
                base_url=base_url
            )

        elif response_type == "goodbye":
            # End conversation
            response = voice_service.create_goodbye_response()
            # Save transcript before cleaning up
            if CallSid in conversation_state:
                state = conversation_state[CallSid]
                try:
                    outcome = None
                    if "booking" in result:
                        outcome = "booking_created"
                    elif "order" in result:
                        outcome = "order_placed"
                    
                    transcript_service.save_transcript(
                        db=db,
                        account_id=restaurant.id,
                        transcript_type="voice",
                        customer_phone=From,
                        conversation_id=CallSid,
                        messages=state.get("messages", []),
                        twilio_phone=To,
                        outcome=outcome
                    )
                except Exception as e:
                    logger.error(f"Failed to save transcript: {str(e)}")
                del conversation_state[CallSid]

        else:
            # Default: gather more input
            base_url = get_base_url(request)
            message = result.get("message", "I'm not sure I understand. Could you rephrase that?")
            response = voice_service.create_gather_response(prompt=message, base_url=base_url)

        return Response(content=str(response), media_type="application/xml")

    except Exception as e:
        logger.error(f"Error processing speech: {str(e)}", exc_info=True)
        response = voice_service.create_error_response(
            "I'm sorry, I encountered an error. Let me transfer you to our main menu."
        )
        return Response(content=str(response), media_type="application/xml")


@router.post("/status")
async def call_status(
    request: Request,
    CallSid: Optional[str] = Form(None),
    CallStatus: Optional[str] = Form(None),
    CallDuration: Optional[str] = Form(None),
    To: Optional[str] = Form(None),
    From: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Handle call status callbacks.

    Args:
        CallSid: Unique call identifier
        CallStatus: Status of the call (completed, failed, busy, etc.)
        CallDuration: Call duration in seconds
        To: Restaurant's Twilio number
        From: Customer's phone number
        db: Database session

    Returns:
        Success response
    """
    logger.info(f"Call {CallSid} status: {CallStatus}")

    # Save transcript and clean up conversation state when call ends
    if CallStatus in ["completed", "failed", "busy", "no-answer"] and CallSid in conversation_state:
        state = conversation_state[CallSid]
        try:
            from backend.models_platform import RestaurantAccount
            restaurant = db.query(RestaurantAccount).filter(
                RestaurantAccount.id == state.get("restaurant_id")
            ).first()
            
            if restaurant:
                duration_seconds = int(CallDuration) if CallDuration else None
                transcript_service.save_transcript(
                    db=db,
                    account_id=restaurant.id,
                    transcript_type="voice",
                    customer_phone=state.get("phone", From or ""),
                    conversation_id=CallSid,
                    messages=state.get("messages", []),
                    twilio_phone=To,
                    duration_seconds=duration_seconds
                )
        except Exception as e:
            logger.error(f"Failed to save transcript on call end: {str(e)}")
        
        del conversation_state[CallSid]

    return {"status": "ok"}


@router.get("/health")
async def voice_health():
    """Health check for voice service."""
    return {
        "service": "voice",
        "enabled": voice_service.enabled,
        "status": "healthy" if voice_service.enabled else "disabled"
    }


# SMS conversation state (in production, use Redis or similar)
sms_conversation_state: Dict[str, Dict[str, Any]] = {}


@router.post("/sms/incoming")
async def sms_incoming(
    To: Optional[str] = Form(None),
    From: Optional[str] = Form(None),
    Body: Optional[str] = Form(None),
    MessageSid: Optional[str] = Form(None),
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
    from backend.models_platform import RestaurantAccount
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
        "status": "healthy" if sms_service.enabled else "disabled",
        "active_conversations": len(sms_conversation_state)
    }
