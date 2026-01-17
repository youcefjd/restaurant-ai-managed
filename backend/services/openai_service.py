"""
LLM service for conversation handling with OpenAI GPT-4o or Google Gemini.

Supports streaming responses for low-latency voice interactions.
Default provider is Google Gemini Flash-Lite (cheaper), with OpenAI GPT-4o as fallback.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, AsyncGenerator, List
from datetime import datetime

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai = None

from backend.core.logging import setup_logging

logger = setup_logging(__name__)


class LLMService:
    """Service for LLM conversation handling with OpenAI or Gemini."""

    def __init__(self):
        """Initialize LLM service with provider selection. Defaults to Gemini with OpenAI as fallback."""
        self.provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.gemini_api_key = os.getenv("GOOGLE_AI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
        
        # Initialize provider clients
        self.openai_client = None
        self.gemini_client = None
        self.openai_enabled = False
        self.gemini_enabled = False
        self.enabled = False

        # Try to initialize Gemini (primary/default)
        if GEMINI_AVAILABLE and self.gemini_api_key:
            try:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_client = genai.GenerativeModel(self.gemini_model)
                self.gemini_enabled = True
                logger.info(f"Gemini LLM service initialized with model: {self.gemini_model} (default)")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini client: {str(e)}")
                self.gemini_enabled = False

        # Try to initialize OpenAI (fallback)
        if OPENAI_AVAILABLE and self.openai_api_key:
            try:
                self.openai_client = AsyncOpenAI(api_key=self.openai_api_key)
                self.openai_enabled = True
                logger.info(f"OpenAI LLM service initialized with model: {self.openai_model} (fallback)")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {str(e)}")
                self.openai_enabled = False

        # Set enabled status based on provider preference
        if self.provider == "gemini":
            self.enabled = self.gemini_enabled or self.openai_enabled
            if not self.gemini_enabled and self.openai_enabled:
                logger.warning("Gemini not available, using OpenAI as fallback")
        elif self.provider == "openai":
            self.enabled = self.openai_enabled or self.gemini_enabled
            if not self.openai_enabled and self.gemini_enabled:
                logger.warning("OpenAI not available, using Gemini as fallback")
        else:
            self.enabled = self.gemini_enabled or self.openai_enabled
        
        if not self.enabled:
            logger.error("No LLM service available - both Gemini and OpenAI failed to initialize")

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
            system_prompt: System prompt with instructions and context
            user_message: User's message
            conversation_history: Previous conversation messages (optional)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response

        Yields:
            Response text chunks as they're generated
        """
        if not self.enabled:
            error_msg = f"LLM service is disabled - provider: {self.provider}"
            logger.error(error_msg)
            yield f"Error: {error_msg}"
            return

        try:
            # Try primary provider first (Gemini by default)
            if self.provider == "gemini":
                if self.gemini_enabled and self.gemini_client:
                    try:
                        async for chunk in self._generate_gemini_response(
                            system_prompt, user_message, conversation_history, temperature, max_tokens
                        ):
                            yield chunk
                        return  # Success, exit
                    except Exception as e:
                        logger.warning(f"Gemini generation failed: {str(e)}, trying OpenAI fallback")
                        # Fall through to OpenAI fallback
                
                # Fallback to OpenAI
                if self.openai_enabled and self.openai_client:
                    logger.info("Using OpenAI as fallback")
                    async for chunk in self._generate_openai_response(
                        system_prompt, user_message, conversation_history, temperature, max_tokens
                    ):
                        yield chunk
                    return
            
            elif self.provider == "openai":
                if self.openai_enabled and self.openai_client:
                    try:
                        async for chunk in self._generate_openai_response(
                            system_prompt, user_message, conversation_history, temperature, max_tokens
                        ):
                            yield chunk
                        return  # Success, exit
                    except Exception as e:
                        logger.warning(f"OpenAI generation failed: {str(e)}, trying Gemini fallback")
                        # Fall through to Gemini fallback
                
                # Fallback to Gemini
                if self.gemini_enabled and self.gemini_client:
                    logger.info("Using Gemini as fallback")
                    async for chunk in self._generate_gemini_response(
                        system_prompt, user_message, conversation_history, temperature, max_tokens
                    ):
                        yield chunk
                    return
            
            # Both providers failed or not available
            error_msg = "No LLM provider available - both Gemini and OpenAI failed"
            logger.error(error_msg)
            yield f"Error: {error_msg}"
            
        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}", exc_info=True)
            yield f"Error: Failed to generate response - {str(e)}"

    async def _generate_openai_response(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]],
        temperature: float,
        max_tokens: int
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response from OpenAI."""
        try:
            # Build messages list
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})

            # Stream response from OpenAI
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

        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}", exc_info=True)
            yield f"Error: OpenAI API error - {str(e)}"

    async def _generate_gemini_response(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]],
        temperature: float,
        max_tokens: int
    ) -> AsyncGenerator[str, None]:
        """Generate streaming response from Gemini."""
        try:
            # Build full prompt with system prompt and conversation history
            full_prompt = f"{system_prompt}\n\n"
            
            if conversation_history:
                for msg in conversation_history:
                    role = "User" if msg.get("role") == "user" else "Assistant"
                    full_prompt += f"{role}: {msg.get('content', '')}\n\n"
            
            full_prompt += f"User: {user_message}\nAssistant:"

            # Stream response from Gemini
            response = await self.gemini_client.generate_content_async(
                full_prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                },
                stream=True
            )

            async for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}", exc_info=True)
            yield f"Error: Gemini API error - {str(e)}"

    async def generate_complete_response(
        self,
        system_prompt: str,
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 512
    ) -> str:
        """
        Generate complete response (non-streaming).

        Args:
            system_prompt: System prompt with instructions and context
            user_message: User's message
            conversation_history: Previous conversation messages (optional)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens in response

        Returns:
            Complete response text
        """
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
