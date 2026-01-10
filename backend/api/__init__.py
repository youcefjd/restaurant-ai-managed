"""
Restaurant Reservation System API Module

This module initializes the FastAPI application and configures all necessary
components including database, middleware, and route handlers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

from backend.database import engine, Base
from backend.api.routes import restaurants, tables, customers, bookings, availability
from backend.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Manage application lifecycle events.
    
    This function handles startup and shutdown events for the FastAPI application.
    It ensures the database tables are created on startup.
    
    Args:
        app: The FastAPI application instance
        
    Yields:
        None
    """
    # Startup
    logger.info("Starting up Restaurant Reservation System API")
    
    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Restaurant Reservation System API")


# Create FastAPI application instance
app = FastAPI(
    title="Restaurant Reservation System API",
    description="A comprehensive API for managing restaurant reservations with advanced availability checking and auto-table assignment",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Include API routers
app.include_router(
    restaurants.router,
    prefix="/api/restaurants",
    tags=["restaurants"]
)

app.include_router(
    tables.router,
    prefix="/api",
    tags=["tables"]
)

app.include_router(
    customers.router,
    prefix="/api/customers",
    tags=["customers"]
)

app.include_router(
    bookings.router,
    prefix="/api/bookings",
    tags=["bookings"]
)

app.include_router(
    availability.router,
    prefix="/api/availability",
    tags=["availability"]
)


@app.get("/")
async def root():
    """
    Root endpoint returning API information.
    
    Returns:
        dict: API welcome message and version information
    """
    return {
        "message": "Welcome to Restaurant Reservation System API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        dict: Health status and service information
    """
    return {
        "status": "healthy",
        "service": "Restaurant Reservation System API",
        "version": "1.0.0"
    }


# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """
    Handle 404 Not Found errors.
    
    Args:
        request: The incoming request
        exc: The exception that was raised
        
    Returns:
        dict: Error response with status code 404
    """
    return {
        "detail": "The requested resource was not found",
        "status_code": 404
    }


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """
    Handle 500 Internal Server errors.
    
    Args:
        request: The incoming request
        exc: The exception that was raised
        
    Returns:
        dict: Error response with status code 500
    """
    logger.error(f"Internal server error: {exc}")
    return {
        "detail": "An internal server error occurred",
        "status_code": 500
    }


# Export the app instance
__all__ = ["app"]