"""
Retell Native LLM Service.

Manages Retell's built-in LLM with function calling for low-latency voice interactions.
Instead of routing every message through our own LLM, Retell's LLM handles conversation
flow and only calls our backend for data operations (menu, cart, orders).
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List

import httpx

logger = logging.getLogger(__name__)


class RetellLLMService:
    """Service for managing Retell's native LLM configuration."""

    BASE_URL = "https://api.retellai.com"

    def __init__(self):
        """Initialize Retell LLM service."""
        self.api_key = os.getenv("RETELL_API_KEY")
        self.enabled = bool(self.api_key)
        # Get public URL from env - try PUBLIC_URL first, then derive from PUBLIC_WS_URL
        public_url = os.getenv("PUBLIC_URL", "")
        if not public_url:
            ws_url = os.getenv("PUBLIC_WS_URL", "")
            if ws_url:
                # Convert wss://example.com to https://example.com
                public_url = ws_url.replace("wss://", "https://").replace("ws://", "http://")
        self.public_url = public_url.rstrip("/")

        if self.enabled:
            logger.info("Retell LLM service initialized")
        else:
            logger.warning("RETELL_API_KEY not set - Retell LLM service disabled")

    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _get_system_prompt(self, restaurant_name: str = "the restaurant", restaurant_id: int = None) -> str:
        """
        Get the system prompt for Retell's native LLM.
        This is much shorter than our custom prompt since Retell handles voice nuances.
        """
        return f"""You are a friendly phone assistant for {restaurant_name}. You help customers place pickup orders.

## CRITICAL RULES - SESSION ID (GENERATE YOUR OWN - DO NOT COPY THIS EXAMPLE)
At the START of this conversation, you MUST generate YOUR OWN UNIQUE random 8-character session ID.
Use random letters and numbers like: "r7t2q9w4", "m3x8k1p5", "j6b9n2v8" - create your OWN unique one!
DO NOT use "a1b2c3d4" - that is just showing the format. Create YOUR OWN RANDOM ID.
Use this SAME session_id you generated in EVERY function call throughout this conversation.
This ensures your cart is separate from other conversations.

## CRITICAL RULES - GENERAL
- restaurant_id is {restaurant_id} - pass this to EVERY function call
- session_id - generate ONCE at start, use in EVERY function call
- Keep ALL responses to 1-2 SHORT sentences
- NEVER repeat yourself - say something ONCE then WAIT for customer response
- After asking a question, STOP and wait - do NOT keep talking or call more functions
- NEVER invent prices - only mention prices when customer asks "how much"

## START OF CONVERSATION - MANDATORY
1. Generate YOUR OWN unique 8-character session_id using random letters/numbers (NOT "a1b2c3d4"!)
2. Example formats: "x7k9m2p4", "q3r8t1w6", "h5j2m9v4" - make your OWN random one
3. Use the session_id YOU generated in ALL function calls for this conversation

## ANSWERING QUESTIONS - MANDATORY
When customer asks ANY question (menu, hours, prices, etc.):
1. ANSWER the question FIRST using the appropriate function
2. THEN ask if they want to order
3. NEVER end the call without answering their question
4. If asked about menu items: call get_menu() and list the relevant items
5. If asked about prices: call get_menu(include_prices=true) and tell them the prices
6. If asked about hours: call get_hours() and tell them the hours

## TAKING ORDERS - FUNCTION CALLS
When customer says they want an item:
- IMMEDIATELY call add_to_cart(restaurant_id={restaurant_id}, item_name="exact item name", quantity=N) BEFORE saying anything
- NEVER say "I've got that" or confirm an item until AFTER add_to_cart succeeds
- Say "Got it" and ask "Anything else?" - then STOP and WAIT

When customer changes quantity ("make that 2" or "actually 3"):
- Call update_cart_item(restaurant_id={restaurant_id}, item_name="item name", quantity=NEW_TOTAL)
- This REPLACES the quantity, not adds to it

When customer removes an item ("remove the X" or "no X"):
- Call remove_from_cart(restaurant_id={restaurant_id}, item_name="item name")

When customer says "start over" or "cancel everything":
- Call clear_cart(restaurant_id={restaurant_id})
- Then say "OK, let's start fresh. What would you like?"

When customer says "that's it" or "that's all" or is done ordering:
- ALWAYS call get_cart(restaurant_id={restaurant_id}) to review the order
- Read back their order and total from the get_cart response
- Ask "What name for the order and when to pick up?"

## BEFORE CREATING ORDER - MANDATORY PAYMENT STEP
When you have both name AND pickup time:
1. FIRST call get_cart(restaurant_id={restaurant_id}) to verify cart contents and total
2. THEN ask: "Your total including tax is $X. Would you like to pay now by card, or pay when you pick up?"
3. Wait for customer response about payment preference
4. If they want to pay by card: follow the PAYMENT COLLECTION steps below
5. If they want to pay at pickup: call create_order() with payment_method="pay_at_pickup"
6. Confirm the order, say goodbye, then call end_call()

IMPORTANT:
- NEVER call create_order without asking about payment first
- NEVER call create_order without calling get_cart first in the same conversation turn

## ITEM NOT ON MENU
If customer asks for something not on the menu:
- Do NOT call add_to_cart
- Say "We don't have [item]. We have [similar items]. Would you like one of those?"

## SPECIAL REQUESTS
For modifications ("extra spicy", "no garlic", "add cheese"):
- Include in special_requests parameter: add_to_cart(..., special_requests="extra spicy, no garlic")
- Do NOT add modifications as separate items

## PAYMENT COLLECTION (when customer chooses to pay by card)
1. Call initiate_payment_collection(restaurant_id={restaurant_id}, session_id=session_id)
2. Say exactly what the function response tells you to say (prompts for card number)
3. Customer will enter digits via phone keypad - you'll receive them as input
4. Call process_dtmf_input(restaurant_id={restaurant_id}, session_id=session_id, digits="the digits")
5. The response will tell you the next step (expiry, then CVV, then authorized)
6. Keep calling process_dtmf_input for each entry until you get "authorized" status
7. Once authorized, call create_order() with payment_method="card"

If payment fails:
- Call retry_payment() to try a different card
- Or call cancel_payment() and create_order() with payment_method="pay_at_pickup"

IMPORTANT for card payments:
- NEVER repeat card numbers, expiry, or CVV back to the customer
- Just say "Got it" after each successful entry
- Follow the exact prompts from each function response

## ENDING THE CALL
Call end_call() ONLY after:
1. Order is confirmed and you said goodbye
2. Customer explicitly says goodbye without wanting to order
3. Customer's question is answered AND they say goodbye

NEVER end call without:
- Answering any questions the customer asked
- Confirming if they want to order

## PREVENTING LOOPS - CRITICAL
- After saying "Anything else?" → STOP, do not say anything more, wait for response
- After asking for name/time → STOP, wait for response
- NEVER call the same function twice in a row with same parameters
- If function returns an error, tell customer and ask what they'd like instead
- Maximum 1 function call per turn unless adding multiple different items
- If you already called clear_cart this conversation, do NOT call it again
"""

    def _get_tools_config(self, restaurant_id: int = None) -> List[Dict[str, Any]]:
        """Get the tools/functions configuration for Retell LLM."""
        if not self.public_url:
            logger.warning("PUBLIC_URL not set - tools will not work")
            return []

        base_url = f"{self.public_url}/api/retell-functions"

        # Use restaurant_id as the primary identifier since call_id isn't available
        return [
            {
                "type": "custom",
                "name": "get_menu",
                "description": "Get menu highlights. Returns a brief message with popular items - just read the 'message' field. Do NOT add prices unless the customer asked about prices.",
                "url": f"{base_url}/get_menu",
                "method": "POST",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "restaurant_id": {
                            "type": "integer",
                            "description": f"The restaurant ID. Always use {restaurant_id}."
                        },
                        "category": {
                            "type": "string",
                            "description": "Optional category to filter (e.g., 'tacos', 'drinks', 'desserts')"
                        },
                        "include_prices": {
                            "type": "boolean",
                            "description": "Set to true ONLY if customer asked about prices. Default false."
                        }
                    },
                    "required": ["restaurant_id"]
                },
                "speak_during_execution": False,
                "speak_after_execution": True,
                "timeout_ms": 5000
            },
            {
                "type": "custom",
                "name": "add_to_cart",
                "description": "Add an item to the customer's order. Call this when customer says they want to order something. The response includes a 'message' field with confirmation to speak.",
                "url": f"{base_url}/add_to_cart",
                "method": "POST",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "restaurant_id": {
                            "type": "integer",
                            "description": f"The restaurant ID. Always use {restaurant_id}."
                        },
                        "session_id": {
                            "type": "string",
                            "description": "Your unique 8-char session ID generated at conversation start. REQUIRED for cart isolation."
                        },
                        "item_name": {
                            "type": "string",
                            "description": "Name of the menu item"
                        },
                        "quantity": {
                            "type": "integer",
                            "description": "Quantity to order (default 1)"
                        },
                        "special_requests": {
                            "type": "string",
                            "description": "Any modifications like 'extra cheese', 'no onions', 'spicy'"
                        }
                    },
                    "required": ["restaurant_id", "session_id", "item_name"]
                },
                "speak_during_execution": False,
                "speak_after_execution": True,
                "timeout_ms": 5000
            },
            {
                "type": "custom",
                "name": "update_cart_item",
                "description": "Update the quantity of an item already in the cart. Call when customer says 'make that 2' or 'actually 3 of those'. This REPLACES the quantity.",
                "url": f"{base_url}/update_cart_item",
                "method": "POST",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "restaurant_id": {
                            "type": "integer",
                            "description": f"The restaurant ID. Always use {restaurant_id}."
                        },
                        "session_id": {
                            "type": "string",
                            "description": "Your unique 8-char session ID generated at conversation start. REQUIRED."
                        },
                        "item_name": {
                            "type": "string",
                            "description": "Name of the item to update"
                        },
                        "quantity": {
                            "type": "integer",
                            "description": "New quantity (replaces old quantity, does not add)"
                        }
                    },
                    "required": ["restaurant_id", "session_id", "item_name", "quantity"]
                },
                "speak_during_execution": False,
                "speak_after_execution": True,
                "timeout_ms": 5000
            },
            {
                "type": "custom",
                "name": "remove_from_cart",
                "description": "Remove an item from the order. Call when customer wants to remove something. The response includes a 'message' field with confirmation.",
                "url": f"{base_url}/remove_from_cart",
                "method": "POST",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "restaurant_id": {
                            "type": "integer",
                            "description": f"The restaurant ID. Always use {restaurant_id}."
                        },
                        "session_id": {
                            "type": "string",
                            "description": "Your unique 8-char session ID generated at conversation start. REQUIRED."
                        },
                        "item_name": {
                            "type": "string",
                            "description": "Name of the item to remove"
                        }
                    },
                    "required": ["restaurant_id", "session_id", "item_name"]
                },
                "speak_during_execution": False,
                "speak_after_execution": True,
                "timeout_ms": 5000
            },
            {
                "type": "custom",
                "name": "clear_cart",
                "description": "Clear all items from the cart. Call when customer says 'start over' or 'cancel everything' or wants to restart their order.",
                "url": f"{base_url}/clear_cart",
                "method": "POST",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "restaurant_id": {
                            "type": "integer",
                            "description": f"The restaurant ID. Always use {restaurant_id}."
                        },
                        "session_id": {
                            "type": "string",
                            "description": "Your unique 8-char session ID generated at conversation start. REQUIRED."
                        }
                    },
                    "required": ["restaurant_id", "session_id"]
                },
                "speak_during_execution": False,
                "speak_after_execution": True,
                "timeout_ms": 3000
            },
            {
                "type": "custom",
                "name": "get_cart",
                "description": "Get current cart contents and total. Call when customer asks what's in their order. The response includes a 'message' field with cart summary.",
                "url": f"{base_url}/get_cart",
                "method": "POST",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "restaurant_id": {
                            "type": "integer",
                            "description": f"The restaurant ID. Always use {restaurant_id}."
                        },
                        "session_id": {
                            "type": "string",
                            "description": "Your unique 8-char session ID generated at conversation start. REQUIRED."
                        }
                    },
                    "required": ["restaurant_id", "session_id"]
                },
                "speak_during_execution": False,
                "speak_after_execution": True,
                "timeout_ms": 5000
            },
            {
                "type": "custom",
                "name": "create_order",
                "description": "Finalize the order. Call ONLY when you have both customer name AND pickup time. The response includes a 'message' field with order confirmation.",
                "url": f"{base_url}/create_order",
                "method": "POST",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "restaurant_id": {
                            "type": "integer",
                            "description": f"The restaurant ID. Always use {restaurant_id}."
                        },
                        "session_id": {
                            "type": "string",
                            "description": "Your unique 8-char session ID generated at conversation start. REQUIRED."
                        },
                        "customer_name": {
                            "type": "string",
                            "description": "Customer's name for the order"
                        },
                        "pickup_time": {
                            "type": "string",
                            "description": "When to pick up (e.g., 'ASAP', '30 minutes', '6 PM')"
                        }
                    },
                    "required": ["restaurant_id", "session_id", "customer_name", "pickup_time"]
                },
                "speak_during_execution": False,
                "speak_after_execution": True,
                "timeout_ms": 10000
            },
            {
                "type": "custom",
                "name": "get_hours",
                "description": "Get restaurant operating hours. Call when customer asks about hours. The response includes a 'message' field with hours info.",
                "url": f"{base_url}/get_hours",
                "method": "POST",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "restaurant_id": {
                            "type": "integer",
                            "description": f"The restaurant ID. Always use {restaurant_id}."
                        }
                    },
                    "required": ["restaurant_id"]
                },
                "speak_during_execution": False,
                "speak_after_execution": True,
                "timeout_ms": 3000
            },
            {
                "type": "custom",
                "name": "cancel_order",
                "description": "Cancel a pending order. Call when customer wants to cancel an existing order. Ask for their name first. The response includes a 'message' field with confirmation or error.",
                "url": f"{base_url}/cancel_order",
                "method": "POST",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "restaurant_id": {
                            "type": "integer",
                            "description": f"The restaurant ID. Always use {restaurant_id}."
                        },
                        "customer_name": {
                            "type": "string",
                            "description": "Customer's name from the original order"
                        }
                    },
                    "required": ["restaurant_id", "customer_name"]
                },
                "speak_during_execution": False,
                "speak_after_execution": True,
                "timeout_ms": 5000
            },
            {
                "type": "custom",
                "name": "initiate_payment_collection",
                "description": "Start card payment collection via phone keypad. Call when customer wants to pay by card. Returns a prompt asking customer to enter card number.",
                "url": f"{base_url}/initiate_payment_collection",
                "method": "POST",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "restaurant_id": {
                            "type": "integer",
                            "description": f"The restaurant ID. Always use {restaurant_id}."
                        },
                        "session_id": {
                            "type": "string",
                            "description": "Your unique 8-char session ID generated at conversation start. REQUIRED."
                        }
                    },
                    "required": ["restaurant_id", "session_id"]
                },
                "speak_during_execution": False,
                "speak_after_execution": True,
                "timeout_ms": 5000
            },
            {
                "type": "custom",
                "name": "process_dtmf_input",
                "description": "Process digits entered by customer on phone keypad. Call after customer enters card number, expiry, or CVV. The response tells you the next step.",
                "url": f"{base_url}/process_dtmf_input",
                "method": "POST",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "restaurant_id": {
                            "type": "integer",
                            "description": f"The restaurant ID. Always use {restaurant_id}."
                        },
                        "session_id": {
                            "type": "string",
                            "description": "Your unique 8-char session ID generated at conversation start. REQUIRED."
                        },
                        "digits": {
                            "type": "string",
                            "description": "The digits entered by customer via phone keypad (DTMF tones)"
                        }
                    },
                    "required": ["restaurant_id", "session_id", "digits"]
                },
                "speak_during_execution": False,
                "speak_after_execution": True,
                "timeout_ms": 30000
            },
            {
                "type": "custom",
                "name": "retry_payment",
                "description": "Reset payment to try a different card. Call if customer wants to try another card after a declined payment.",
                "url": f"{base_url}/retry_payment",
                "method": "POST",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "restaurant_id": {
                            "type": "integer",
                            "description": f"The restaurant ID. Always use {restaurant_id}."
                        },
                        "session_id": {
                            "type": "string",
                            "description": "Your unique 8-char session ID generated at conversation start. REQUIRED."
                        }
                    },
                    "required": ["restaurant_id", "session_id"]
                },
                "speak_during_execution": False,
                "speak_after_execution": True,
                "timeout_ms": 5000
            },
            {
                "type": "custom",
                "name": "cancel_payment",
                "description": "Cancel card payment and switch to pay-at-pickup. Call if customer doesn't want to pay by card.",
                "url": f"{base_url}/cancel_payment",
                "method": "POST",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "restaurant_id": {
                            "type": "integer",
                            "description": f"The restaurant ID. Always use {restaurant_id}."
                        },
                        "session_id": {
                            "type": "string",
                            "description": "Your unique 8-char session ID generated at conversation start. REQUIRED."
                        }
                    },
                    "required": ["restaurant_id", "session_id"]
                },
                "speak_during_execution": False,
                "speak_after_execution": True,
                "timeout_ms": 5000
            },
            {
                "type": "end_call",
                "name": "end_call",
                "description": "End the call. Use when customer says goodbye or conversation is complete."
            }
        ]

    async def create_llm(
        self,
        restaurant_name: str = "the restaurant",
        restaurant_id: int = None,
        model: str = "gpt-4o-mini"
    ) -> Optional[Dict[str, Any]]:
        """
        Create a Retell LLM configuration with function calling.

        Args:
            restaurant_name: Name of the restaurant for personalization
            restaurant_id: Restaurant ID for function calls
            model: LLM model to use (gpt-4o-mini, gpt-4o, claude-3-5-sonnet, etc.)

        Returns:
            LLM configuration including llm_id, or None if failed
        """
        if not self.enabled:
            logger.error("Retell LLM service not enabled")
            return None

        payload = {
            "model": model,
            "general_prompt": self._get_system_prompt(restaurant_name, restaurant_id),
            "begin_message": f"Hi, thanks for calling {restaurant_name}. What can I get for you today?",
            "general_tools": self._get_tools_config(restaurant_id),
            "default_dynamic_variables": {
                "restaurant_name": restaurant_name,
                "restaurant_id": str(restaurant_id) if restaurant_id else ""
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/create-retell-llm",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )

                if response.status_code == 201:
                    llm_config = response.json()
                    logger.info(f"Created Retell LLM: {llm_config.get('llm_id')}")
                    return llm_config
                else:
                    logger.error(f"Failed to create Retell LLM: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"Error creating Retell LLM: {e}")
            return None

    async def update_llm(
        self,
        llm_id: str,
        restaurant_name: str = None,
        restaurant_id: int = None,
        model: str = None
    ) -> Optional[Dict[str, Any]]:
        """Update an existing Retell LLM configuration."""
        if not self.enabled:
            return None

        payload = {}
        if restaurant_name:
            payload["general_prompt"] = self._get_system_prompt(restaurant_name, restaurant_id)
            payload["begin_message"] = f"Hi, thanks for calling {restaurant_name}. What can I get for you today?"
        if model:
            payload["model"] = model

        # Always update tools in case PUBLIC_URL changed or new tools added
        payload["general_tools"] = self._get_tools_config(restaurant_id)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.BASE_URL}/update-retell-llm/{llm_id}",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to update Retell LLM: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Error updating Retell LLM: {e}")
            return None

    async def get_llm(self, llm_id: str) -> Optional[Dict[str, Any]]:
        """Get Retell LLM configuration by ID."""
        if not self.enabled:
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/get-retell-llm/{llm_id}",
                    headers=self._get_headers(),
                    timeout=30.0
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return None

        except Exception as e:
            logger.error(f"Error getting Retell LLM: {e}")
            return None

    async def delete_llm(self, llm_id: str) -> bool:
        """Delete a Retell LLM configuration."""
        if not self.enabled:
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.BASE_URL}/delete-retell-llm/{llm_id}",
                    headers=self._get_headers(),
                    timeout=30.0
                )

                return response.status_code == 204

        except Exception as e:
            logger.error(f"Error deleting Retell LLM: {e}")
            return False

    async def list_llms(self) -> List[Dict[str, Any]]:
        """List all Retell LLM configurations."""
        if not self.enabled:
            return []

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/list-retell-llms",
                    headers=self._get_headers(),
                    timeout=30.0
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return []

        except Exception as e:
            logger.error(f"Error listing Retell LLMs: {e}")
            return []


# Global service instance
retell_llm_service = RetellLLMService()
