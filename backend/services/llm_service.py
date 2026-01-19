"""
LLM service for conversation handling with Google Gemini or OpenAI GPT.

Supports streaming responses for low-latency voice interactions.
Default provider is Gemini with OpenAI as fallback.
"""

import os
import logging
import asyncio
from typing import Optional, Dict, Any, AsyncGenerator, List

from backend.core.logging import setup_logging

logger = setup_logging(__name__)

# Check for available SDKs
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None

try:
    from google import genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None


class LLMService:
    """Service for LLM conversation handling with Gemini or OpenAI."""

    def __init__(self):
        """Initialize LLM service."""
        self.provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.gemini_api_key = os.getenv("GOOGLE_AI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")

        self.openai_client = None
        self.gemini_client = None
        self.openai_enabled = False
        self.gemini_enabled = False
        self.enabled = False

        # Initialize Gemini (primary)
        if GEMINI_AVAILABLE and self.gemini_api_key:
            try:
                self.gemini_client = genai.Client(api_key=self.gemini_api_key)
                self.gemini_enabled = True
                logger.info(f"Gemini initialized with model: {self.gemini_model}")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini: {e}")

        # Initialize OpenAI (fallback)
        if OPENAI_AVAILABLE and self.openai_api_key:
            try:
                self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
                self.openai_enabled = True
                logger.info(f"OpenAI initialized with model: {self.openai_model}")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")

        # Set enabled status
        if self.provider == "gemini":
            self.enabled = self.gemini_enabled or self.openai_enabled
        else:
            self.enabled = self.openai_enabled or self.gemini_enabled

        if not self.enabled:
            logger.error("No LLM service available")

    async def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 512
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming response from LLM.

        Args:
            system_prompt: System prompt with instructions
            user_message: User's message
            conversation_history: Previous messages (optional)
            temperature: Sampling temperature
            max_tokens: Maximum response tokens

        Yields:
            Response text chunks
        """
        if not self.enabled:
            yield "I'm sorry, the AI service is temporarily unavailable."
            return

        # Try primary provider
        if self.provider == "gemini" and self.gemini_enabled:
            try:
                async for chunk in self._generate_gemini(
                    system_prompt, user_message, conversation_history, temperature, max_tokens
                ):
                    yield chunk
                return
            except Exception as e:
                logger.warning(f"Gemini failed, trying OpenAI: {e}")

        # Fallback to OpenAI
        if self.openai_enabled:
            try:
                async for chunk in self._generate_openai(
                    system_prompt, user_message, conversation_history, temperature, max_tokens
                ):
                    yield chunk
                return
            except Exception as e:
                logger.error(f"OpenAI failed: {e}")

        # Try Gemini as last resort if OpenAI was primary
        if self.provider == "openai" and self.gemini_enabled:
            try:
                async for chunk in self._generate_gemini(
                    system_prompt, user_message, conversation_history, temperature, max_tokens
                ):
                    yield chunk
                return
            except Exception as e:
                logger.error(f"Gemini fallback failed: {e}")

        yield "I'm sorry, I'm having trouble right now. Please try again."

    async def _generate_openai(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]],
        temperature: float,
        max_tokens: int
    ) -> AsyncGenerator[str, None]:
        """Generate response using OpenAI."""
        messages = [{"role": "system", "content": system_prompt}]

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": user_message})

        stream = await self.openai_client.chat.completions.create(
            model=self.openai_model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def _generate_gemini(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]],
        temperature: float,
        max_tokens: int
    ) -> AsyncGenerator[str, None]:
        """Generate response using Gemini."""
        # Build prompt
        full_prompt = f"{system_prompt}\n\n"

        if conversation_history:
            logger.info(f"Including {len(conversation_history)} messages in conversation history")
            for msg in conversation_history:
                role = "User" if msg.get("role") == "user" else "Assistant"
                full_prompt += f"{role}: {msg.get('content', '')}\n\n"

        full_prompt += f"User: {user_message}\nAssistant:"

        # Generate response (run in thread pool to avoid blocking event loop)
        def _generate():
            return self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=full_prompt,
                config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                }
            )

        response = await asyncio.to_thread(_generate)

        # Extract text from response
        logger.debug(f"Raw Gemini response object: {response}")
        text = self._extract_gemini_text(response)
        if text:
            logger.info(f"Gemini response length: {len(text)} chars")
            yield text
        else:
            logger.warning("No text extracted from Gemini response")

    def _extract_gemini_text(self, response) -> Optional[str]:
        """Extract text from Gemini response."""
        try:
            # Log finish reason if available
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'finish_reason'):
                        logger.info(f"Gemini finish_reason: {candidate.finish_reason}")

            # Try direct text property
            if hasattr(response, 'text') and response.text:
                return response.text

            # Try candidates structure
            if hasattr(response, 'candidates') and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            for part in candidate.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    return part.text

            logger.warning(f"No text found in Gemini response: {response}")
            return None
        except Exception as e:
            logger.error(f"Error extracting Gemini text: {e}")
            return None

    async def generate_complete_response(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 512
    ) -> str:
        """Generate complete (non-streaming) response."""
        response_text = ""
        async for chunk in self.generate_response(
            system_prompt, user_message, conversation_history, temperature, max_tokens
        ):
            response_text += chunk
        return response_text

    def is_enabled(self) -> bool:
        """Check if LLM service is enabled."""
        return self.enabled

    def get_provider(self) -> str:
        """Get current LLM provider."""
        return self.provider

    def get_available_providers(self) -> Dict[str, bool]:
        """Get status of available providers."""
        return {
            "gemini": self.gemini_enabled,
            "openai": self.openai_enabled,
            "enabled": self.enabled
        }


# Global LLM service instance
llm_service = LLMService()
