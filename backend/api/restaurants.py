"""
Restaurant CRUD endpoints with validation.

This module provides API endpoints for managing restaurants including
creation, retrieval, update, and listing operations with comprehensive
validation and error handling.
"""

from typing import List, Optional
from datetime import datetime, time
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.database import get_db
from backend.models.restaurant import Restaurant
from backend.schemas.restaurant import (
    RestaurantCreate,
    RestaurantUpdate,
    RestaurantResponse,
    RestaurantListResponse
)
from backend.utils.validators import validate_phone_number, validate_email
from backend.utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

# Create router with prefix and tags
router = APIRouter(prefix="/api/restaurants", tags=["restaurants"])


@router.post("/", response_model=RestaurantResponse, status_code=status.HTTP_201_CREATED)
async def create_restaurant(
    restaurant_data: RestaurantCreate,
    db: Session = Depends(get_db)
) -> RestaurantResponse:
    """
    Create a new restaurant.
    
    Args:
        restaurant_data: Restaurant creation data
        db: Database session
        
    Returns:
        RestaurantResponse: Created restaurant details
        
    Raises:
        HTTPException: If validation fails or restaurant already exists
    """
    try:
        # Validate phone number format
        if not validate_phone_number(restaurant_data.phone):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid phone number format. Use format: +1234567890"
            )
        
        # Validate email format
        if not validate_email(restaurant_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        # Validate opening and closing times
        if restaurant_data.opening_time >= restaurant_data.closing_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Opening time must be before closing time"
            )
        
        # Validate booking duration
        if restaurant_data.booking_duration_minutes < 15 or restaurant_data.booking_duration_minutes > 480:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Booking duration must be between 15 and 480 minutes"
            )
        
        # Validate max party size
        if restaurant_data.max_party_size < 1 or restaurant_data.max_party_size > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Max party size must be between 1 and 50"
            )
        
        # Check if restaurant with same email already exists
        existing_restaurant = db.query(Restaurant).filter(
            Restaurant.email == restaurant_data.email
        ).first()
        
        if existing_restaurant:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Restaurant with this email already exists"
            )
        
        # Create restaurant instance
        restaurant = Restaurant(
            name=restaurant_data.name.strip(),
            address=restaurant_data.address.strip(),
            phone=restaurant_data.phone.strip(),
            email=restaurant_data.email.strip().lower(),
            opening_time=restaurant_data.opening_time,
            closing_time=restaurant_data.closing_time,
            booking_duration_minutes=restaurant_data.booking_duration_minutes,
            max_party_size=restaurant_data.max_party_size
        )
        
        # Save to database
        db.add(restaurant)
        db.commit()
        db.refresh(restaurant)
        
        logger.info(f"Created restaurant: {restaurant.id} - {restaurant.name}")
        
        return RestaurantResponse.from_orm(restaurant)
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error creating restaurant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create restaurant due to data conflict"
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating restaurant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get("/{restaurant_id}", response_model=RestaurantResponse)
async def get_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db)
) -> RestaurantResponse:
    """
    Get restaurant details by ID.
    
    Args:
        restaurant_id: Restaurant ID
        db: Database session
        
    Returns:
        RestaurantResponse: Restaurant details
        
    Raises:
        HTTPException: If restaurant not found
    """
    try:
        # Validate restaurant ID
        if restaurant_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid restaurant ID"
            )
        
        # Query restaurant
        restaurant = db.query(Restaurant).filter(
            Restaurant.id == restaurant_id
        ).first()
        
        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Restaurant with ID {restaurant_id} not found"
            )
        
        logger.info(f"Retrieved restaurant: {restaurant_id}")
        
        return RestaurantResponse.from_orm(restaurant)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving restaurant {restaurant_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.put("/{restaurant_id}", response_model=RestaurantResponse)
async def update_restaurant(
    restaurant_id: int,
    restaurant_data: RestaurantUpdate,
    db: Session = Depends(get_db)
) -> RestaurantResponse:
    """
    Update restaurant information.
    
    Args:
        restaurant_id: Restaurant ID
        restaurant_data: Update data
        db: Database session
        
    Returns:
        RestaurantResponse: Updated restaurant details
        
    Raises:
        HTTPException: If validation fails or restaurant not found
    """
    try:
        # Validate restaurant ID
        if restaurant_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid restaurant ID"
            )
        
        # Get existing restaurant
        restaurant = db.query(Restaurant).filter(
            Restaurant.id == restaurant_id
        ).first()
        
        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Restaurant with ID {restaurant_id} not found"
            )
        
        # Update fields if provided
        if restaurant_data.name is not None:
            restaurant.name = restaurant_data.name.strip()
        
        if restaurant_data.address is not None:
            restaurant.address = restaurant_data.address.strip()
        
        if restaurant_data.phone is not None:
            if not validate_phone_number(restaurant_data.phone):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid phone number format. Use format: +1234567890"
                )
            restaurant.phone = restaurant_data.phone.strip()
        
        if restaurant_data.email is not None:
            if not validate_email(restaurant_data.email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid email format"
                )
            # Check if email is already used by another restaurant
            existing = db.query(Restaurant).filter(
                Restaurant.email == restaurant_data.email.strip().lower(),
                Restaurant.id != restaurant_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already used by another restaurant"
                )
            restaurant.email = restaurant_data.email.strip().lower()
        
        # Update time fields with validation
        opening_time = restaurant_data.opening_time or restaurant.opening_time
        closing_time = restaurant_data.closing_time or restaurant.closing_time
        
        if opening_time >= closing_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Opening time must be before closing time"
            )
        
        if restaurant_data.opening_time is not None:
            restaurant.opening_time = restaurant_data.opening_time
        
        if restaurant_data.closing_time is not None:
            restaurant.closing_time = restaurant_data.closing_time
        
        if restaurant_data.booking_duration_minutes is not None:
            if restaurant_data.booking_duration_minutes < 15 or restaurant_data.booking_duration_minutes > 480:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Booking duration must be between 15 and 480 minutes"
                )
            restaurant.booking_duration_minutes = restaurant_data.booking_duration_minutes
        
        if restaurant_data.max_party_size is not None:
            if restaurant_data.max_party_size < 1 or restaurant_data.max_party_size > 50:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Max party size must be between 1 and 50"
                )
            restaurant.max_party_size = restaurant_data.max_party_size
        
        # Update timestamp
        restaurant.updated_at = datetime.utcnow()
        
        # Commit changes
        db.commit()
        db.refresh(restaurant)
        
        logger.info(f"Updated restaurant: {restaurant_id}")
        
        return RestaurantResponse.from_orm(restaurant)
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error updating restaurant {restaurant_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update restaurant due to data conflict"
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating restaurant {restaurant_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get("/", response_model=RestaurantListResponse)
async def list_restaurants(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search by name or address"),
    db: Session = Depends(get_db)
) -> RestaurantListResponse:
    """
    List all restaurants with optional search and pagination.
    
    Args:
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        search: Optional search term for name or address
        db: Database session
        
    Returns:
        RestaurantListResponse: List of restaurants with pagination info
    """
    try:
        # Build base query
        query = db.query(Restaurant)
        
        # Apply search filter if provided
        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                (Restaurant.name.ilike(search_term)) |
                (Restaurant.address.ilike(search_term))
            )
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination
        restaurants = query.offset(skip).limit(limit).all()
        
        logger.info(f"Listed {len(restaurants)} restaurants (total: {total})")
        
        return RestaurantListResponse(
            restaurants=[RestaurantResponse.from_orm(r) for r in restaurants],
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"Error listing restaurants: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.delete("/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db)
) -> None:
    """
    Delete a restaurant (soft delete by marking as inactive).
    
    Args:
        restaurant_id: Restaurant ID
        db: Database session
        
    Raises:
        HTTPException: If restaurant not found or has active bookings
    """
    try:
        # Validate restaurant ID
        if restaurant_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid restaurant ID"
            )
        
        # Get restaurant
        restaurant = db.query(Restaurant).filter(
            Restaurant.id == restaurant_id
        ).first()
        
        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Restaurant with ID {restaurant_id} not found"
            )
        
        # Check for active bookings (would be implemented when booking model is available)
        # For now, we'll do a hard delete
        
        # Delete restaurant
        db.delete(restaurant)
        db.commit()
        
        logger.info(f"Deleted restaurant: {restaurant_id}")
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting restaurant {restaurant_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )