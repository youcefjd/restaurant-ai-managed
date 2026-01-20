"""
Retell AI Voice Integration API.

Handles:
1. Webhook events from Retell (call_started, call_ended, call_analyzed)
2. WebSocket connection for custom LLM responses
3. Agent and phone number management

Architecture:
  Retell handles: Phone → STT → TTS → Phone
  We handle: LLM responses via WebSocket

This is much simpler than the Twilio+Deepgram+TTS stack because
Retell manages the entire voice pipeline.
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.retell_service import retell_service
from backend.services.conversation_handler import conversation_handler
from backend.services.transcript_service import transcript_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Store active call contexts
active_calls: Dict[str, Dict[str, Any]] = {}


# ==================== Pydantic Models ====================

class WebhookEvent(BaseModel):
    """Retell webhook event."""
    event: str
    call: Dict[str, Any]


class CreateAgentRequest(BaseModel):
    """Request to create a Retell agent."""
    name: str
    voice_id: str = "11labs-Adrian"
    restaurant_id: int


class BindPhoneRequest(BaseModel):
    """Request to bind a phone number to an agent."""
    phone_number: str
    agent_id: str


# ==================== Webhook Handler ====================

@router.post("/webhook")
async def retell_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle Retell webhook events.

    Events:
    - call_started: Call has begun
    - call_ended: Call has ended
    - call_analyzed: Post-call analysis complete
    """
    # Get raw body for signature verification
    body = await request.body()

    # Verify signature
    signature = request.headers.get("X-Retell-Signature", "")
    if not retell_service.verify_webhook_signature(body, signature):
        logger.warning("Invalid Retell webhook signature")
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        event_data = json.loads(body)
        event_type = event_data.get("event")
        call_data = event_data.get("call", {})
        call_id = call_data.get("call_id")

        logger.info(f"Retell webhook: {event_type} for call {call_id}")

        if event_type == "call_started":
            # Initialize call context
            active_calls[call_id] = {
                "call_id": call_id,
                "from_number": call_data.get("from_number"),
                "to_number": call_data.get("to_number"),
                "agent_id": call_data.get("agent_id"),
                "start_time": datetime.now(),
                "conversation_history": [],
                "context": {},
                "metadata": call_data.get("metadata", {})
            }
            logger.info(f"Call started: {call_id} from {call_data.get('from_number')}")

        elif event_type == "call_ended":
            # Save transcript and clean up
            if call_id in active_calls:
                call_context = active_calls[call_id]

                # Get restaurant ID from metadata or agent binding
                restaurant_id = call_context.get("metadata", {}).get("restaurant_id")

                if restaurant_id and call_context.get("conversation_history"):
                    try:
                        transcript_service.save_transcript(
                            db=db,
                            account_id=restaurant_id,
                            transcript_type="voice_retell",
                            customer_phone=call_context.get("from_number", ""),
                            conversation_id=call_id,
                            messages=call_context["conversation_history"],
                            twilio_phone=call_context.get("to_number")
                        )
                        logger.info(f"Saved transcript for call {call_id}")
                    except Exception as e:
                        logger.error(f"Failed to save transcript: {e}")

                del active_calls[call_id]

            logger.info(f"Call ended: {call_id}, duration: {call_data.get('duration_ms')}ms")

        elif event_type == "call_analyzed":
            # Post-call analysis with sentiment, summary, etc.
            analysis = call_data.get("call_analysis", {})
            logger.info(f"Call analyzed: {call_id}, sentiment: {analysis.get('user_sentiment')}")

        return JSONResponse({"status": "ok"})

    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Custom LLM WebSocket ====================

@router.websocket("/llm-websocket/{call_id}")
async def llm_websocket(websocket: WebSocket, call_id: str):
    """
    WebSocket endpoint for custom LLM responses.

    Retell sends conversation updates, we respond with LLM-generated text.
    Retell handles STT and TTS - we just provide the "brain".
    """
    await websocket.accept()
    logger.info(f"LLM WebSocket connected for call: {call_id}")

    # Get or create call context
    call_context = active_calls.get(call_id, {
        "call_id": call_id,
        "conversation_history": [],
        "context": {},
        "restaurant_id": None,
        "from_number": None
    })

    # Track response IDs to handle interruptions
    current_response_id = 0

    try:
        # Send initial config
        config_message = {
            "response_type": "config",
            "config": {
                "auto_reconnect": True,
                "call_details": True
            }
        }
        await websocket.send_json(config_message)

        while True:
            try:
                # Receive message from Retell
                data = await websocket.receive_json()
                interaction_type = data.get("interaction_type")

                logger.debug(f"Received from Retell: {interaction_type}")

                if interaction_type == "call_details":
                    # Extract call details
                    call_details = data.get("call", {})
                    call_context["from_number"] = call_details.get("from_number")
                    call_context["to_number"] = call_details.get("to_number")
                    call_context["agent_id"] = call_details.get("agent_id")
                    metadata = call_details.get("metadata", {})
                    call_context["restaurant_id"] = metadata.get("restaurant_id")
                    call_context["metadata"] = metadata

                    # Update active calls
                    active_calls[call_id] = call_context

                    logger.info(f"Call details received: {call_context['from_number']} -> restaurant {call_context['restaurant_id']}")

                    # Send greeting
                    restaurant_name = metadata.get("restaurant_name", "our restaurant")
                    greeting = f"Hi, thanks for calling {restaurant_name}. How can I help you today?"

                    await _send_response(
                        websocket,
                        response_id=0,
                        content=greeting,
                        content_complete=True
                    )

                    # Add to history
                    call_context["conversation_history"].append({
                        "role": "assistant",
                        "content": greeting
                    })

                elif interaction_type == "ping_pong":
                    # Respond to ping
                    await websocket.send_json({
                        "response_type": "ping_pong",
                        "timestamp": data.get("timestamp")
                    })

                elif interaction_type == "update_only":
                    # Just update transcript, no response needed
                    transcript = data.get("transcript", [])
                    if transcript:
                        # Update conversation history with latest
                        _update_history_from_transcript(call_context, transcript)

                elif interaction_type in ["response_required", "reminder_required"]:
                    # LLM response needed
                    response_id = data.get("response_id", 0)
                    current_response_id = response_id
                    transcript = data.get("transcript", [])

                    # Get the latest user message
                    user_message = ""
                    if transcript:
                        for utterance in reversed(transcript):
                            if utterance.get("role") == "user":
                                user_message = utterance.get("content", "")
                                break

                    if not user_message:
                        # No user message, might be a reminder
                        if interaction_type == "reminder_required":
                            user_message = "[silence - customer hasn't responded]"
                        else:
                            continue

                    logger.info(f"Processing: {user_message[:100]}...")

                    # Update history
                    _update_history_from_transcript(call_context, transcript)

                    # Process with our conversation handler
                    response = await _process_with_llm(
                        user_message,
                        call_context,
                        websocket,
                        response_id,
                        current_response_id
                    )

                    if response:
                        # Add assistant response to history
                        call_context["conversation_history"].append({
                            "role": "assistant",
                            "content": response
                        })

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for call: {call_id}")
                break
            except Exception as e:
                logger.error(f"Error processing message: {e}", exc_info=True)
                # Try to send error response
                try:
                    await _send_response(
                        websocket,
                        response_id=current_response_id,
                        content="I'm sorry, I had trouble with that. Could you say that again?",
                        content_complete=True
                    )
                except:
                    pass

    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)

    finally:
        logger.info(f"LLM WebSocket closed for call: {call_id}")


async def _send_response(
    websocket: WebSocket,
    response_id: int,
    content: str,
    content_complete: bool = False,
    end_call: bool = False
):
    """Send a response to Retell."""
    message = {
        "response_type": "response",
        "response_id": response_id,
        "content": content,
        "content_complete": content_complete,
        "end_call": end_call
    }
    await websocket.send_json(message)


async def _process_with_llm(
    user_message: str,
    call_context: Dict[str, Any],
    websocket: WebSocket,
    response_id: int,
    current_response_id: int
) -> Optional[str]:
    """
    Process user message with our conversation handler.

    Streams response back to Retell for low latency.
    """
    from backend.database import SessionLocal

    restaurant_id = call_context.get("restaurant_id")
    from_number = call_context.get("from_number", "")
    context = call_context.get("context", {})
    conversation_history = call_context.get("conversation_history", [])

    if not restaurant_id:
        # Try to get restaurant from phone number
        logger.warning("No restaurant_id in call context")
        response = "I'm sorry, I'm having trouble identifying the restaurant. Please try calling again."
        await _send_response(websocket, response_id, response, content_complete=True)
        return response

    db = SessionLocal()
    try:
        # Call our existing conversation handler
        result = await conversation_handler.process_message(
            message=user_message,
            phone=from_number,
            restaurant_id=restaurant_id,
            context=context,
            conversation_history=conversation_history,
            db=db
        )

        # Update context
        call_context["context"] = result.get("context", context)

        # Get response message
        response_message = result.get("message", "I didn't understand that. Could you repeat?")
        response_type = result.get("type", "gather")

        # Check if we should end the call
        end_call = response_type in ["goodbye", "hangup"]

        # Check if response_id is still current (user might have interrupted)
        if response_id != current_response_id:
            logger.info(f"Response {response_id} abandoned, current is {current_response_id}")
            return None

        # Send response to Retell
        # For low latency, we could stream sentence by sentence
        # But for simplicity, send complete response
        await _send_response(
            websocket,
            response_id,
            response_message,
            content_complete=True,
            end_call=end_call
        )

        return response_message

    except Exception as e:
        logger.error(f"LLM processing error: {e}", exc_info=True)
        error_response = "I'm sorry, I had trouble understanding. Could you repeat that?"
        await _send_response(websocket, response_id, error_response, content_complete=True)
        return error_response

    finally:
        db.close()


def _update_history_from_transcript(
    call_context: Dict[str, Any],
    transcript: List[Dict[str, str]]
):
    """Update conversation history from Retell transcript."""
    # Retell provides full transcript, we just need the latest
    # Our history format: [{"role": "user/assistant", "content": "..."}]

    history = call_context.get("conversation_history", [])

    # Map Retell roles to our format
    for utterance in transcript:
        role = "assistant" if utterance.get("role") == "agent" else "user"
        content = utterance.get("content", "")

        # Check if already in history (avoid duplicates)
        if history and history[-1].get("content") == content:
            continue

        # Only add if it's new
        if content:
            # Check if this extends the last message of same role
            if history and history[-1].get("role") == role:
                # Retell might send partial updates, check if it's an extension
                last_content = history[-1].get("content", "")
                if content.startswith(last_content):
                    history[-1]["content"] = content
                elif not last_content.startswith(content):
                    history.append({"role": role, "content": content})
            else:
                history.append({"role": role, "content": content})

    call_context["conversation_history"] = history


# ==================== Agent Management Endpoints ====================

@router.post("/agents")
async def create_agent(
    request: CreateAgentRequest,
    db: Session = Depends(get_db)
):
    """Create a Retell agent for a restaurant."""
    if not retell_service.is_enabled():
        raise HTTPException(status_code=503, detail="Retell service not configured")

    # Get restaurant details
    from backend.models_platform import RestaurantAccount
    restaurant = db.query(RestaurantAccount).filter(
        RestaurantAccount.id == request.restaurant_id
    ).first()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # Build LLM WebSocket URL
    public_url = os.getenv("PUBLIC_WS_URL", "").replace("wss://", "").replace("ws://", "")
    if not public_url:
        raise HTTPException(
            status_code=400,
            detail="PUBLIC_WS_URL not configured. Set it to your ngrok or production URL."
        )

    llm_ws_url = f"wss://{public_url}/api/retell/llm-websocket"

    # Create agent
    agent = await retell_service.create_agent(
        name=f"{restaurant.business_name} Voice Agent",
        voice_id=request.voice_id,
        llm_websocket_url=llm_ws_url,
        webhook_url=f"https://{public_url}/api/retell/webhook",
        ambient_sound="office",  # Slight background noise for realism
        responsiveness=0.8,  # Quick responses
        interruption_sensitivity=0.7,  # Allow interruptions
        enable_backchannel=True,  # "uh-huh", "I see"
        boosted_keywords=[restaurant.business_name],  # Improve recognition
        reminder_trigger_ms=8000,  # Remind after 8s silence
        reminder_max_count=2,
        end_call_after_silence_ms=30000,  # End after 30s silence
    )

    if not agent:
        raise HTTPException(status_code=500, detail="Failed to create agent")

    # Store agent ID with restaurant (you might want to add a field for this)
    # For now, return the agent details
    return {
        "agent_id": agent.get("agent_id"),
        "name": agent.get("agent_name"),
        "voice_id": agent.get("voice_id"),
        "restaurant_id": request.restaurant_id,
        "llm_websocket_url": llm_ws_url
    }


@router.get("/agents")
async def list_agents():
    """List all Retell agents."""
    if not retell_service.is_enabled():
        raise HTTPException(status_code=503, detail="Retell service not configured")

    agents = await retell_service.list_agents()
    return {"agents": agents}


@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    """Delete a Retell agent."""
    if not retell_service.is_enabled():
        raise HTTPException(status_code=503, detail="Retell service not configured")

    success = await retell_service.delete_agent(agent_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete agent")

    return {"status": "deleted", "agent_id": agent_id}


# ==================== Phone Number Management ====================

@router.get("/phone-numbers")
async def list_phone_numbers():
    """List all Retell phone numbers."""
    if not retell_service.is_enabled():
        raise HTTPException(status_code=503, detail="Retell service not configured")

    numbers = await retell_service.list_phone_numbers()
    return {"phone_numbers": numbers}


@router.post("/phone-numbers/bind")
async def bind_phone_number(request: BindPhoneRequest):
    """Bind a phone number to an agent."""
    if not retell_service.is_enabled():
        raise HTTPException(status_code=503, detail="Retell service not configured")

    result = await retell_service.update_phone_number(
        phone_number=request.phone_number,
        agent_id=request.agent_id
    )

    if not result:
        raise HTTPException(status_code=500, detail="Failed to bind phone number")

    return result


@router.post("/phone-numbers/import")
async def import_twilio_number(
    phone_number: str,
    agent_id: str = None
):
    """Import an existing Twilio phone number to Retell."""
    if not retell_service.is_enabled():
        raise HTTPException(status_code=503, detail="Retell service not configured")

    twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
    twilio_token = os.getenv("TWILIO_AUTH_TOKEN")

    if not twilio_sid or not twilio_token:
        raise HTTPException(
            status_code=400,
            detail="Twilio credentials not configured"
        )

    result = await retell_service.import_phone_number(
        phone_number=phone_number,
        twilio_account_sid=twilio_sid,
        twilio_auth_token=twilio_token,
        agent_id=agent_id
    )

    if not result:
        raise HTTPException(status_code=500, detail="Failed to import phone number")

    return result


# ==================== SMS Endpoints ====================

@router.post("/sms/send")
async def send_sms(
    from_number: str,
    to_number: str,
    message: str
):
    """Send a one-way SMS."""
    if not retell_service.is_enabled():
        raise HTTPException(status_code=503, detail="Retell service not configured")

    result = await retell_service.send_sms(from_number, to_number, message)

    if not result:
        raise HTTPException(status_code=500, detail="Failed to send SMS")

    return result


@router.post("/sms/chat")
async def start_sms_chat(
    from_number: str,
    to_number: str,
    agent_id: str = None,
    restaurant_id: int = None
):
    """Start a two-way SMS conversation with AI agent."""
    if not retell_service.is_enabled():
        raise HTTPException(status_code=503, detail="Retell service not configured")

    metadata = {}
    if restaurant_id:
        metadata["restaurant_id"] = restaurant_id

    result = await retell_service.create_sms_chat(
        from_number=from_number,
        to_number=to_number,
        agent_id=agent_id,
        metadata=metadata if metadata else None
    )

    if not result:
        raise HTTPException(status_code=500, detail="Failed to start SMS chat")

    return result


# ==================== Call Management ====================

@router.post("/calls/outbound")
async def create_outbound_call(
    from_number: str,
    to_number: str,
    agent_id: str = None,
    restaurant_id: int = None
):
    """Create an outbound call."""
    if not retell_service.is_enabled():
        raise HTTPException(status_code=503, detail="Retell service not configured")

    metadata = {}
    if restaurant_id:
        metadata["restaurant_id"] = restaurant_id

    result = await retell_service.create_phone_call(
        from_number=from_number,
        to_number=to_number,
        agent_id=agent_id,
        metadata=metadata if metadata else None
    )

    if not result:
        raise HTTPException(status_code=500, detail="Failed to create call")

    return result


@router.get("/calls/{call_id}")
async def get_call(call_id: str):
    """Get call details."""
    if not retell_service.is_enabled():
        raise HTTPException(status_code=503, detail="Retell service not configured")

    result = await retell_service.get_call(call_id)

    if not result:
        raise HTTPException(status_code=404, detail="Call not found")

    return result


# ==================== Health Check ====================

@router.get("/health")
async def retell_health():
    """Health check for Retell integration."""
    return {
        "service": "retell",
        "enabled": retell_service.is_enabled(),
        "active_calls": len(active_calls),
        "status": "healthy" if retell_service.is_enabled() else "disabled"
    }
