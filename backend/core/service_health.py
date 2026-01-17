"""
Service health checker for startup validation.

Tests actual API connectivity for all external services used by the voice chat agent.
"""

import asyncio
import logging
from typing import Dict, Optional
from twilio.rest import Client
import httpx

from backend.core.logging import setup_logging
from backend.services.openai_service import llm_service
from backend.services.voice_service import voice_service
from backend.services.sms_service import sms_service
from backend.services.deepgram_service import deepgram_service
from backend.services.elevenlabs_service import elevenlabs_service
from backend.services.menu_parser import menu_parser

logger = setup_logging(__name__)


class ServiceHealthChecker:
    """Checks health status of external services using actual API calls."""

    def __init__(self):
        """Initialize service health checker."""
        self.results: Dict[str, Dict[str, Optional[str]]] = {}

    async def check_gemini(self) -> Dict[str, Optional[str]]:
        """
        Check Gemini API connectivity by making an actual API call.
        
        Returns:
            Dict with service name, status, and optional error message
        """
        if not llm_service.gemini_enabled:
            return {
                "service": "Gemini LLM",
                "status": "disabled",
                "error": "API key not set or client not initialized"
            }
        
        try:
            # Make actual API call with minimal prompt
            response = await asyncio.wait_for(
                llm_service.generate_complete_response(
                    system_prompt="Test",
                    user_message="Hi",
                    max_tokens=5
                ),
                timeout=10.0
            )
            
            if response:
                model = llm_service.gemini_model
                return {
                    "service": "Gemini LLM",
                    "status": "healthy",
                    "details": f"model: {model}"
                }
            else:
                return {
                    "service": "Gemini LLM",
                    "status": "failed",
                    "error": "Empty response from API"
                }
        except asyncio.TimeoutError:
            return {
                "service": "Gemini LLM",
                "status": "failed",
                "error": "API call timed out (>10s)"
            }
        except Exception as e:
            return {
                "service": "Gemini LLM",
                "status": "failed",
                "error": str(e)
            }

    async def check_openai(self) -> Dict[str, Optional[str]]:
        """
        Check OpenAI API connectivity by making an actual API call.
        
        Returns:
            Dict with service name, status, and optional error message
        """
        if not llm_service.openai_enabled:
            return {
                "service": "OpenAI LLM",
                "status": "disabled",
                "error": "API key not set or client not initialized"
            }
        
        try:
            # Make actual API call with minimal prompt
            response = await asyncio.wait_for(
                llm_service.generate_complete_response(
                    system_prompt="Test",
                    user_message="Hi",
                    max_tokens=5
                ),
                timeout=10.0
            )
            
            if response:
                model = llm_service.openai_model
                return {
                    "service": "OpenAI LLM",
                    "status": "healthy",
                    "details": f"model: {model}"
                }
            else:
                return {
                    "service": "OpenAI LLM",
                    "status": "failed",
                    "error": "Empty response from API"
                }
        except asyncio.TimeoutError:
            return {
                "service": "OpenAI LLM",
                "status": "failed",
                "error": "API call timed out (>10s)"
            }
        except Exception as e:
            return {
                "service": "OpenAI LLM",
                "status": "failed",
                "error": str(e)
            }

    def check_twilio(self) -> Dict[str, Optional[str]]:
        """
        Check Twilio API connectivity by validating account credentials.
        
        Returns:
            Dict with service name, status, and optional error message
        """
        if not voice_service.enabled and not sms_service.enabled:
            return {
                "service": "Twilio Voice/SMS",
                "status": "disabled",
                "error": "Account SID or Auth Token not set"
            }
        
        try:
            # Use SMS service client if available, otherwise create temporary one
            if sms_service.enabled and sms_service.client:
                client = sms_service.client
            elif voice_service.enabled:
                # Create temporary client for testing
                import os
                account_sid = os.getenv("TWILIO_ACCOUNT_SID")
                auth_token = os.getenv("TWILIO_AUTH_TOKEN")
                if account_sid and auth_token:
                    client = Client(account_sid, auth_token)
                else:
                    return {
                        "service": "Twilio Voice/SMS",
                        "status": "disabled",
                        "error": "Credentials not configured"
                    }
            else:
                return {
                    "service": "Twilio Voice/SMS",
                    "status": "disabled",
                    "error": "No client available"
                }
            
            # Make actual API call to fetch account info
            account = client.api.accounts(client.account_sid).fetch()
            
            if account:
                account_sid_short = str(account.sid)[:10] + "..." if len(str(account.sid)) > 10 else str(account.sid)
                return {
                    "service": "Twilio Voice/SMS",
                    "status": "healthy",
                    "details": f"account: {account_sid_short}"
                }
            else:
                return {
                    "service": "Twilio Voice/SMS",
                    "status": "failed",
                    "error": "Unable to fetch account info"
                }
        except Exception as e:
            error_msg = str(e)
            # Extract meaningful error message
            if "authenticate" in error_msg.lower() or "401" in error_msg:
                error_msg = "Authentication failed - invalid credentials"
            return {
                "service": "Twilio Voice/SMS",
                "status": "failed",
                "error": error_msg
            }

    def check_deepgram(self) -> Dict[str, Optional[str]]:
        """
        Check Deepgram service initialization (lightweight check).
        
        Returns:
            Dict with service name, status, and optional error message
        """
        if not deepgram_service.enabled:
            return {
                "service": "Deepgram STT",
                "status": "disabled",
                "error": "API key not set"
            }
        
        try:
            # Check if client is initialized
            if deepgram_service.client:
                return {
                    "service": "Deepgram STT",
                    "status": "healthy",
                    "details": "client initialized"
                }
            else:
                return {
                    "service": "Deepgram STT",
                    "status": "failed",
                    "error": "Client not initialized"
                }
        except Exception as e:
            return {
                "service": "Deepgram STT",
                "status": "failed",
                "error": str(e)
            }

    async def check_elevenlabs(self) -> Dict[str, Optional[str]]:
        """
        Check ElevenLabs API connectivity by calling the /voices endpoint.
        
        Returns:
            Dict with service name, status, and optional error message
        """
        if not elevenlabs_service.enabled:
            return {
                "service": "ElevenLabs TTS",
                "status": "disabled",
                "error": "API key not set"
            }
        
        try:
            # Make actual API call to verify credentials
            voices = await asyncio.wait_for(
                elevenlabs_service.get_voices(),
                timeout=10.0
            )
            
            if voices is not None:
                return {
                    "service": "ElevenLabs TTS",
                    "status": "healthy",
                    "details": f"{len(voices)} voices available"
                }
            else:
                return {
                    "service": "ElevenLabs TTS",
                    "status": "failed",
                    "error": "Unable to fetch voices"
                }
        except asyncio.TimeoutError:
            return {
                "service": "ElevenLabs TTS",
                "status": "failed",
                "error": "API call timed out (>10s)"
            }
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "authenticate" in error_msg.lower():
                error_msg = "Invalid API key"
            return {
                "service": "ElevenLabs TTS",
                "status": "failed",
                "error": error_msg
            }

    def check_menu_parser(self) -> Dict[str, Optional[str]]:
        """
        Check menu parser service (uses Gemini API, same as LLM).
        
        Returns:
            Dict with service name, status, and optional error message
        """
        if not menu_parser.enabled:
            return {
                "service": "Menu Parser",
                "status": "disabled",
                "error": "Gemini API key not set"
            }
        
        # Menu parser uses same Gemini API as LLM
        # If Gemini is healthy, menu parser should work too
        # But we'll verify it's enabled separately
        if menu_parser.gemini_client:
            return {
                "service": "Menu Parser",
                "status": "healthy",
                "details": "using Gemini"
            }
        else:
            return {
                "service": "Menu Parser",
                "status": "disabled",
                "error": "Gemini client not initialized"
            }

    async def check_all_critical(self) -> Dict[str, Dict[str, Optional[str]]]:
        """
        Check all critical services (Gemini/OpenAI, Twilio, Deepgram, ElevenLabs).
        
        These are all required for the voice agent to work with Media Streams.
        Without them, the voice agent will fail and fall back to SMS only.
        
        Returns:
            Dict mapping service names to their health check results
        """
        logger.info("Running service health checks...")
        
        results = {}
        
        # Check LLM service (critical)
        if llm_service.provider == "gemini" and llm_service.gemini_enabled:
            results["gemini"] = await self.check_gemini()
        elif llm_service.provider == "openai" and llm_service.openai_enabled:
            results["openai"] = await self.check_openai()
        else:
            # Check both if available (for fallback scenarios)
            if llm_service.gemini_enabled:
                results["gemini"] = await self.check_gemini()
            if llm_service.openai_enabled:
                results["openai"] = await self.check_openai()
        
        # Check Twilio (critical)
        results["twilio"] = self.check_twilio()
        
        # Check Deepgram (critical for Media Streams STT)
        results["deepgram"] = self.check_deepgram()
        
        # Check ElevenLabs (critical for Media Streams TTS)
        results["elevenlabs"] = await self.check_elevenlabs()
        
        return results

    async def check_all_optional(self) -> Dict[str, Dict[str, Optional[str]]]:
        """
        Check all optional services.
        
        Returns:
            Dict mapping service names to their health check results
        """
        results = {}
        
        # Check Menu Parser (uses Gemini, but verify separately)
        results["menu_parser"] = self.check_menu_parser()
        
        return results

    async def check_all(self) -> Dict[str, Dict[str, Optional[str]]]:
        """
        Check all services (critical and optional).
        
        Returns:
            Dict mapping service names to their health check results
        """
        critical = await self.check_all_critical()
        optional = await self.check_all_optional()
        
        return {**critical, **optional}

    def format_results(self, results: Dict[str, Dict[str, Optional[str]]]) -> str:
        """
        Format health check results for logging.
        
        Args:
            results: Dict of health check results
            
        Returns:
            Formatted string for logging
        """
        lines = []
        
        for service_name, result in results.items():
            status = result.get("status", "unknown")
            details = result.get("details", "")
            error = result.get("error", "")
            
            if status == "healthy":
                emoji = "✅"
                details_str = f" ({details})" if details else ""
                lines.append(f"{emoji} {result['service']}: {status}{details_str}")
            elif status == "disabled":
                emoji = "⚠️"
                lines.append(f"{emoji}  {result['service']}: {status} ({error})")
            else:
                emoji = "❌"
                lines.append(f"{emoji} {result['service']}: {status} ({error})")
        
        return "\n".join(lines)

    def get_summary(self, results: Dict[str, Dict[str, Optional[str]]]) -> Dict[str, int]:
        """
        Get summary counts of healthy/failed services.
        
        Args:
            results: Dict of health check results
            
        Returns:
            Dict with counts for critical and optional services
        """
        critical_healthy = 0
        critical_failed = 0
        optional_healthy = 0
        optional_failed = 0
        
        # All services needed for voice agent are critical
        critical_services = {"gemini", "openai", "twilio", "deepgram", "elevenlabs"}
        
        for service_name, result in results.items():
            is_critical = service_name in critical_services
            status = result.get("status", "unknown")
            
            if status == "healthy":
                if is_critical:
                    critical_healthy += 1
                else:
                    optional_healthy += 1
            elif status == "failed":
                if is_critical:
                    critical_failed += 1
                else:
                    optional_failed += 1
        
        return {
            "critical_healthy": critical_healthy,
            "critical_failed": critical_failed,
            "critical_total": critical_healthy + critical_failed,
            "optional_healthy": optional_healthy,
            "optional_failed": optional_failed,
            "optional_total": optional_healthy + optional_failed
        }


# Global instance
service_health_checker = ServiceHealthChecker()
