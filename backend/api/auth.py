"""
Authentication API Endpoints

Handles login, signup, and token refresh for both restaurants and admins.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta

from backend.database import get_db, SupabaseDB
from backend.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user
)
from backend.services.twilio_provisioning import twilio_provisioning
from backend.auth import verify_password
from slowapi import Limiter
from slowapi.util import get_remote_address

import logging
import os
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Rate limiter for auth endpoints
limiter = Limiter(key_func=get_remote_address)

# Table names
RESTAURANT_ACCOUNTS_TABLE = "restaurant_accounts"
RESTAURANTS_TABLE = "restaurants"
ADMIN_NOTIFICATIONS_TABLE = "admin_notifications"

# Enum values (matching models_platform.py)
SUBSCRIPTION_TIER_FREE = "free"
SUBSCRIPTION_STATUS_TRIAL = "trial"
NOTIFICATION_TYPE_RESTAURANT_SIGNUP = "restaurant_signup"

# Admin credentials from environment (secure)
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")


# Pydantic models
class SignupRequest(BaseModel):
    business_name: str
    owner_name: str
    owner_email: EmailStr
    owner_phone: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/signup", response_model=LoginResponse)
@limiter.limit("3/minute")
async def signup_restaurant(
    request: Request,
    signup_data: SignupRequest,
    db: SupabaseDB = Depends(get_db)
):
    """
    Register a new restaurant account.

    Creates account with:
    - 30-day free trial OR 10 orders (whichever comes first)
    - Auto-provisioned Twilio phone number
    - Notification sent to platform admin

    Rate limited to 3 signups per minute per IP.
    """
    # Check if email already exists
    existing_email = db.query_one(RESTAURANT_ACCOUNTS_TABLE, {"owner_email": signup_data.owner_email})

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check if phone number already exists
    existing_phone = db.query_one(RESTAURANT_ACCOUNTS_TABLE, {"phone": signup_data.owner_phone})

    if existing_phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Phone number already registered"
        )

    # Note: For MVP, we use a shared Twilio number instead of provisioning per-restaurant
    # Auto-provisioning can be enabled later for paid plans
    twilio_number = None

    # Calculate trial end date
    trial_ends_at = datetime.now() + timedelta(days=30)

    # Create new restaurant account
    account_data = {
        "business_name": signup_data.business_name,
        "owner_name": signup_data.owner_name,
        "owner_email": signup_data.owner_email,
        "password_hash": get_password_hash(signup_data.password),
        "phone": signup_data.owner_phone,
        "twilio_phone_number": twilio_number,
        "subscription_tier": SUBSCRIPTION_TIER_FREE,
        "subscription_status": SUBSCRIPTION_STATUS_TRIAL,
        "platform_commission_rate": 15.0,  # Free tier default: 15%
        "commission_enabled": True,
        "trial_ends_at": trial_ends_at.isoformat(),
        "trial_order_limit": 10,
        "trial_orders_used": 0,
        "onboarding_completed": False,
        "is_active": True
    }

    account = db.insert(RESTAURANT_ACCOUNTS_TABLE, account_data)

    # Auto-create Restaurant record linked to this account
    restaurant_data = {
        "account_id": account["id"],
        "name": account["business_name"],
        "address": "Address pending",  # Will be updated during onboarding
        "phone": signup_data.owner_phone,
        "email": account["owner_email"],
        "opening_time": "09:00:00",   # Default 9 AM
        "closing_time": "21:00:00",   # Default 9 PM
        "booking_duration_minutes": 90,
        "max_party_size": 10
    }
    db.insert(RESTAURANTS_TABLE, restaurant_data)
    logger.info(f"Auto-created restaurant location for account {account['id']}")

    # Create admin notification for new signup
    notification_data = {
        "notification_type": NOTIFICATION_TYPE_RESTAURANT_SIGNUP,
        "title": f"New Restaurant Signup: {account['business_name']}",
        "message": f"{account['business_name']} signed up with email {account['owner_email']}. " +
                f"Trial ends: {trial_ends_at.strftime('%B %d, %Y')}. " +
                (f"Twilio number: {twilio_number}" if twilio_number else "No Twilio number assigned."),
        "account_id": account["id"],
        "is_read": False
    }
    db.insert(ADMIN_NOTIFICATIONS_TABLE, notification_data)

    logger.info(f"New restaurant signup: {account['id']} - {account['business_name']}")

    # Create access token
    access_token = create_access_token(
        data={
            "sub": str(account["id"]),
            "email": account["owner_email"],
            "role": "restaurant"
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": account["id"],
            "email": account["owner_email"],
            "business_name": account["business_name"],
            "role": "restaurant",
            "twilio_phone_number": twilio_number,
            "trial_ends_at": account["trial_ends_at"] if account.get("trial_ends_at") else None,
            "trial_order_limit": account["trial_order_limit"],
            "trial_orders_used": account["trial_orders_used"]
        }
    }


@router.post("/login", response_model=LoginResponse)
@limiter.limit("5/minute")
async def login_restaurant(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: SupabaseDB = Depends(get_db)
):
    """
    Login for restaurant accounts.

    Uses OAuth2 password flow (username = email, password = password).
    Rate limited to 5 attempts per minute.
    """
    # Find restaurant account
    account = db.query_one(RESTAURANT_ACCOUNTS_TABLE, {"owner_email": form_data.username})

    if not account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if password hash exists
    if not account.get("password_hash"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account password not set. Please contact support.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(form_data.password, account["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if account is active
    if not account.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account suspended. Contact support."
        )

    # Create access token
    access_token = create_access_token(
        data={
            "sub": str(account["id"]),
            "email": account["owner_email"],
            "role": "restaurant"
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": account["id"],
            "email": account["owner_email"],
            "business_name": account["business_name"],
            "role": "restaurant",
            "subscription_tier": account["subscription_tier"],
            "subscription_status": account["subscription_status"],
            "trial_ends_at": account["trial_ends_at"] if account.get("trial_ends_at") else None,
            "timezone": account.get("timezone", "America/New_York"),
            "address": account.get("address"),
            "city": account.get("city"),
            "state": account.get("state")
        }
    }


@router.post("/admin/login", response_model=LoginResponse)
@limiter.limit("3/minute")
async def login_admin(
    request: Request,
    login_data: AdminLoginRequest,
    db: SupabaseDB = Depends(get_db)
):
    """
    Login for platform admin.

    Uses environment variables ADMIN_EMAIL and ADMIN_PASSWORD_HASH.
    Generate hash with: python -c "import bcrypt; print(bcrypt.hashpw(b'yourpassword', bcrypt.gensalt()).decode())"
    Rate limited to 3 attempts per minute.
    """
    # Verify admin credentials are configured
    if not ADMIN_EMAIL or not ADMIN_PASSWORD_HASH:
        logger.error("Admin credentials not configured in environment")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin login not configured"
        )

    # Check email matches
    if login_data.email != ADMIN_EMAIL:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Verify password using bcrypt
    if not verify_password(login_data.password, ADMIN_PASSWORD_HASH):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Create access token
    access_token = create_access_token(
        data={
            "sub": "1",
            "email": login_data.email,
            "role": "admin"
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": 1,
            "email": login_data.email,
            "role": "admin"
        }
    }


@router.get("/me")
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: SupabaseDB = Depends(get_db)
):
    """
    Get current authenticated user information.
    """
    if current_user["role"] == "admin":
        return {
            "id": current_user["id"],
            "email": current_user["email"],
            "role": "admin"
        }

    # Get fresh account data
    account = db.query_one(RESTAURANT_ACCOUNTS_TABLE, {"id": current_user["account_id"]})

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    return {
        "id": account["id"],
        "email": account["owner_email"],
        "business_name": account["business_name"],
        "role": "restaurant",
        "subscription_tier": account["subscription_tier"],
        "subscription_status": account["subscription_status"],
        "trial_ends_at": account["trial_ends_at"] if account.get("trial_ends_at") else None,
        "is_active": account["is_active"],
        "timezone": account.get("timezone", "America/New_York"),
        "address": account.get("address"),
        "city": account.get("city"),
        "state": account.get("state")
    }
