"""
Restaurant onboarding and account management endpoints.

Handles restaurant signup, profile management, and menu setup.
"""

import logging
import json as json_lib
from typing import List, Optional, Union
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from typing import Optional as Opt

from backend.database import get_db, SupabaseDB
from backend.services.google_maps_service import google_maps_service
from backend.services.menu_parser import menu_parser

router = APIRouter()
logger = logging.getLogger(__name__)


# Pydantic schemas

class RestaurantAccountCreate(BaseModel):
    """Schema for creating a restaurant account."""
    business_name: str = Field(..., min_length=1, max_length=255)
    owner_name: str = Field(..., min_length=1, max_length=255)
    owner_email: EmailStr
    owner_phone: str = Field(..., min_length=10, max_length=20)

    class Config:
        from_attributes = True


class RestaurantAccountResponse(BaseModel):
    """Schema for restaurant account response."""
    id: int
    business_name: str
    owner_name: Optional[str]
    owner_email: str
    owner_phone: Optional[str]
    twilio_phone_number: Optional[str]
    opening_time: Optional[str]
    closing_time: Optional[str]
    operating_days: Optional[List[str]]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    timezone: Optional[str]
    subscription_tier: str
    subscription_status: str
    platform_commission_rate: float
    onboarding_completed: bool
    is_active: bool
    trial_ends_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MenuUpdate(BaseModel):
    """Schema for updating a menu."""
    menu_name: Optional[str] = None
    menu_description: Optional[str] = None

class MenuItemCreate(BaseModel):
    """Schema for creating a menu item."""
    category_id: int
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price_cents: int = Field(..., ge=0)
    dietary_tags: Optional[List[str]] = None
    is_available: bool = True
    preparation_time_minutes: Optional[int] = None
    display_order: int = 0

    class Config:
        from_attributes = True


class MenuItemUpdate(BaseModel):
    """Schema for updating a menu item."""
    category_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    price_cents: Optional[int] = Field(None, ge=0)
    dietary_tags: Optional[List[str]] = None
    is_available: Optional[bool] = None
    preparation_time_minutes: Optional[int] = None
    display_order: Optional[int] = None

    class Config:
        from_attributes = True


class MenuItemResponse(BaseModel):
    """Schema for menu item response."""
    id: int
    category_id: int
    name: str
    description: Optional[str]
    price_cents: int
    dietary_tags: Optional[List[str]]
    is_available: bool
    image_url: Optional[str]
    preparation_time_minutes: Optional[int]
    display_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MenuModifierCreate(BaseModel):
    """Schema for creating a menu modifier."""
    item_id: int
    name: str = Field(..., min_length=1, max_length=255)
    price_adjustment_cents: int = 0
    is_default: bool = False
    modifier_group: Optional[str] = None

    class Config:
        from_attributes = True


class MenuModifierResponse(BaseModel):
    """Schema for menu modifier response."""
    id: int
    item_id: int
    name: str
    price_adjustment_cents: int
    is_default: bool
    modifier_group: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Endpoints

@router.post("/signup", response_model=RestaurantAccountResponse, status_code=status.HTTP_201_CREATED)
async def signup_restaurant(
    account_data: RestaurantAccountCreate,
    db: SupabaseDB = Depends(get_db)
):
    """
    Sign up a new restaurant account.

    Creates account with:
    - 30-day free trial
    - FREE tier subscription
    - Platform commission rate of 10%
    """
    # Check if email already exists
    existing = db.query_one("restaurant_accounts", {"owner_email": account_data.owner_email})

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create account
    account_dict = account_data.model_dump()
    account_dict.update({
        "subscription_tier": "free",
        "subscription_status": "trial",
        "platform_commission_rate": 10.0,
        "trial_ends_at": (datetime.now() + timedelta(days=30)).isoformat(),
        "onboarding_completed": False,
        "is_active": True
    })

    account = db.insert("restaurant_accounts", account_dict)

    logger.info(f"New restaurant account created: {account['id']} - {account['business_name']}")

    return account


@router.get("/accounts/{account_id}", response_model=RestaurantAccountResponse)
async def get_account(account_id: int, db: SupabaseDB = Depends(get_db)):
    """Get restaurant account details."""
    account = db.query_one("restaurant_accounts", {"id": account_id})

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    return account


class TwilioPhoneUpdate(BaseModel):
    """Schema for updating Twilio phone number."""
    twilio_phone_number: str = Field(..., min_length=10, max_length=20, description="Twilio phone number in E.164 format (e.g., +15551234567)")


@router.patch("/accounts/{account_id}/twilio-phone", response_model=RestaurantAccountResponse)
async def update_twilio_phone(
    account_id: int,
    phone_data: TwilioPhoneUpdate,
    db: SupabaseDB = Depends(get_db)
):
    """
    Update Twilio phone number for restaurant account.

    This phone number is used to identify which restaurant a call is for.
    The number must match the Twilio phone number configured in your Twilio account.
    """
    # Verify account exists
    account = db.query_one("restaurant_accounts", {"id": account_id})
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    # Validate phone number format (E.164 format: +[country code][number])
    phone = phone_data.twilio_phone_number.strip()

    # Basic validation: should start with + and have 10+ digits
    if not phone.startswith('+'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number must be in E.164 format (e.g., +15551234567). Must start with +"
        )

    # Remove + and check if remaining is all digits
    digits_only = phone[1:].replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    if not digits_only.isdigit() or len(digits_only) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number must contain at least 10 digits"
        )

    # Normalize to E.164 format (strip all formatting, keep only + and digits)
    normalized_phone = '+' + digits_only

    # Check if phone number is already in use by another account
    # Query all accounts with this phone number and filter out current account
    existing_accounts = db.query_all("restaurant_accounts", {"twilio_phone_number": normalized_phone})
    existing = next((acc for acc in existing_accounts if acc["id"] != account_id), None)

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This phone number is already assigned to another restaurant"
        )

    # Update phone number (stored in normalized E.164 format)
    updated_account = db.update("restaurant_accounts", account_id, {"twilio_phone_number": normalized_phone})

    logger.info(f"Updated Twilio phone number for account {account_id}: {phone}")

    return updated_account


@router.delete("/accounts/{account_id}/twilio-phone", response_model=RestaurantAccountResponse)
async def remove_twilio_phone(
    account_id: int,
    db: SupabaseDB = Depends(get_db)
):
    """
    Remove Twilio phone number from restaurant account.

    This will set the phone number to null, disabling voice AI for this restaurant.
    """
    # Verify account exists
    account = db.query_one("restaurant_accounts", {"id": account_id})
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    # Remove phone number
    updated_account = db.update("restaurant_accounts", account_id, {"twilio_phone_number": None})

    logger.info(f"Removed Twilio phone number for account {account_id}")

    return updated_account


class OperatingHoursUpdate(BaseModel):
    """Schema for updating operating hours."""
    opening_time: Optional[str] = Field(None, description="Opening time in HH:MM format (e.g., '09:00')")
    closing_time: Optional[str] = Field(None, description="Closing time in HH:MM format (e.g., '22:00')")
    operating_days: Optional[List[int]] = Field(None, description="Array of weekdays (0=Monday, 6=Sunday)")


@router.patch("/accounts/{account_id}/operating-hours", response_model=RestaurantAccountResponse)
async def update_operating_hours(
    account_id: int,
    hours_data: OperatingHoursUpdate,
    db: SupabaseDB = Depends(get_db)
):
    """
    Update operating hours for restaurant account.

    This information is used by the AI to answer customer questions about hours of operation.
    """
    # Verify account exists
    account = db.query_one("restaurant_accounts", {"id": account_id})
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    update_data = {}

    # Validate time format if provided
    if hours_data.opening_time:
        try:
            # Validate HH:MM format
            parts = hours_data.opening_time.split(':')
            if len(parts) != 2 or not all(p.isdigit() for p in parts):
                raise ValueError("Invalid time format")
            hour, minute = int(parts[0]), int(parts[1])
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                raise ValueError("Invalid time values")
            update_data["opening_time"] = hours_data.opening_time
        except (ValueError, AttributeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Opening time must be in HH:MM format (e.g., '09:00')"
            )

    if hours_data.closing_time:
        try:
            # Validate HH:MM format
            parts = hours_data.closing_time.split(':')
            if len(parts) != 2 or not all(p.isdigit() for p in parts):
                raise ValueError("Invalid time format")
            hour, minute = int(parts[0]), int(parts[1])
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                raise ValueError("Invalid time values")
            update_data["closing_time"] = hours_data.closing_time
        except (ValueError, AttributeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Closing time must be in HH:MM format (e.g., '22:00')"
            )

    if hours_data.operating_days is not None:
        # Validate operating days (0-6, Monday-Sunday)
        if not all(isinstance(day, int) and 0 <= day <= 6 for day in hours_data.operating_days):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Operating days must be integers between 0 (Monday) and 6 (Sunday)"
            )
        update_data["operating_days"] = hours_data.operating_days

    if update_data:
        updated_account = db.update("restaurant_accounts", account_id, update_data)
    else:
        updated_account = account

    logger.info(f"Updated operating hours for account {account_id}")

    return updated_account


@router.post("/accounts/{account_id}/menus", status_code=status.HTTP_201_CREATED)
async def create_menu(
    account_id: int,
    menu_name: str,
    menu_description: Optional[str] = None,
    db: SupabaseDB = Depends(get_db)
):
    """Create a new menu for a restaurant account."""
    # Verify account exists
    account = db.query_one("restaurant_accounts", {"id": account_id})
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    # Create menu
    menu = db.insert("menus", {
        "account_id": account_id,
        "name": menu_name,
        "description": menu_description,
        "is_active": True
    })

    return {
        "id": menu["id"],
        "account_id": menu["account_id"],
        "name": menu["name"],
        "description": menu["description"],
        "is_active": menu["is_active"]
    }


@router.put("/menus/{menu_id}", status_code=status.HTTP_200_OK)
async def update_menu(
    menu_id: int,
    menu_update: MenuUpdate,
    db: SupabaseDB = Depends(get_db)
):
    """Update a menu's name and/or description."""
    menu = db.query_one("menus", {"id": menu_id})
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu not found"
        )

    update_data = {}
    if menu_update.menu_name is not None:
        update_data["name"] = menu_update.menu_name
    if menu_update.menu_description is not None:
        update_data["description"] = menu_update.menu_description

    if update_data:
        menu = db.update("menus", menu_id, update_data)

    return {
        "id": menu["id"],
        "account_id": menu["account_id"],
        "name": menu["name"],
        "description": menu["description"],
        "is_active": menu["is_active"]
    }


@router.delete("/menus/{menu_id}", status_code=status.HTTP_200_OK)
async def delete_menu(
    menu_id: int,
    db: SupabaseDB = Depends(get_db)
):
    """Delete a menu and all its categories and items."""
    menu = db.query_one("menus", {"id": menu_id})
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu not found"
        )

    menu_name = menu["name"]

    # Delete all items in categories belonging to this menu
    categories = db.query_all("menu_categories", {"menu_id": menu_id})
    for category in categories:
        db.delete_where("menu_items", {"category_id": category["id"]})

    # Delete all categories belonging to this menu
    db.delete_where("menu_categories", {"menu_id": menu_id})

    # Delete the menu
    db.delete("menus", menu_id)

    logger.info(f"Deleted menu {menu_id}: {menu_name}")

    return {
        "message": f"Menu '{menu_name}' has been deleted",
        "menu_id": menu_id
    }


@router.post("/menus/{menu_id}/categories", status_code=status.HTTP_201_CREATED)
async def create_category(
    menu_id: int,
    category_name: str,
    category_description: Optional[str] = None,
    display_order: int = 0,
    db: SupabaseDB = Depends(get_db)
):
    """Create a new category in a menu."""
    # Verify menu exists
    menu = db.query_one("menus", {"id": menu_id})
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu not found"
        )

    # Create category
    category = db.insert("menu_categories", {
        "menu_id": menu_id,
        "name": category_name,
        "description": category_description,
        "display_order": display_order
    })

    return {
        "id": category["id"],
        "menu_id": category["menu_id"],
        "name": category["name"],
        "description": category["description"],
        "display_order": category["display_order"]
    }


@router.post("/items", response_model=MenuItemResponse, status_code=status.HTTP_201_CREATED)
async def create_menu_item(
    item_data: MenuItemCreate,
    db: SupabaseDB = Depends(get_db)
):
    """Create a new menu item."""
    # Verify category exists
    category = db.query_one("menu_categories", {"id": item_data.category_id})
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # Create item
    item = db.insert("menu_items", item_data.model_dump())

    return item


@router.put("/items/{item_id}", response_model=MenuItemResponse)
async def update_menu_item(
    item_id: int,
    item_data: MenuItemUpdate,
    db: SupabaseDB = Depends(get_db)
):
    """Update a menu item."""
    # Find the item
    item = db.query_one("menu_items", {"id": item_id})
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu item not found"
        )

    # If category_id is being updated, verify the category exists
    if item_data.category_id is not None and item_data.category_id != item["category_id"]:
        category = db.query_one("menu_categories", {"id": item_data.category_id})
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

    # Update fields that are provided
    update_data = {k: v for k, v in item_data.model_dump(exclude_unset=True).items() if v is not None}

    if update_data:
        item = db.update("menu_items", item_id, update_data)

    logger.info(f"Updated menu item {item_id}: {item['name']}")
    return item


@router.patch("/items/{item_id}/availability")
async def toggle_menu_item_availability(
    item_id: int,
    is_available: bool,
    db: SupabaseDB = Depends(get_db)
):
    """
    Toggle menu item availability.

    Use this to mark items as available/unavailable based on ingredient availability
    or during different times of the day.
    """
    item = db.query_one("menu_items", {"id": item_id})
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu item not found"
        )

    item = db.update("menu_items", item_id, {"is_available": is_available})

    return {
        "id": item["id"],
        "name": item["name"],
        "is_available": item["is_available"],
        "message": f"Item '{item['name']}' is now {'available' if is_available else 'unavailable'}"
    }


@router.delete("/items/{item_id}", status_code=status.HTTP_200_OK)
async def delete_menu_item(
    item_id: int,
    db: SupabaseDB = Depends(get_db)
):
    """
    Delete a menu item by ID.
    """
    item = db.query_one("menu_items", {"id": item_id})
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu item not found"
        )

    item_name = item["name"]
    db.delete("menu_items", item_id)

    logger.info(f"Deleted menu item {item_id}: {item_name}")

    return {
        "message": f"Menu item '{item_name}' has been deleted",
        "deleted_item_id": item_id
    }


@router.delete("/accounts/{account_id}/menus/{menu_id}/items", status_code=status.HTTP_200_OK)
async def delete_all_menu_items(
    account_id: int,
    menu_id: int,
    db: SupabaseDB = Depends(get_db)
):
    """
    Delete all menu items from a specific menu.
    """
    # Verify account exists
    account = db.query_one("restaurant_accounts", {"id": account_id})
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    # Verify menu exists and belongs to account
    menu = db.query_one("menus", {"id": menu_id})
    if not menu or menu["account_id"] != account_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu not found"
        )

    # Get all categories for this menu and delete their items
    categories = db.query_all("menu_categories", {"menu_id": menu_id})
    items_count = 0
    for category in categories:
        items = db.query_all("menu_items", {"category_id": category["id"]})
        items_count += len(items)
        db.delete_where("menu_items", {"category_id": category["id"]})

    logger.info(f"Deleted all {items_count} menu items from menu {menu_id} for account {account_id}")

    return {
        "message": f"Deleted {items_count} menu item(s) from menu '{menu['name']}'",
        "deleted_count": items_count,
        "menu_id": menu_id
    }


@router.post("/modifiers", response_model=MenuModifierResponse, status_code=status.HTTP_201_CREATED)
async def create_modifier(
    modifier_data: MenuModifierCreate,
    db: SupabaseDB = Depends(get_db)
):
    """Create a new menu modifier."""
    # Verify item exists
    item = db.query_one("menu_items", {"id": modifier_data.item_id})
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu item not found"
        )

    # Create modifier
    modifier = db.insert("menu_modifiers", modifier_data.model_dump())

    return modifier


@router.get("/accounts/{account_id}/menu-full")
async def get_full_menu(account_id: int, db: SupabaseDB = Depends(get_db)):
    """
    Get complete menu structure for a restaurant account.

    Returns all menus with categories, items, and modifiers.
    Optimized to use only 5 queries regardless of menu size.
    """
    account = db.query_one("restaurant_accounts", {"id": account_id})
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    # Fetch all data upfront (5 queries total instead of N+1)
    menus = db.query_all("menus", {"account_id": account_id})
    if not menus:
        return {
            "account_id": account_id,
            "business_name": account["business_name"],
            "menus": []
        }

    menu_ids = [m["id"] for m in menus]

    # Get all categories for all menus in one query
    all_categories = db.table("menu_categories").select("*").in_("menu_id", menu_ids).execute().data or []

    category_ids = [c["id"] for c in all_categories]

    # Get all items for all categories in one query
    all_items = []
    if category_ids:
        all_items = db.table("menu_items").select("*").in_("category_id", category_ids).execute().data or []

    item_ids = [i["id"] for i in all_items]

    # Get all modifiers for all items in one query
    all_modifiers = []
    if item_ids:
        all_modifiers = db.table("menu_modifiers").select("*").in_("item_id", item_ids).execute().data or []

    # Build lookup maps for efficient assembly
    modifiers_by_item = {}
    for mod in all_modifiers:
        item_id = mod["item_id"]
        if item_id not in modifiers_by_item:
            modifiers_by_item[item_id] = []
        modifiers_by_item[item_id].append({
            "id": mod["id"],
            "name": mod["name"],
            "price_adjustment_cents": mod["price_adjustment_cents"],
            "price_display": f"+${mod['price_adjustment_cents'] / 100:.2f}" if mod["price_adjustment_cents"] > 0 else "",
            "is_default": mod["is_default"],
            "modifier_group": mod["modifier_group"]
        })

    items_by_category = {}
    for item in all_items:
        cat_id = item["category_id"]
        if cat_id not in items_by_category:
            items_by_category[cat_id] = []
        items_by_category[cat_id].append({
            "id": item["id"],
            "name": item["name"],
            "description": item["description"],
            "price_cents": item["price_cents"],
            "price_display": f"${item['price_cents'] / 100:.2f}",
            "dietary_tags": item["dietary_tags"] or [],
            "is_available": item["is_available"],
            "modifiers": modifiers_by_item.get(item["id"], [])
        })

    categories_by_menu = {}
    for cat in all_categories:
        menu_id = cat["menu_id"]
        if menu_id not in categories_by_menu:
            categories_by_menu[menu_id] = []
        categories_by_menu[menu_id].append({
            "id": cat["id"],
            "name": cat["name"],
            "description": cat["description"],
            "items": items_by_category.get(cat["id"], [])
        })

    # Assemble final structure
    menus_data = []
    for menu in menus:
        menus_data.append({
            "id": menu["id"],
            "name": menu["name"],
            "description": menu["description"],
            "is_active": menu["is_active"],
            "categories": categories_by_menu.get(menu["id"], [])
        })

    return {
        "account_id": account_id,
        "business_name": account["business_name"],
        "menus": menus_data
    }


@router.get("/google-maps/search")
async def search_google_maps_places(
    query: str,
    location: Optional[str] = None,
    db: SupabaseDB = Depends(get_db)
):
    """
    Search for restaurants on Google Maps.

    This endpoint allows restaurants to search for their business on Google Maps
    to automatically import operating hours.

    Args:
        query: Search query (e.g., "restaurant name" or "restaurant name, city")
        location: Optional location bias (e.g., "New York, NY")

    Returns:
        List of matching places with basic information
    """
    if not google_maps_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Maps API is not configured. Please set GOOGLE_MAPS_API_KEY environment variable."
        )

    try:
        results = google_maps_service.search_places(query, location)
        return {
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"Error searching Google Maps: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search Google Maps: {str(e)}"
        )


@router.get("/google-maps/place/{place_id}")
async def get_google_maps_place_details(
    place_id: str,
    db: SupabaseDB = Depends(get_db)
):
    """
    Get detailed information about a Google Maps place including operating hours.

    This endpoint retrieves place details that can be used to auto-populate
    restaurant operating hours.

    Args:
        place_id: Google Maps place ID

    Returns:
        Place details including operating hours in a format suitable for our system
    """
    if not google_maps_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Maps API is not configured. Please set GOOGLE_MAPS_API_KEY environment variable."
        )

    try:
        place_details = google_maps_service.get_place_details(place_id)
        return place_details
    except Exception as e:
        logger.error(f"Error getting place details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get place details: {str(e)}"
        )


class GoogleMapsPlaceUpdate(BaseModel):
    """Schema for updating hours from Google Maps place."""
    place_id: str = Field(..., description="Google Maps place ID")


@router.post("/accounts/{account_id}/operating-hours-from-google")
async def update_operating_hours_from_google(
    account_id: int,
    place_data: GoogleMapsPlaceUpdate,
    db: SupabaseDB = Depends(get_db)
):
    """
    Update restaurant operating hours from Google Maps place.

    This endpoint fetches operating hours from Google Maps and updates
    the restaurant account automatically.

    Args:
        account_id: Restaurant account ID
        place_id: Google Maps place ID

    Returns:
        Updated restaurant account with new operating hours
    """
    # Verify account exists
    account = db.query_one("restaurant_accounts", {"id": account_id})
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    if not google_maps_service.is_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Maps API is not configured. Please set GOOGLE_MAPS_API_KEY environment variable."
        )

    try:
        # Get place details
        place_details = google_maps_service.get_place_details(place_data.place_id)
        opening_hours = place_details.get('opening_hours', {})

        # Build update data
        update_data = {}
        if opening_hours.get('opening_time'):
            update_data["opening_time"] = opening_hours['opening_time']
        if opening_hours.get('closing_time'):
            update_data["closing_time"] = opening_hours['closing_time']
        if opening_hours.get('operating_days'):
            update_data["operating_days"] = opening_hours['operating_days']

        if update_data:
            account = db.update("restaurant_accounts", account_id, update_data)

        logger.info(f"Updated operating hours from Google Maps for account {account_id}")

        return account

    except Exception as e:
        logger.error(f"Error updating hours from Google Maps: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update hours from Google Maps: {str(e)}"
        )


@router.post("/accounts/{account_id}/menus/import", status_code=status.HTTP_201_CREATED)
async def import_menu(
    account_id: int,
    menu_name: Opt[str] = Form(None),
    menu_description: Opt[str] = Form(None),
    json_data: Opt[str] = Form(None),
    text_data: Opt[str] = Form(None),
    image_file: Opt[UploadFile] = File(None),
    pdf_file: Opt[UploadFile] = File(None),
    image_files: List[UploadFile] = File(...),
    db: SupabaseDB = Depends(get_db)
):
    """
    Import a menu from JSON, plain text, PDF, single image, or multiple images using AI parsing.

    This endpoint accepts menu data in multiple formats:
    - JSON: Structured menu data (will be validated and imported)
    - Text: Plain text menu description (uses AI to extract structure)
    - PDF: PDF file containing menu (extracts text and uses AI to parse)
    - Image: Single image file (JPEG, PNG) of menu (uses AI vision)
    - Images: Multiple image files (JPEG, PNG) of menu (uses AI vision on each and merges)

    Args:
        account_id: Restaurant account ID
        menu_name: Optional menu name (if not provided, will use parsed name or "Imported Menu")
        menu_description: Optional menu description
        json_data: JSON string with menu structure
        text_data: Plain text menu description
        image_file: Single image file (JPEG, PNG, WebP) of menu
        pdf_file: PDF file containing menu
        image_files: Multiple image files (JPEG, PNG, WebP) of menu

    Returns:
        Created menu with all categories and items
    """
    # Verify account exists
    account = db.query_one("restaurant_accounts", {"id": account_id})
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    # Determine input type
    input_data = None
    image_data = None
    image_type = None
    pdf_data = None
    image_list = None
    image_types = None

    # Count how many input types are provided
    input_count = sum([
        1 if json_data else 0,
        1 if text_data else 0,
        1 if image_file else 0,
        1 if pdf_file else 0,
        1 if image_files and len(image_files) > 0 else 0
    ])

    if input_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either json_data, text_data, image_file, pdf_file, or image_files"
        )

    if input_count > 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide only one input type at a time"
        )

    if pdf_file:
        # Handle PDF upload
        pdf_data = await pdf_file.read()
        content_type = pdf_file.content_type or "application/pdf"
        if content_type != "application/pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PDF file must be a valid PDF"
            )
    elif image_files and len(image_files) > 0:
        # Handle multiple image uploads
        image_list = []
        image_types = []
        for img_file in image_files:
            img_data = await img_file.read()
            img_type = img_file.content_type or "image/jpeg"
            if img_type not in ["image/jpeg", "image/png", "image/jpg", "image/webp"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Image file {img_file.filename} must be JPEG, PNG, or WebP"
                )
            image_list.append(img_data)
            image_types.append(img_type)
    elif image_file:
        # Handle single image upload
        image_data = await image_file.read()
        image_type = image_file.content_type or "image/jpeg"
        if image_type not in ["image/jpeg", "image/png", "image/jpg", "image/webp"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image file must be JPEG, PNG, or WebP"
            )
    elif json_data:
        input_data = json_data
    elif text_data:
        input_data = text_data

    try:
        # Parse menu using AI
        parsed_menu = await menu_parser.parse_menu(
            input_data=input_data,
            image_data=image_data,
            image_type=image_type,
            pdf_data=pdf_data,
            image_list=image_list,
            image_types=image_types
        )

        # Use provided name or parsed name
        final_menu_name = menu_name or parsed_menu.get("name") or "Imported Menu"
        final_menu_description = menu_description or parsed_menu.get("description")

        # Create menu
        menu = db.insert("menus", {
            "account_id": account_id,
            "name": final_menu_name,
            "description": final_menu_description,
            "is_active": True
        })

        # Create categories and items
        categories_data = parsed_menu.get("categories", [])
        created_categories = []
        created_items = []

        for cat_idx, category_data in enumerate(categories_data):
            category = db.insert("menu_categories", {
                "menu_id": menu["id"],
                "name": category_data.get("name", f"Category {cat_idx + 1}"),
                "description": category_data.get("description"),
                "display_order": category_data.get("display_order", cat_idx)
            })
            created_categories.append(category)

            # Create items for this category
            items_data = category_data.get("items", [])
            for item_idx, item_data in enumerate(items_data):
                item = db.insert("menu_items", {
                    "category_id": category["id"],
                    "name": item_data.get("name", f"Item {item_idx + 1}"),
                    "description": item_data.get("description"),
                    "price_cents": item_data.get("price_cents", 0),
                    "dietary_tags": item_data.get("dietary_tags", []),
                    "is_available": True,
                    "preparation_time_minutes": item_data.get("preparation_time_minutes"),
                    "display_order": item_data.get("display_order", item_idx)
                })
                created_items.append(item)

        # Build response
        response_categories = []
        for category in created_categories:
            category_items = [item for item in created_items if item["category_id"] == category["id"]]
            response_categories.append({
                "id": category["id"],
                "name": category["name"],
                "description": category["description"],
                "display_order": category["display_order"],
                "items_count": len(category_items),
                "items": [
                    {
                        "id": item["id"],
                        "name": item["name"],
                        "description": item["description"],
                        "price_cents": item["price_cents"],
                        "price_display": f"${item['price_cents'] / 100:.2f}",
                        "dietary_tags": item["dietary_tags"] or [],
                        "is_available": item["is_available"]
                    }
                    for item in category_items
                ]
            })

        logger.info(f"Successfully imported menu '{final_menu_name}' for account {account_id} with {len(created_categories)} categories and {len(created_items)} items")

        return {
            "id": menu["id"],
            "account_id": menu["account_id"],
            "name": menu["name"],
            "description": menu["description"],
            "is_active": menu["is_active"],
            "categories": response_categories,
            "total_items": len(created_items),
            "message": f"Successfully imported menu with {len(created_categories)} categories and {len(created_items)} items"
        }

    except ValueError as e:
        logger.error(f"Menu import validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error importing menu: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import menu: {str(e)}"
        )
