"""
Retell AI Service for voice and SMS integration.

Retell AI provides an all-in-one voice AI platform with:
- Natural-sounding voices with low latency
- Custom LLM integration via WebSocket
- Phone number management
- SMS capabilities

Docs: https://docs.retellai.com
"""

import os
import json
import hmac
import hashlib
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)


class RetellService:
    """Service for interacting with Retell AI API."""

    BASE_URL = "https://api.retellai.com"

    def __init__(self):
        """Initialize Retell service with API key."""
        self.api_key = os.getenv("RETELL_API_KEY")
        self.enabled = bool(self.api_key)

        if self.enabled:
            logger.info("Retell AI service initialized")
        else:
            logger.warning("RETELL_API_KEY not set - Retell service disabled")

    def is_enabled(self) -> bool:
        """Check if Retell service is enabled."""
        return self.enabled

    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        api_key: Optional[str] = None
    ) -> bool:
        """
        Verify webhook signature from Retell.

        Args:
            payload: Raw request body bytes
            signature: X-Retell-Signature header value
            api_key: API key to use for verification (defaults to self.api_key)

        Returns:
            True if signature is valid
        """
        key = api_key or self.api_key
        if not key:
            return False

        expected = hmac.new(
            key.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected, signature)

    # ==================== Agent Management ====================

    async def create_agent(
        self,
        name: str,
        voice_id: str = "11labs-Adrian",
        llm_websocket_url: str = None,
        system_prompt: str = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new Retell agent.

        Args:
            name: Agent name
            voice_id: Voice ID (default: 11labs-Adrian)
            llm_websocket_url: WebSocket URL for custom LLM
            system_prompt: System prompt for built-in LLM
            **kwargs: Additional agent configuration

        Returns:
            Agent object or None if failed
        """
        if not self.enabled:
            logger.error("Retell service not enabled")
            return None

        payload = {
            "agent_name": name,
            "voice_id": voice_id,
            **kwargs
        }

        # Use custom LLM or Retell's built-in LLM
        if llm_websocket_url:
            payload["response_engine"] = {
                "type": "custom-llm",
                "llm_websocket_url": llm_websocket_url
            }
        elif system_prompt:
            payload["response_engine"] = {
                "type": "retell-llm",
                "llm_id": kwargs.get("llm_id")
            }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/create-agent",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )

                if response.status_code == 201:
                    agent = response.json()
                    logger.info(f"Created Retell agent: {agent.get('agent_id')}")
                    return agent
                else:
                    logger.error(f"Failed to create agent: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"Error creating Retell agent: {e}")
            return None

    async def get_agent(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent by ID."""
        if not self.enabled:
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/get-agent/{agent_id}",
                    headers=self._get_headers(),
                    timeout=30.0
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to get agent: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Error getting Retell agent: {e}")
            return None

    async def update_agent(
        self,
        agent_id: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Update an existing agent."""
        if not self.enabled:
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.BASE_URL}/update-agent/{agent_id}",
                    headers=self._get_headers(),
                    json=kwargs,
                    timeout=30.0
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to update agent: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Error updating Retell agent: {e}")
            return None

    async def list_agents(self) -> List[Dict[str, Any]]:
        """List all agents."""
        if not self.enabled:
            return []

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/list-agents",
                    headers=self._get_headers(),
                    timeout=30.0
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to list agents: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"Error listing Retell agents: {e}")
            return []

    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent."""
        if not self.enabled:
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.BASE_URL}/delete-agent/{agent_id}",
                    headers=self._get_headers(),
                    timeout=30.0
                )

                if response.status_code == 204:
                    logger.info(f"Deleted Retell agent: {agent_id}")
                    return True
                else:
                    logger.error(f"Failed to delete agent: {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"Error deleting Retell agent: {e}")
            return False

    # ==================== Phone Number Management ====================

    async def create_phone_number(
        self,
        area_code: int = 415,
        agent_id: str = None,
        nickname: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Purchase a new phone number from Retell.

        Args:
            area_code: Area code for the number (default: 415)
            agent_id: Agent to bind to this number for inbound calls
            nickname: Friendly name for the number

        Returns:
            Phone number object or None
        """
        if not self.enabled:
            return None

        payload = {"area_code": area_code}
        if agent_id:
            payload["inbound_agent_id"] = agent_id
        if nickname:
            payload["nickname"] = nickname

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/create-phone-number",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )

                if response.status_code == 201:
                    phone = response.json()
                    logger.info(f"Created Retell phone number: {phone.get('phone_number')}")
                    return phone
                else:
                    logger.error(f"Failed to create phone number: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"Error creating Retell phone number: {e}")
            return None

    async def import_phone_number(
        self,
        phone_number: str,
        twilio_account_sid: str,
        twilio_auth_token: str,
        agent_id: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Import an existing Twilio phone number to Retell.

        Args:
            phone_number: E.164 format phone number
            twilio_account_sid: Twilio account SID
            twilio_auth_token: Twilio auth token
            agent_id: Agent to bind for inbound calls

        Returns:
            Phone number object or None
        """
        if not self.enabled:
            return None

        payload = {
            "phone_number": phone_number,
            "telephony_credential": {
                "twilio_account_sid": twilio_account_sid,
                "twilio_auth_token": twilio_auth_token
            }
        }
        if agent_id:
            payload["inbound_agent_id"] = agent_id

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/import-phone-number",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )

                if response.status_code == 201:
                    phone = response.json()
                    logger.info(f"Imported phone number to Retell: {phone_number}")
                    return phone
                else:
                    logger.error(f"Failed to import phone number: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"Error importing phone number: {e}")
            return None

    async def get_phone_number(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get phone number details."""
        if not self.enabled:
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/get-phone-number/{phone_number}",
                    headers=self._get_headers(),
                    timeout=30.0
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return None

        except Exception as e:
            logger.error(f"Error getting phone number: {e}")
            return None

    async def update_phone_number(
        self,
        phone_number: str,
        agent_id: str = None,
        nickname: str = None
    ) -> Optional[Dict[str, Any]]:
        """Update phone number configuration."""
        if not self.enabled:
            return None

        payload = {}
        if agent_id is not None:
            payload["inbound_agent_id"] = agent_id
        if nickname is not None:
            payload["nickname"] = nickname

        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.BASE_URL}/update-phone-number/{phone_number}",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to update phone number: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Error updating phone number: {e}")
            return None

    async def list_phone_numbers(self) -> List[Dict[str, Any]]:
        """List all phone numbers."""
        if not self.enabled:
            return []

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/list-phone-numbers",
                    headers=self._get_headers(),
                    timeout=30.0
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return []

        except Exception as e:
            logger.error(f"Error listing phone numbers: {e}")
            return []

    # ==================== Call Management ====================

    async def create_phone_call(
        self,
        from_number: str,
        to_number: str,
        agent_id: str = None,
        metadata: Dict[str, Any] = None,
        retell_llm_dynamic_variables: Dict[str, str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create an outbound phone call.

        Args:
            from_number: Retell phone number (E.164)
            to_number: Destination number (E.164)
            agent_id: Override agent for this call
            metadata: Custom metadata for the call
            retell_llm_dynamic_variables: Variables to inject into prompts

        Returns:
            Call object or None
        """
        if not self.enabled:
            return None

        payload = {
            "from_number": from_number,
            "to_number": to_number
        }
        if agent_id:
            payload["override_agent_id"] = agent_id
        if metadata:
            payload["metadata"] = metadata
        if retell_llm_dynamic_variables:
            payload["retell_llm_dynamic_variables"] = retell_llm_dynamic_variables

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/create-phone-call",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )

                if response.status_code == 201:
                    call = response.json()
                    logger.info(f"Created outbound call: {call.get('call_id')}")
                    return call
                else:
                    logger.error(f"Failed to create call: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"Error creating call: {e}")
            return None

    async def get_call(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get call details."""
        if not self.enabled:
            return None

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/get-call/{call_id}",
                    headers=self._get_headers(),
                    timeout=30.0
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return None

        except Exception as e:
            logger.error(f"Error getting call: {e}")
            return None

    async def list_calls(
        self,
        filter_criteria: Dict[str, Any] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List calls with optional filtering."""
        if not self.enabled:
            return []

        params = {"limit": limit}
        if filter_criteria:
            params["filter_criteria"] = json.dumps(filter_criteria)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/list-calls",
                    headers=self._get_headers(),
                    params=params,
                    timeout=30.0
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return []

        except Exception as e:
            logger.error(f"Error listing calls: {e}")
            return []

    # ==================== SMS Management ====================

    async def create_sms_chat(
        self,
        from_number: str,
        to_number: str,
        agent_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Start an outbound SMS conversation.

        The initial message will be auto-generated by the agent.

        Args:
            from_number: Retell phone number with SMS capability (E.164)
            to_number: Destination number (E.164)
            agent_id: Override agent for this chat
            metadata: Custom metadata

        Returns:
            Chat object or None
        """
        if not self.enabled:
            return None

        payload = {
            "from_number": from_number,
            "to_number": to_number
        }
        if agent_id:
            payload["override_agent_id"] = agent_id
        if metadata:
            payload["metadata"] = metadata

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/create-sms-chat",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )

                if response.status_code == 201:
                    chat = response.json()
                    logger.info(f"Created SMS chat: {chat.get('chat_id')}")
                    return chat
                else:
                    logger.error(f"Failed to create SMS chat: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"Error creating SMS chat: {e}")
            return None

    async def send_sms(
        self,
        from_number: str,
        to_number: str,
        message: str
    ) -> Optional[Dict[str, Any]]:
        """
        Send a one-way SMS message.

        Args:
            from_number: Retell phone number (E.164)
            to_number: Destination number (E.164)
            message: Text message content

        Returns:
            Response or None
        """
        if not self.enabled:
            return None

        payload = {
            "from_number": from_number,
            "to_number": to_number,
            "message": message
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/send-sms",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30.0
                )

                if response.status_code in [200, 201]:
                    logger.info(f"Sent SMS from {from_number} to {to_number}")
                    return response.json() if response.text else {"status": "sent"}
                else:
                    logger.error(f"Failed to send SMS: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return None


# Global service instance
retell_service = RetellService()
