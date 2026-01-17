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
    # #region agent log
    import json; _log_f = open('/Users/simon/Documents/code/.cursor/debug.log', 'a'); _log_f.write(json.dumps({'sessionId': 'debug-session', 'runId': 'migration-v2', 'hypothesisId': 'A', 'location': 'llm_service.py:21', 'message': 'Before google.genai import', 'data': {}, 'timestamp': __import__('time').time() * 1000}) + '\n'); _log_f.close()
    # #endregion
    from google import genai
    # #region agent log
    _log_f = open('/Users/simon/Documents/code/.cursor/debug.log', 'a'); _log_f.write(json.dumps({'sessionId': 'debug-session', 'runId': 'migration-v2', 'hypothesisId': 'A', 'location': 'llm_service.py:25', 'message': 'Import success, checking Client class', 'data': {'has_client': hasattr(genai, 'Client'), 'has_configure': hasattr(genai, 'configure'), 'has_generative_model': hasattr(genai, 'GenerativeModel')}, 'timestamp': __import__('time').time() * 1000}) + '\n'); _log_f.close()
    # #endregion
    GEMINI_AVAILABLE = True
except ImportError as e:
    # #region agent log
    _log_f = open('/Users/simon/Documents/code/.cursor/debug.log', 'a'); _log_f.write(json.dumps({'sessionId': 'debug-session', 'runId': 'migration-v2', 'hypothesisId': 'A', 'location': 'llm_service.py:30', 'message': 'Import failed', 'data': {'error': str(e)}, 'timestamp': __import__('time').time() * 1000}) + '\n'); _log_f.close()
    # #endregion
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
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        
        # Initialize provider clients
        self.openai_client = None
        self.gemini_client = None
        self.openai_enabled = False
        self.gemini_enabled = False
        self.enabled = False

        # Try to initialize Gemini (primary/default)
        if GEMINI_AVAILABLE and self.gemini_api_key:
            try:
                # Log API key info (first 10 chars + last 4 for debugging without exposing full key)
                api_key_preview = f"{self.gemini_api_key[:10]}...{self.gemini_api_key[-4:]}" if len(self.gemini_api_key) > 14 else "***"
                logger.info(f"Initializing Gemini client with API key: {api_key_preview}, requested model: {self.gemini_model}")
                
                # #region agent log
                _log_f = open('/Users/simon/Documents/code/.cursor/debug.log', 'a'); _log_f.write(json.dumps({'sessionId': 'debug-session', 'runId': 'migration-v2', 'hypothesisId': 'B', 'location': 'llm_service.py:52', 'message': 'Before Client initialization', 'data': {'model': self.gemini_model}, 'timestamp': __import__('time').time() * 1000}) + '\n'); _log_f.close()
                # #endregion
                self.gemini_client = genai.Client(api_key=self.gemini_api_key)
                # #region agent log
                _log_f = open('/Users/simon/Documents/code/.cursor/debug.log', 'a'); _log_f.write(json.dumps({'sessionId': 'debug-session', 'runId': 'migration-v2', 'hypothesisId': 'B', 'location': 'llm_service.py:56', 'message': 'After Client init', 'data': {'client_type': type(self.gemini_client).__name__, 'has_models': hasattr(self.gemini_client, 'models')}, 'timestamp': __import__('time').time() * 1000}) + '\n'); _log_f.close()
                # #endregion
                
                # Auto-select best available model if not explicitly set or if default might not exist
                # This happens asynchronously after initialization, so we'll defer model selection
                # For now, mark as enabled and we'll validate/update the model when needed
                self.gemini_enabled = True
                logger.info(f"Gemini LLM service initialized with model: {self.gemini_model} (will auto-validate on first use)")
            except Exception as e:
                # #region agent log
                _log_f = open('/Users/simon/Documents/code/.cursor/debug.log', 'a'); _log_f.write(json.dumps({'sessionId': 'debug-session', 'runId': 'migration-v2', 'hypothesisId': 'B', 'location': 'llm_service.py:62', 'message': 'Client init exception', 'data': {'error': str(e), 'error_type': type(e).__name__}, 'timestamp': __import__('time').time() * 1000}) + '\n'); _log_f.close()
                # #endregion
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

    async def _ensure_valid_gemini_model(self) -> bool:
        """
        Ensure we have a valid Gemini model. Auto-select best available if current model fails.
        
        Returns:
            True if we have a valid model, False otherwise
        """
        if not self.gemini_enabled or not self.gemini_client:
            return False
        
        # If we haven't validated the model yet, try to auto-select the best one
        if not hasattr(self, '_gemini_model_validated'):
            try:
                best_model = await self.auto_select_gemini_model()
                if best_model:
                    self.gemini_model = best_model
                    logger.info(f"Auto-selected Gemini model: {self.gemini_model}")
                self._gemini_model_validated = True
                return True
            except Exception as e:
                logger.warning(f"Failed to auto-select Gemini model: {str(e)}")
                self._gemini_model_validated = True
                return True  # Still try with default model
        
        return True

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
            # Ensure we have a valid model (auto-select if needed)
            await self._ensure_valid_gemini_model()
            # Build full prompt with system prompt and conversation history
            full_prompt = f"{system_prompt}\n\n"
            
            if conversation_history:
                for msg in conversation_history:
                    role = "User" if msg.get("role") == "user" else "Assistant"
                    full_prompt += f"{role}: {msg.get('content', '')}\n\n"
            
            full_prompt += f"User: {user_message}\nAssistant:"

            # #region agent log
            _log_f = open('/Users/simon/Documents/code/.cursor/debug.log', 'a'); _log_f.write(json.dumps({'sessionId': 'debug-session', 'runId': 'migration-v2', 'hypothesisId': 'C', 'location': 'llm_service.py:228', 'message': 'Before generate_content', 'data': {'has_models': hasattr(self.gemini_client, 'models'), 'has_generate_content': hasattr(self.gemini_client.models if hasattr(self.gemini_client, 'models') else None, 'generate_content') if self.gemini_client else False}, 'timestamp': __import__('time').time() * 1000}) + '\n'); _log_f.close()
            # #endregion

            # Stream response from Gemini using new client API
            # Note: The new API handles streaming through iterable responses
            response = self.gemini_client.models.generate_content(
                model=self.gemini_model,
                contents=full_prompt,
                config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                }
            )

            # Log response structure for debugging
            has_aiter = hasattr(response, '__aiter__')
            has_iter = hasattr(response, '__iter__') and not isinstance(response, str)
            logger.debug(f"Gemini response type: {type(response)}, has __aiter__: {has_aiter}, has __iter__: {has_iter}")
            
            # Handle streaming response - try both sync and async iteration
            text_yielded = False
            if has_aiter:
                logger.debug("Handling async iterable response")
                chunk_count = 0
                async for chunk in response:
                    chunk_count += 1
                    logger.info(f"Async chunk {chunk_count} type: {type(chunk)}, has text: {hasattr(chunk, 'text') if hasattr(chunk, '__dict__') else 'N/A'}")
                    chunk_text = None
                    if hasattr(chunk, 'text') and chunk.text:
                        chunk_text = chunk.text
                    elif isinstance(chunk, str):
                        chunk_text = chunk
                    elif hasattr(chunk, 'candidates') and chunk.candidates:
                        # Handle response chunks with candidates
                        for candidate in chunk.candidates:
                            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                                for part in candidate.content.parts:
                                    if hasattr(part, 'text') and part.text:
                                        chunk_text = part.text
                                        break
                                if chunk_text:
                                    break
                    
                    if chunk_text:
                        yield chunk_text
                        text_yielded = True
            elif has_iter:
                logger.debug("Handling sync iterable response")
                chunk_count = 0
                for chunk in response:
                    chunk_count += 1
                    chunk_text = None
                    
                    # Handle tuples - extract text from tuple structure
                    if isinstance(chunk, tuple):
                        logger.debug(f"Sync chunk {chunk_count} is tuple with length {len(chunk)}, items: {[type(i).__name__ for i in chunk]}")
                        # Tuples from Google Genai might contain (text, metadata) or (response_obj, ...)
                        for item_idx, item in enumerate(chunk):
                            if isinstance(item, str) and item.strip():
                                chunk_text = item.strip()
                                break
                            elif hasattr(item, 'text'):
                                text_val = getattr(item, 'text', None)
                                if text_val:
                                    chunk_text = str(text_val).strip()
                                    break
                            elif hasattr(item, 'content'):
                                content = getattr(item, 'content', None)
                                if content:
                                    if hasattr(content, 'parts'):
                                        parts = getattr(content, 'parts', None)
                                        if parts:
                                            for part in parts:
                                                part_text = getattr(part, 'text', None)
                                                if part_text:
                                                    chunk_text = str(part_text).strip()
                                                    break
                                    if not chunk_text and hasattr(content, 'text'):
                                        content_text = getattr(content, 'text', None)
                                        if content_text:
                                            chunk_text = str(content_text).strip()
                                            break
                    elif hasattr(chunk, 'text') and chunk.text:
                        chunk_text = chunk.text
                    elif isinstance(chunk, str):
                        chunk_text = chunk
                    elif hasattr(chunk, 'candidates') and chunk.candidates:
                        # Handle response chunks with candidates
                        for candidate in chunk.candidates:
                            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                                for part in candidate.content.parts:
                                    if hasattr(part, 'text') and part.text:
                                        chunk_text = part.text
                                        break
                                if chunk_text:
                                    break
                    
                    if chunk_text:
                        yield chunk_text
                        text_yielded = True
            else:
                # Non-streaming response
                logger.debug("Handling non-streaming response")
                chunk_text = None
                
                # Try multiple extraction strategies for GenerateContentResponse
                # Strategy 1: Direct text property (primary method) - try both property and method
                if not chunk_text:
                    try:
                        if hasattr(response, 'text'):
                            text_val = getattr(response, 'text', None)
                            # Check if it's callable (method) or a property
                            if callable(text_val):
                                text_val = text_val()
                            if text_val and (isinstance(text_val, str) or str(text_val).strip()):
                                chunk_text = str(text_val).strip()
                                if chunk_text:
                                    logger.debug("Extracted text via response.text")
                    except Exception as e:
                        logger.debug(f"Failed to access response.text: {e}")
                
                # Strategy 1b: response.content.text (alternative format)
                if not chunk_text:
                    try:
                        if hasattr(response, 'content'):
                            content = getattr(response, 'content', None)
                            if content and hasattr(content, 'text'):
                                text_val = getattr(content, 'text', None)
                                if callable(text_val):
                                    text_val = text_val()
                                if text_val and (isinstance(text_val, str) or str(text_val).strip()):
                                    chunk_text = str(text_val).strip()
                                    if chunk_text:
                                        logger.debug("Extracted text via response.content.text")
                    except Exception as e:
                        logger.debug(f"Failed to access response.content.text: {e}")
                
                # Strategy 2: Get the text from response object (new SDK might have this method)
                if not chunk_text and hasattr(response, '__str__'):
                    try:
                        str_repr = str(response)
                        # Only use if it looks like actual text, not object representation
                        if str_repr and not str_repr.startswith('<') and len(str_repr) > 0:
                            chunk_text = str_repr
                    except Exception:
                        pass
                
                # Strategy 3: Candidates structure (standard Gemini API format)
                if not chunk_text:
                    try:
                        candidates = getattr(response, 'candidates', None)
                        if candidates and len(candidates) > 0:
                            for candidate in candidates:
                                # Try content.parts[].text (most common structure)
                                if hasattr(candidate, 'content'):
                                    content = getattr(candidate, 'content', None)
                                    if content:
                                        # Try content.parts (list of parts)
                                        parts = getattr(content, 'parts', None)
                                        if parts and len(parts) > 0:
                                            for part in parts:
                                                part_text = getattr(part, 'text', None)
                                                if part_text:
                                                    text_str = str(part_text).strip()
                                                    if text_str:
                                                        chunk_text = text_str
                                                        logger.debug("Extracted text via candidates[].content.parts[].text")
                                                        break
                                            if chunk_text:
                                                break
                                        # Try content.text directly
                                        if not chunk_text:
                                            content_text = getattr(content, 'text', None)
                                            if content_text:
                                                text_str = str(content_text).strip()
                                                if text_str:
                                                    chunk_text = text_str
                                                    logger.debug("Extracted text via candidates[].content.text")
                                                    break
                                        # Try content as string
                                        if not chunk_text and isinstance(content, str) and content.strip():
                                            chunk_text = content.strip()
                                            logger.debug("Extracted text via candidates[].content (string)")
                                            break
                                # Try candidate.text directly
                                if not chunk_text and hasattr(candidate, 'text'):
                                    cand_text = getattr(candidate, 'text', None)
                                    if cand_text:
                                        text_str = str(cand_text).strip()
                                        if text_str:
                                            chunk_text = text_str
                                            logger.debug("Extracted text via candidates[].text")
                                            break
                                
                                if chunk_text:
                                    break
                    except Exception as e:
                        logger.debug(f"Failed to extract from candidates: {e}", exc_info=True)
                
                # Strategy 4: Check if response has a method to get text
                if not chunk_text:
                    for method_name in ['get_text', 'text', 'content', 'get_content']:
                        if hasattr(response, method_name):
                            try:
                                method = getattr(response, method_name)
                                if callable(method):
                                    result = method()
                                    if result:
                                        chunk_text = str(result)
                                        break
                                else:
                                    if method:
                                        chunk_text = str(method)
                                        break
                            except Exception:
                                pass
                
                # Strategy 5: Try accessing through dict-like interface
                if not chunk_text and hasattr(response, '__dict__'):
                    try:
                        for key in ['text', 'content', 'result']:
                            if hasattr(response, key):
                                val = getattr(response, key)
                                if val:
                                    chunk_text = str(val)
                                    break
                    except Exception:
                        pass
                
                # Strategy 6: Direct string conversion (last resort)
                if not chunk_text:
                    if isinstance(response, str):
                        chunk_text = response
                    else:
                        # Try converting to string as absolute last resort
                        try:
                            str_repr = str(response)
                            # Only use if it looks like actual content (not object repr)
                            # Check if it contains meaningful text (not just "<...object...>")
                            if str_repr and len(str_repr) > 10 and not str_repr.strip().startswith('<') and not str_repr.strip().startswith('google.genai'):
                                chunk_text = str_repr
                        except Exception:
                            pass
                
                if chunk_text:
                    yield chunk_text
                    text_yielded = True
                else:
                    # Log detailed info if we can't extract text - try to extract it for debugging
                    attrs = [attr for attr in dir(response) if not attr.startswith('_')]
                    logger.debug(f"Response attributes: {attrs[:20]}")
                    
                    # Try to access and log actual response structure for debugging
                    try:
                        # Try accessing text property directly
                        if hasattr(response, 'text'):
                            text_val = getattr(response, 'text', None)
                            logger.debug(f"response.text exists, value type: {type(text_val)}, value: {str(text_val)[:100] if text_val else None}")
                        
                        # Try accessing content
                        if hasattr(response, 'content'):
                            content = getattr(response, 'content', None)
                            logger.debug(f"response.content exists, type: {type(content)}")
                            if content and hasattr(content, 'text'):
                                content_text = getattr(content, 'text', None)
                                logger.debug(f"response.content.text exists, value: {str(content_text)[:100] if content_text else None}")
                        
                        # Try accessing candidates - this is the most likely structure
                        if hasattr(response, 'candidates'):
                            candidates = getattr(response, 'candidates', None)
                            logger.debug(f"response.candidates exists, type: {type(candidates)}, length: {len(candidates) if candidates else 0}")
                            if candidates and len(candidates) > 0:
                                candidate = candidates[0]
                                cand_attrs = [a for a in dir(candidate) if not a.startswith('_')]
                                logger.debug(f"First candidate type: {type(candidate)}, attributes: {cand_attrs[:15]}")
                                if hasattr(candidate, 'content'):
                                    cand_content = getattr(candidate, 'content', None)
                                    logger.debug(f"candidate.content type: {type(cand_content)}")
                                    if cand_content:
                                        cand_content_attrs = [a for a in dir(cand_content) if not a.startswith('_')]
                                        logger.debug(f"candidate.content attributes: {cand_content_attrs[:15]}")
                                        if hasattr(cand_content, 'parts'):
                                            parts = getattr(cand_content, 'parts', None)
                                            logger.debug(f"candidate.content.parts exists, type: {type(parts)}, length: {len(parts) if parts else 0}")
                                            if parts and len(parts) > 0:
                                                part = parts[0]
                                                part_attrs = [a for a in dir(part) if not a.startswith('_')]
                                                logger.debug(f"First part type: {type(part)}, attributes: {part_attrs[:15]}")
                                                if hasattr(part, 'text'):
                                                    part_text = getattr(part, 'text', None)
                                                    logger.debug(f"part.text exists, value: {str(part_text)[:100] if part_text else None}")
                        
                        # Try accessing via protobuf-like interface (some Google SDKs use this)
                        try:
                            # Try accessing as if it's a protobuf message
                            if hasattr(response, 'candidates') and response.candidates:
                                for idx, candidate in enumerate(response.candidates):
                                    logger.debug(f"Candidate {idx}: {type(candidate)}")
                                    # Try to get all fields/attributes
                                    if hasattr(candidate, 'content'):
                                        content_obj = candidate.content
                                        logger.debug(f"  Content: {type(content_obj)}")
                                        if hasattr(content_obj, 'parts'):
                                            parts_list = content_obj.parts
                                            logger.debug(f"    Parts: {len(parts_list) if parts_list else 0}")
                                            if parts_list:
                                                for part_idx, part_obj in enumerate(parts_list):
                                                    logger.debug(f"      Part {part_idx}: {type(part_obj)}")
                                                    # Try all possible ways to get text
                                                    for attr in ['text', 'data', 'content']:
                                                        if hasattr(part_obj, attr):
                                                            val = getattr(part_obj, attr)
                                                            logger.debug(f"        {attr}: {type(val)} = {str(val)[:200] if val else None}")
                        except Exception as pb_e:
                            logger.info(f"Error accessing protobuf-like structure: {pb_e}")
                        
                        # Log __dict__ if available
                        if hasattr(response, '__dict__'):
                            logger.debug(f"Response __dict__ keys: {list(response.__dict__.keys())[:15]}")
                    except Exception as e:
                        logger.debug(f"Error inspecting response structure: {e}", exc_info=True)
                    
                    logger.warning(f"Unable to extract text from Gemini response. Type: {type(response)}")
            
            if not text_yielded:
                logger.warning(f"No text extracted from Gemini response. Response type: {type(response)}")

        except Exception as e:
            # #region agent log
            _log_f = open('/Users/simon/Documents/code/.cursor/debug.log', 'a'); _log_f.write(json.dumps({'sessionId': 'debug-session', 'runId': 'migration-v2', 'hypothesisId': 'C', 'location': 'llm_service.py:268', 'message': 'Gemini generate_content exception', 'data': {'error': str(e), 'error_type': type(e).__name__}, 'timestamp': __import__('time').time() * 1000}) + '\n'); _log_f.close()
            # #endregion
            
            # Check if it's a 404 (model not found) - try auto-selecting a different model
            error_str = str(e)
            is_404 = "404" in error_str or "NOT_FOUND" in error_str or "not found" in error_str.lower()
            
            if is_404 and not hasattr(self, '_model_auto_selected'):
                logger.warning(f"Model {self.gemini_model} not found (404), attempting to auto-select best available model...")
                try:
                    best_model = await self.auto_select_gemini_model()
                    if best_model and best_model != self.gemini_model:
                        old_model = self.gemini_model
                        self.gemini_model = best_model
                        self._model_auto_selected = True
                        logger.info(f"Auto-switched from {old_model} to {best_model}")
                        
                        # Retry with the new model
                        try:
                            response = self.gemini_client.models.generate_content(
                                model=self.gemini_model,
                                contents=full_prompt,
                                config={
                                    "temperature": temperature,
                                    "max_output_tokens": max_tokens,
                                }
                            )
                            
                            # Handle the response (same logic as above)
                            if hasattr(response, '__aiter__'):
                                async for chunk in response:
                                    if hasattr(chunk, 'text') and chunk.text:
                                        yield chunk.text
                                    elif isinstance(chunk, str):
                                        yield chunk
                                    elif hasattr(chunk, 'candidates') and chunk.candidates:
                                        for candidate in chunk.candidates:
                                            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                                                for part in candidate.content.parts:
                                                    if hasattr(part, 'text') and part.text:
                                                        yield part.text
                            elif hasattr(response, '__iter__'):
                                for chunk in response:
                                    if hasattr(chunk, 'text') and chunk.text:
                                        yield chunk.text
                                    elif isinstance(chunk, str):
                                        yield chunk
                                    elif hasattr(chunk, 'candidates') and chunk.candidates:
                                        for candidate in chunk.candidates:
                                            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                                                for part in candidate.content.parts:
                                                    if hasattr(part, 'text') and part.text:
                                                        yield part.text
                            else:
                                # Try multiple extraction strategies (same as main handler)
                                text_found = False
                                if hasattr(response, 'text') and response.text:
                                    yield response.text
                                    text_found = True
                                elif hasattr(response, 'content') and hasattr(response.content, 'text') and response.content.text:
                                    yield response.content.text
                                    text_found = True
                                elif hasattr(response, 'candidates') and response.candidates:
                                    for candidate in response.candidates:
                                        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                                            for part in candidate.content.parts:
                                                if hasattr(part, 'text') and part.text:
                                                    yield part.text
                                                    text_found = True
                                                    break
                                            if text_found:
                                                break
                                        elif hasattr(candidate, 'text') and candidate.text:
                                            yield candidate.text
                                            text_found = True
                                            break
                                elif isinstance(response, str):
                                    yield response
                                    text_found = True
                                
                                if not text_found:
                                    logger.warning(f"Failed to extract text from retry response. Type: {type(response)}")
                            return  # Success with auto-selected model
                        except Exception as retry_error:
                            logger.error(f"Failed to use auto-selected model {best_model}: {str(retry_error)}")
                    else:
                        self._model_auto_selected = True
                except Exception as auto_select_error:
                    logger.warning(f"Failed to auto-select model: {str(auto_select_error)}")
                    self._model_auto_selected = True
            
            logger.error(f"Gemini API error: {error_str}", exc_info=True)
            yield f"Error: Gemini API error - {error_str}"

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

    async def list_available_gemini_models(self) -> List[str]:
        """
        List all available Gemini models that support generateContent.
        Tests common model names to see which ones are available.
        
        Returns:
            List of available model names
        """
        if not self.gemini_enabled or not self.gemini_client:
            return []
        
        try:
            # Common Gemini model names to test
            models_to_test = [
                "gemini-1.5-flash",  # Stable, fast
                "gemini-1.5-pro",    # Stable, capable
                "gemini-2.0-flash-exp",  # Experimental, fast
                "gemini-2.0-flash-thinking-exp",  # Experimental with thinking
                "gemini-3-flash",    # Latest (may not exist)
                "gemini-1.5-flash-latest",  # Latest version
                "gemini-1.5-pro-latest",    # Latest version
            ]
            
            available_models = []
            
            # Test each model by trying to call it with a minimal request
            for model_name in models_to_test:
                try:
                    # Try a minimal test request (this might fail for models that don't support generateContent)
                    test_response = self.gemini_client.models.generate_content(
                        model=model_name,
                        contents="Hi",
                        config={"temperature": 0.7, "max_output_tokens": 1}
                    )
                    # If we get here without exception, the model exists
                    available_models.append(model_name)
                    logger.debug(f"Model {model_name} is available")
                except Exception as e:
                    # Model not found or not available - skip it
                    error_str = str(e).lower()
                    if "404" not in error_str and "not found" not in error_str:
                        # Other error might mean model exists but request failed
                        # Let's add it anyway as it might work with proper config
                        if "quota" not in error_str and "429" not in error_str:
                            available_models.append(model_name)
                            logger.debug(f"Model {model_name} appears to exist (error: {str(e)[:50]})")
            
            return available_models
            
        except Exception as e:
            logger.warning(f"Failed to list Gemini models: {str(e)}")
            return []

    def select_best_gemini_model(self, available_models: List[str]) -> str:
        """
        Select the best/fastest Gemini model from available models.
        
        Priority order:
        1. Flash models (fastest) - prefer newer versions
        2. Pro models (more capable but slower)
        
        Args:
            available_models: List of available model names
            
        Returns:
            Best model name, or default fallback if none found
        """
        if not available_models:
            return "gemini-1.5-flash"  # Default fallback
        
        # Priority: prefer flash models (fastest), then pro models
        # Within each category, prefer newer versions
        
        flash_models = [m for m in available_models if 'flash' in m.lower()]
        pro_models = [m for m in available_models if 'pro' in m.lower() and 'flash' not in m.lower()]
        
        # Sort flash models: prefer newer versions (higher numbers first)
        if flash_models:
            flash_models.sort(key=lambda x: (
                # Extract version number if available (e.g., "gemini-3-flash" -> 3)
                int(x.split('-')[1]) if x.split('-')[1].isdigit() else 0,
                # Prefer non-experimental versions
                'exp' not in x.lower(),
                x
            ), reverse=True)
            logger.info(f"Available flash models: {flash_models}")
            return flash_models[0]
        
        # Fallback to pro models if no flash models
        if pro_models:
            pro_models.sort(key=lambda x: (
                int(x.split('-')[1]) if x.split('-')[1].isdigit() else 0,
                'exp' not in x.lower(),
                x
            ), reverse=True)
            logger.info(f"Available pro models: {pro_models}")
            return pro_models[0]
        
        # If we have any models, use the first one
        if available_models:
            logger.info(f"Using first available model: {available_models[0]}")
            return available_models[0]
        
        # Last resort fallback
        return "gemini-1.5-flash"

    async def auto_select_gemini_model(self) -> Optional[str]:
        """
        Automatically detect and select the best available Gemini model.
        
        Returns:
            Selected model name, or None if detection fails
        """
        if not self.gemini_enabled or not self.gemini_client:
            return None
        
        try:
            logger.info("Discovering available Gemini models...")
            available_models = await self.list_available_gemini_models()
            
            if available_models:
                logger.info(f"Found {len(available_models)} available Gemini models: {available_models}")
                best_model = self.select_best_gemini_model(available_models)
                logger.info(f"Auto-selected best model: {best_model}")
                return best_model
            else:
                logger.warning("No Gemini models found, using default")
                return None
        except Exception as e:
            logger.warning(f"Failed to auto-select Gemini model: {str(e)}")
            return None


# Global LLM service instance
llm_service = LLMService()
