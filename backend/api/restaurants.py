"""Restaurant CRUD endpoints with validation."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from backend.database import get_db, SupabaseDB
from backend.schemas import RestaurantCreate, RestaurantUpdate, Restaurant as RestaurantResponse

router = APIRouter()


@router.post("/", response_model=RestaurantResponse, status_code=status.HTTP_201_CREATED)
async def create_restaurant(
    restaurant_data: RestaurantCreate,
    db: SupabaseDB = Depends(get_db)
):
    """Create a new restaurant."""
    data = restaurant_data.model_dump()
    # Convert time objects to strings for Supabase
    if 'opening_time' in data and data['opening_time']:
        data['opening_time'] = str(data['opening_time'])
    if 'closing_time' in data and data['closing_time']:
        data['closing_time'] = str(data['closing_time'])

    restaurant = db.insert("restaurants", data)
    return restaurant


@router.get("/{restaurant_id}", response_model=RestaurantResponse)
async def get_restaurant(restaurant_id: int, db: SupabaseDB = Depends(get_db)):
    """Get a restaurant by ID."""
    restaurant = db.query_one("restaurants", {"id": restaurant_id})
    if not restaurant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )
    return restaurant


@router.get("/", response_model=List[RestaurantResponse])
async def list_restaurants(
    skip: int = 0,
    limit: int = 100,
    db: SupabaseDB = Depends(get_db)
):
    """List all restaurants."""
    restaurants = db.query_all("restaurants", offset=skip, limit=limit)
    return restaurants


@router.put("/{restaurant_id}", response_model=RestaurantResponse)
async def update_restaurant(
    restaurant_id: int,
    restaurant_data: RestaurantUpdate,
    db: SupabaseDB = Depends(get_db)
):
    """Update a restaurant."""
    # Check if restaurant exists
    existing = db.query_one("restaurants", {"id": restaurant_id})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )

    update_data = restaurant_data.model_dump(exclude_unset=True)
    # Convert time objects to strings for Supabase
    if 'opening_time' in update_data and update_data['opening_time']:
        update_data['opening_time'] = str(update_data['opening_time'])
    if 'closing_time' in update_data and update_data['closing_time']:
        update_data['closing_time'] = str(update_data['closing_time'])

    if update_data:
        restaurant = db.update("restaurants", restaurant_id, update_data)
    else:
        restaurant = existing

    return restaurant


@router.delete("/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_restaurant(restaurant_id: int, db: SupabaseDB = Depends(get_db)):
    """Delete a restaurant."""
    # Check if restaurant exists
    existing = db.query_one("restaurants", {"id": restaurant_id})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant not found"
        )

    db.delete("restaurants", restaurant_id)
    return None
