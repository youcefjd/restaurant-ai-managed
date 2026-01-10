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
from sqlalchemy.exc import SQLAlchemyError
import uvicorn
from dotenv import load_dotenv
import os

from backend.database import engine, Base
from backend.api import restaurants, tables, customers, bookings, availability
from backend.core.exceptions import (
    BusinessLogicError,
    ResourceNotFoundError,
    ValidationError,
    ConflictError
)
from backend.core.logging import setup_logging

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logging(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan events
    """
    # Startup
    logger.info("Starting Restaurant Reservation System API")
    
    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified successfully")
    except SQLAlchemyError as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise
    
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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page", "X-Per-Page"],
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


@app.exception_handler(SQLAlchemyError)
async def database_error_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors"""
    logger.error(f"Database error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Database error",
            "message": "A database error occurred. Please try again later."
        }
    )


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
        # Test database connection
        from backend.database import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        db_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": time.time(),
        "services": {
            "api": "healthy",
            "database": db_status
        },
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }


# Register API routers
app.include_router(
    restaurants.router,
    prefix="/api",
    tags=["Restaurants"]
)

app.include_router(
    tables.router,
    prefix="/api",
    tags=["Tables"]
)

app.include_router(
    customers.router,
    prefix="/api",
    tags=["Customers"]
)

app.include_router(
    bookings.router,
    prefix="/api",
    tags=["Bookings"]
)

app.include_router(
    availability.router,
    prefix="/api",
    tags=["Availability"]
)


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