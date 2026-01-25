"""
Restaurant Reservation System API
Main FastAPI application entry point with CORS, middleware, and route registration
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn
from dotenv import load_dotenv
import os

# Load environment variables FIRST before any imports that need them
# Calculate absolute path to .env file to ensure it's found regardless of CWD
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_env_path = os.path.join(_project_root, '.env')

# Load .env file from project root (important for uvicorn --reload and different CWDs)
# override=True ensures .env values override any existing environment variables
load_dotenv(_env_path, override=True)

from backend.database import init_db, check_connection, SupabaseDB
from backend.api import restaurants, tables, customers, bookings, availability, voice, payments, deliveries, onboarding, platform_admin, stripe_connect, auth, transcripts, test_conversation, table_management, orders, retell_voice, mcp_tools, retell_functions
from backend.core.exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    ValidationError,
    ConflictError
)
from backend.core.logging import setup_logging

# Setup logging
logger = setup_logging(__name__)

# Rate limiter - uses client IP for identification
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan events
    """
    # Startup
    logger.info("Starting Restaurant Reservation System API")
    
    # Verify Supabase connection
    try:
        init_db()
        logger.info("Supabase connection verified successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {str(e)}")
        raise
    
    # Run service health checks (after services are initialized)
    from backend.core.service_health import service_health_checker
    
    try:
        # Check critical services
        critical_results = await service_health_checker.check_all_critical()
        
        # Check optional services
        optional_results = await service_health_checker.check_all_optional()
        
        # Combine results
        all_results = {**critical_results, **optional_results}
        
        # Log results
        logger.info("Service health check results:")
        formatted_results = service_health_checker.format_results(all_results)
        logger.info(formatted_results)
        
        # Get summary
        summary = service_health_checker.get_summary(all_results)
        
        # Log summary
        logger.info("Service Health Summary:")
        logger.info(f"  Critical: {summary['critical_healthy']}/{summary['critical_total']} healthy")
        logger.info(f"  Optional: {summary['optional_healthy']}/{summary['optional_total']} healthy")
        
        # Check if any critical services failed
        # Special handling for LLM services: allow startup if at least one LLM provider is healthy
        # (since the service has fallback logic built in)
        failed_critical = []
        gemini_result = critical_results.get("gemini", {})
        openai_result = critical_results.get("openai", {})
        gemini_status = gemini_result.get("status")
        openai_status = openai_result.get("status")
        
        gemini_healthy = gemini_status == "healthy"
        openai_healthy = openai_status == "healthy"
        gemini_failed = gemini_status == "failed"
        openai_failed = openai_status == "failed"
        
        # Check if we have at least one working LLM provider
        has_working_llm = gemini_healthy or openai_healthy
        
        # If both LLM providers failed, that's a critical failure
        if gemini_failed and openai_failed:
            failed_critical.append("LLM (both Gemini and OpenAI failed)")
        # If one LLM provider failed but the other is healthy, log a warning but don't fail
        elif gemini_failed or openai_failed:
            failed_provider = "Gemini" if gemini_failed else "OpenAI"
            working_provider = "OpenAI" if gemini_failed else "Gemini"
            logger.warning(
                f"{failed_provider} LLM health check failed, but {working_provider} is healthy. "
                f"Server will use {working_provider} as fallback."
            )
        
        # Check other critical services (non-LLM)
        # Note: twilio (SMS) is not strictly required for voice to work
        # ElevenLabs and Deepgram are required for voice functionality
        voice_critical_services = ["deepgram", "elevenlabs"]

        for service_name, result in critical_results.items():
            if service_name in ["gemini", "openai"]:
                continue  # Handled above
            if service_name == "twilio":
                # Twilio SMS is not critical - just log warning
                if result.get("status") == "failed":
                    logger.warning(f"Twilio SMS service unhealthy: {result.get('error', 'unknown error')}. SMS features will be unavailable.")
                continue
            if result.get("status") == "failed":
                if service_name in voice_critical_services:
                    failed_critical.append(result.get("service", service_name))
                else:
                    logger.warning(f"{service_name} service unhealthy: {result.get('error', 'unknown error')}")

        if failed_critical:
            # Check if we should skip strict health checks (for development)
            skip_strict = os.getenv("SKIP_STRICT_HEALTH_CHECKS", "").lower() in ("true", "1", "yes")

            if skip_strict:
                logger.warning(
                    f"WARNING: Critical services failed health check: {', '.join(failed_critical)}. "
                    f"Continuing anyway because SKIP_STRICT_HEALTH_CHECKS=true"
                )
            else:
                error_msg = (
                    f"ERROR: Critical services failed health check. Server cannot start.\n"
                    f"Failed services: {', '.join(failed_critical)}\n"
                    f"Set SKIP_STRICT_HEALTH_CHECKS=true to bypass (for development only)"
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg)
        
        if has_working_llm:
            logger.info("All critical services healthy. Server ready to accept requests.")
        else:
            logger.info("Server ready to accept requests (with degraded LLM service).")
        
    except RuntimeError:
        # Re-raise RuntimeError (critical service failures)
        raise
    except Exception as e:
        # Log other errors but don't fail startup
        logger.warning(f"Service health check encountered an error: {str(e)}")
        logger.warning("Continuing startup despite health check error...")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Restaurant Reservation System API")


# Create FastAPI app instance
app = FastAPI(
    title="Restaurant Reservation System",
    description="API for managing restaurant reservations with automatic table assignment",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# Configure rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
cors_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:4173,http://localhost:5173")
cors_origins = cors_origins_env.split(",")
# Strip whitespace from origins
cors_origins = [origin.strip() for origin in cors_origins if origin.strip()]

logger.info(f"CORS configured with origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
        "X-Request-ID",
    ],
    expose_headers=["X-Total-Count", "X-Page", "X-Per-Page", "X-Process-Time", "X-Request-ID"],
)

# Add security middleware
if os.getenv("ENVIRONMENT", "development") == "production":
    # Only allow specific hosts in production
    allowed_hosts = os.getenv("ALLOWED_HOSTS", "localhost").split(",")
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all incoming requests and their processing time
    """
    start_time = time.time()
    request_id = f"{time.time()}-{request.client.host}"
    
    # Log request
    logger.info(
        f"Request started",
        extra={
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "client_host": request.client.host,
        }
    )
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log response
    logger.info(
        f"Request completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "process_time": f"{process_time:.3f}s",
        }
    )
    
    # Add custom headers
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-Request-ID"] = request_id
    
    return response


@app.middleware("http")
async def catch_exceptions(request: Request, call_next):
    """
    Global exception handler middleware
    """
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred. Please try again later.",
                "request_id": f"{time.time()}-{request.client.host}"
            }
        )


# Exception handlers
@app.exception_handler(ResourceNotFoundError)
async def resource_not_found_handler(request: Request, exc: ResourceNotFoundError):
    """Handle resource not found errors"""
    logger.warning(f"Resource not found: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "Resource not found",
            "message": exc.message,
            "resource": exc.resource_type,
            "resource_id": exc.resource_id
        }
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle validation errors"""
    logger.warning(f"Validation error: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Validation error",
            "message": exc.message,
            "field": exc.field,
            "value": exc.value
        }
    )


@app.exception_handler(ConflictError)
async def conflict_error_handler(request: Request, exc: ConflictError):
    """Handle conflict errors"""
    logger.warning(f"Conflict error: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": "Conflict",
            "message": exc.message,
            "resource": exc.resource_type,
            "conflicts": exc.conflicts
        }
    )


@app.exception_handler(BusinessLogicError)
async def business_logic_error_handler(request: Request, exc: BusinessLogicError):
    """Handle business logic errors"""
    logger.error(f"Business logic error: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Business logic error",
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(f"Request validation error: {errors}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "message": "Invalid request data",
            "errors": errors
        }
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions"""
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP error",
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def database_error_handler(request: Request, exc: Exception):
    """Handle general database/unexpected errors"""
    # Check if it's a Supabase/database related error
    error_str = str(exc).lower()
    if any(x in error_str for x in ["supabase", "postgrest", "database", "connection"]):
        logger.error(f"Database error: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Database error",
                "message": "A database error occurred. Please try again later."
            }
        )
    # Re-raise other exceptions to be handled by other handlers
    raise exc


# Root endpoint
@app.get("/", tags=["Health"])
async def root() -> Dict[str, Any]:
    """
    Root endpoint - API information
    """
    return {
        "name": "Restaurant Reservation System API",
        "version": "1.0.0",
        "status": "active",
        "docs": "/api/docs",
        "health": "/health"
    }


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint
    
    Returns:
        Dict with health status and timestamp
    """
    try:
        # Test Supabase connection
        db_status = "healthy" if check_connection() else "unhealthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "unhealthy"
    
    # Get CORS origins for debugging
    cors_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:4173,http://localhost:5173")
    cors_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": time.time(),
        "services": {
            "api": "healthy",
            "database": db_status
        },
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "cors_origins": cors_origins
    }


# Register API routers with unique prefixes
# Authentication (public routes)
app.include_router(
    auth.router,
    prefix="/api",
    tags=["Authentication"]
)

app.include_router(
    restaurants.router,
    prefix="/api/restaurants",
    tags=["Restaurants"]
)

app.include_router(
    tables.router,
    prefix="/api",
    tags=["Tables"]
)

app.include_router(
    customers.router,
    prefix="/api/customers",
    tags=["Customers"]
)

app.include_router(
    bookings.router,
    prefix="/api/bookings",
    tags=["Bookings"]
)

app.include_router(
    availability.router,
    prefix="/api/availability",
    tags=["Availability"]
)

app.include_router(
    voice.router,
    prefix="/api/voice",
    tags=["Voice (Twilio/Deepgram)"]
)

app.include_router(
    retell_voice.router,
    prefix="/api/retell",
    tags=["Voice (Retell AI)"]
)

# Retell Function Calling endpoints (for native LLM)
app.include_router(
    retell_functions.router,
    prefix="/api/retell-functions",
    tags=["Voice (Retell Functions)"]
)

app.include_router(
    payments.router,
    prefix="/api/payments",
    tags=["Payments"]
)

app.include_router(
    deliveries.router,
    prefix="/api",
    tags=["Deliveries & Orders"]
)

app.include_router(
    onboarding.router,
    prefix="/api/onboarding",
    tags=["Restaurant Onboarding"]
)

app.include_router(
    platform_admin.router,
    prefix="/api/admin",
    tags=["Platform Admin"]
)

app.include_router(
    stripe_connect.router,
    prefix="/api/stripe-connect",
    tags=["Stripe Connect (Marketplace)"]
)

app.include_router(
    transcripts.router,
    prefix="/api/onboarding",
    tags=["Transcripts"]
)

# Test endpoint for conversation testing (development only)
app.include_router(
    test_conversation.router,
    prefix="/api/test",
    tags=["Testing"]
)

# Table management (manual control of availability)
app.include_router(
    table_management.router,
    prefix="/api/table-management",
    tags=["Table Management"]
)

# Restaurant orders (takeout and delivery) - authenticated restaurant endpoints
app.include_router(
    orders.router,
    prefix="/api/restaurant",
    tags=["Restaurant Orders"]
)

# MCP Tools for Retell AI voice agent
app.include_router(
    mcp_tools.router,
    prefix="/api",
    tags=["MCP Tools"]
)

# Set up MCP server for Retell AI integration
try:
    from fastapi_mcp import FastApiMCP

    # Create MCP server exposing only the MCP tools endpoints
    mcp = FastApiMCP(
        app,
        name="Restaurant Voice Agent MCP",
        description="MCP tools for restaurant ordering via voice",
        # Only expose the MCP tools endpoints
        include_tags=["MCP Tools"]
    )
    mcp.mount()
    logger.info("MCP server mounted at /mcp")
except ImportError:
    logger.warning("fastapi-mcp not installed - MCP server not available")
except Exception as e:
    logger.error(f"Failed to set up MCP server: {e}")


# 404 handler for undefined routes
@app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
async def catch_all(request: Request, path_name: str):
    """
    Catch all undefined routes and return 404
    """
    logger.warning(f"Undefined route accessed: {request.method} /{path_name}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "Not found",
            "message": f"Path '/{path_name}' not found",
            "method": request.method
        }
    )


if __name__ == "__main__":
    # Get configuration from environment
    host = os.getenv("API_HOST", "IP_ADDRESS_REDACTED")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("ENVIRONMENT", "development") == "development"
    workers = int(os.getenv("API_WORKERS", "1"))
    
    # Configure uvicorn
    uvicorn_config = {
        "host": host,
        "port": port,
        "reload": reload,
        "log_level": "info",
        "access_log": True,
    }
    
    # Add workers only if not in reload mode
    if not reload and workers > 1:
        uvicorn_config["workers"] = workers
    
    logger.info(f"Starting server on {host}:{port} (reload={reload})")
    
    # Run the application
    uvicorn.run(
        "backend.main:app",
        **uvicorn_config
    )