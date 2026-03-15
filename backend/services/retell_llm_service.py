"""
Retell Native LLM Service.

Manages Retell's built-in LLM with function calling for low-latency voice interactions.
Instead of routing every message through our own LLM, Retell's LLM handles conversation
flow and only calls our backend for data operations (menu, cart, orders).
"""

import os
import json
import logging
from pathlib import Path
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

    # Path to the prompt template file (repo root)
    PROMPT_TEMPLATE_PATH = Path(__file__).parent.parent.parent / "voice-agent-prompt-template.txt"

    def _load_prompt_template(self) -> tuple[str, str]:
        """
        Load and parse the prompt template file.

        Returns:
            (begin_message, system_prompt) with {{placeholders}} intact
        """
        text = self.PROMPT_TEMPLATE_PATH.read_text()

        # Strip file header comments (### ...) but keep prompt section headers (## ...)
        lines = text.split("\n")
        content_lines = [l for l in lines if not l.startswith("###")]
        text = "\n".join(content_lines).strip()

        # Split on the two section markers
        begin_message = ""
        system_prompt = text

        if "--- BEGIN MESSAGE ---" in text and "--- SYSTEM PROMPT ---" in text:
            parts = text.split("--- SYSTEM PROMPT ---", 1)
            begin_part = parts[0].split("--- BEGIN MESSAGE ---", 1)[1].strip()
            begin_message = begin_part
            system_prompt = parts[1].strip()

        return begin_message, system_prompt

    def _get_begin_message(self, restaurant_name: str = "the restaurant") -> str:
        """Get the begin message with placeholders filled in."""
        begin_message, _ = self._load_prompt_template()
        return self._fill_placeholders(begin_message, restaurant_name)

    def _get_system_prompt(self, restaurant_name: str = "the restaurant", restaurant_id: int = None) -> str:
        """
        Get the system prompt for Retell's native LLM.
        Reads from voice-agent-prompt-template.txt and fills in placeholders.
        """
        _, system_prompt = self._load_prompt_template()
        return self._fill_placeholders(system_prompt, restaurant_name, restaurant_id)

    @staticmethod
    def _fill_placeholders(text: str, restaurant_name: str = "the restaurant", restaurant_id: int = None) -> str:
        """Replace {{PLACEHOLDER}} tokens with actual values."""
        text = text.replace("{{RESTAURANT_NAME}}", restaurant_name)
        text = text.replace("{{RESTAURANT_ID}}", str(restaurant_id) if restaurant_id else "")
        return text

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
                            "description": "Session ID. Always pass \"default\"."
                        },
                        "item_name": {
                            "type": "string",
                            "description": "Name of the menu item"
                        },
                        "quantity": {
                            "type": "integer",
                            "description": "Quantity to order (default 1)"
                        },
                        "size": {
                            "type": "string",
                            "description": "Size of the item if applicable (e.g., 'Small', 'Medium', 'Large'). Only include if the customer specified a size."
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
                            "description": "Session ID. Always pass \"default\"."
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
                            "description": "Session ID. Always pass \"default\"."
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
                            "description": "Session ID. Always pass \"default\"."
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
                            "description": "Session ID. Always pass \"default\"."
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
                            "description": "Session ID. Always pass \"default\"."
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
                "name": "check_customer",
                "description": "Check if the caller is a returning customer. Call this FIRST at the start of every conversation. Returns customer name and last order if they've ordered before.",
                "url": f"{base_url}/check_customer",
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
                "timeout_ms": 5000
            },
            {
                "type": "transfer_call",
                "name": "transfer_call",
                "description": "Transfer the call to restaurant staff. Use when customer is upset, asks for a manager, or has a complaint you can't resolve.",
                "transfer_destination": {
                    "type": "predefined",
                    "number": "{{owner_phone}}"
                },
                "transfer_option": {
                    "type": "cold_transfer",
                    "show_transferee_as_caller": False
                }
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
        model: str = "gpt-4o-mini",
        owner_phone: str = None
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
            "begin_message": self._get_begin_message(restaurant_name),
            "general_tools": self._get_tools_config(restaurant_id),
            "default_dynamic_variables": {
                "restaurant_name": restaurant_name,
                "restaurant_id": str(restaurant_id) if restaurant_id else "",
                "owner_phone": owner_phone or ""
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
        model: str = None,
        owner_phone: str = None
    ) -> Optional[Dict[str, Any]]:
        """Update an existing Retell LLM configuration."""
        if not self.enabled:
            return None

        payload = {}
        if restaurant_name:
            payload["general_prompt"] = self._get_system_prompt(restaurant_name, restaurant_id)
            payload["begin_message"] = self._get_begin_message(restaurant_name)
        if model:
            payload["model"] = model

        # Always update tools in case PUBLIC_URL changed or new tools added
        payload["general_tools"] = self._get_tools_config(restaurant_id)

        # Update dynamic variables if provided
        if restaurant_name or owner_phone:
            payload["default_dynamic_variables"] = {
                "restaurant_name": restaurant_name or "",
                "restaurant_id": str(restaurant_id) if restaurant_id else "",
                "owner_phone": owner_phone or ""
            }

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
