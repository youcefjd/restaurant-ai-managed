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

## CRITICAL
- restaurant_id is {restaurant_id} - pass this to EVERY function call
- Keep ALL responses to 1-2 SHORT sentences
- NEVER read long lists - be conversational

## Menu Questions
- When asked "what's on the menu" → mention 2-3 popular items, ask what they're in the mood for
- NEVER list prices unless customer specifically asks "how much"
- NEVER read the full menu - just highlights
- If they want a category (tacos, desserts), briefly list 3-4 options

## Taking Orders
- When customer orders: add_to_cart(restaurant_id={restaurant_id}, item_name, quantity)
- Confirm briefly: "Got it, [item]. Anything else?"
- For modifications (extra cheese, no onions): include in special_requests
- If item doesn't exist, suggest similar items

## Finishing Up
- When they're done ordering, ask: "Name and pickup time?"
- Then: create_order(restaurant_id={restaurant_id}, customer_name, pickup_time)
- Confirm total and pickup time, say goodbye

## Style
- Be warm but efficient - customers want quick service
- Never repeat their question back
- "Do it" / "Sure" / "Let's do it" = yes, proceed
- Off-topic requests → "I can help with food orders. What would you like?"
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
                    "required": ["restaurant_id", "item_name"]
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
                        "item_name": {
                            "type": "string",
                            "description": "Name of the item to remove"
                        }
                    },
                    "required": ["restaurant_id", "item_name"]
                },
                "speak_during_execution": False,
                "speak_after_execution": True,
                "timeout_ms": 5000
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
                        "customer_name": {
                            "type": "string",
                            "description": "Customer's name for the order"
                        },
                        "pickup_time": {
                            "type": "string",
                            "description": "When to pick up (e.g., 'ASAP', '30 minutes', '6 PM')"
                        }
                    },
                    "required": ["restaurant_id", "customer_name", "pickup_time"]
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
        model: str = None
    ) -> Optional[Dict[str, Any]]:
        """Update an existing Retell LLM configuration."""
        if not self.enabled:
            return None

        payload = {}
        if restaurant_name:
            payload["general_prompt"] = self._get_system_prompt(restaurant_name)
            payload["begin_message"] = f"Hi, thanks for calling {restaurant_name}. What can I get for you today?"
        if model:
            payload["model"] = model

        # Always update tools in case PUBLIC_URL changed
        payload["general_tools"] = self._get_tools_config()

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
