"""
Restaurant onboarding and account management endpoints.

Handles restaurant signup, profile management, and menu setup.
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field

from backend.database import get_db
from backend.models_platform import (
    RestaurantAccount, Menu, MenuCategory, MenuItem, MenuModifier,
    SubscriptionTier, SubscriptionStatus
)
from backend.models import Restaurant

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
    owner_name: str
    owner_email: str
    owner_phone: str
    twilio_phone_number: Optional[str]
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
    db: Session = Depends(get_db)
):
    """
    Sign up a new restaurant account.

    Creates account with:
    - 30-day free trial
    - FREE tier subscription
    - Platform commission rate of 10%
    """
    # Check if email already exists
    existing = db.query(RestaurantAccount).filter(
        RestaurantAccount.owner_email == account_data.owner_email
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create account
    account = RestaurantAccount(
        **account_data.model_dump(),
        subscription_tier=SubscriptionTier.FREE.value,
        subscription_status=SubscriptionStatus.TRIAL.value,
        platform_commission_rate=10.0,
        trial_ends_at=datetime.now() + timedelta(days=30),
        onboarding_completed=False,
        is_active=True
    )

    db.add(account)
    db.commit()
    db.refresh(account)

    logger.info(f"New restaurant account created: {account.id} - {account.business_name}")

    return account


@router.get("/accounts/{account_id}", response_model=RestaurantAccountResponse)
async def get_account(account_id: int, db: Session = Depends(get_db)):
    """Get restaurant account details."""
    account = db.query(RestaurantAccount).filter(RestaurantAccount.id == account_id).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    return account


@router.post("/accounts/{account_id}/menus", status_code=status.HTTP_201_CREATED)
async def create_menu(
    account_id: int,
    menu_name: str,
    menu_description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Create a new menu for a restaurant account."""
    # Verify account exists
    account = db.query(RestaurantAccount).filter(RestaurantAccount.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    # Create menu
    menu = Menu(
        account_id=account_id,
        name=menu_name,
        description=menu_description,
        is_active=True
    )

    db.add(menu)
    db.commit()
    db.refresh(menu)

    return {
        "id": menu.id,
        "account_id": menu.account_id,
        "name": menu.name,
        "description": menu.description,
        "is_active": menu.is_active
    }


@router.post("/menus/{menu_id}/categories", status_code=status.HTTP_201_CREATED)
async def create_category(
    menu_id: int,
    category_name: str,
    category_description: Optional[str] = None,
    display_order: int = 0,
    db: Session = Depends(get_db)
):
    """Create a new category in a menu."""
    # Verify menu exists
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu not found"
        )

    # Create category
    category = MenuCategory(
        menu_id=menu_id,
        name=category_name,
        description=category_description,
        display_order=display_order
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return {
        "id": category.id,
        "menu_id": category.menu_id,
        "name": category.name,
        "description": category.description,
        "display_order": category.display_order
    }


@router.post("/items", response_model=MenuItemResponse, status_code=status.HTTP_201_CREATED)
async def create_menu_item(
    item_data: MenuItemCreate,
    db: Session = Depends(get_db)
):
    """Create a new menu item."""
    # Verify category exists
    category = db.query(MenuCategory).filter(MenuCategory.id == item_data.category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    # Create item
    item = MenuItem(**item_data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)

    return item


@router.patch("/items/{item_id}/availability")
async def toggle_menu_item_availability(
    item_id: int,
    is_available: bool,
    db: Session = Depends(get_db)
):
    """
    Toggle menu item availability.

    Use this to mark items as available/unavailable based on ingredient availability
    or during different times of the day.
    """
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu item not found"
        )

    item.is_available = is_available
    db.commit()
    db.refresh(item)

    return {
        "id": item.id,
        "name": item.name,
        "is_available": item.is_available,
        "message": f"Item '{item.name}' is now {'available' if is_available else 'unavailable'}"
    }


@router.post("/modifiers", response_model=MenuModifierResponse, status_code=status.HTTP_201_CREATED)
async def create_modifier(
    modifier_data: MenuModifierCreate,
    db: Session = Depends(get_db)
):
    """Create a new menu modifier."""
    # Verify item exists
    item = db.query(MenuItem).filter(MenuItem.id == modifier_data.item_id).first()
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Menu item not found"
        )

    # Create modifier
    modifier = MenuModifier(**modifier_data.model_dump())
    db.add(modifier)
    db.commit()
    db.refresh(modifier)

    return modifier


@router.get("/accounts/{account_id}/menu-full")
async def get_full_menu(account_id: int, db: Session = Depends(get_db)):
    """
    Get complete menu structure for a restaurant account.

    Returns all menus with categories, items, and modifiers.
    Used by AI to answer menu questions.
    """
    account = db.query(RestaurantAccount).filter(RestaurantAccount.id == account_id).first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    menus_data = []

    for menu in account.menus:
        menu_dict = {
            "id": menu.id,
            "name": menu.name,
            "description": menu.description,
            "is_active": menu.is_active,
            "categories": []
        }

        for category in menu.categories:
            category_dict = {
                "id": category.id,
                "name": category.name,
                "description": category.description,
                "items": []
            }

            for item in category.items:
                item_dict = {
                    "id": item.id,
                    "name": item.name,
                    "description": item.description,
                    "price_cents": item.price_cents,
                    "price_display": f"${item.price_cents / 100:.2f}",
                    "dietary_tags": item.dietary_tags or [],
                    "is_available": item.is_available,
                    "modifiers": []
                }

                for modifier in item.modifiers:
                    modifier_dict = {
                        "id": modifier.id,
                        "name": modifier.name,
                        "price_adjustment_cents": modifier.price_adjustment_cents,
                        "price_display": f"+${modifier.price_adjustment_cents / 100:.2f}" if modifier.price_adjustment_cents > 0 else "",
                        "is_default": modifier.is_default,
                        "modifier_group": modifier.modifier_group
                    }
                    item_dict["modifiers"].append(modifier_dict)

                category_dict["items"].append(item_dict)

            menu_dict["categories"].append(category_dict)

        menus_data.append(menu_dict)

    return {
        "account_id": account_id,
        "business_name": account.business_name,
        "menus": menus_data
    }
