"""
Authentication API Endpoints

Handles login, signup, and token refresh for both restaurants and admins.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta

from backend.database import get_db
from backend.models_platform import RestaurantAccount, SubscriptionTier, SubscriptionStatus
from backend.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# Pydantic models
class SignupRequest(BaseModel):
    business_name: str
    owner_email: EmailStr
    password: str
    phone: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str


# Hardcoded admin credentials (move to database later)
ADMIN_EMAIL = "admin@restaurantai.com"
ADMIN_PASSWORD = "admin123"  # Change this in production!


@router.post("/signup", response_model=LoginResponse)
async def signup_restaurant(
    signup_data: SignupRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new restaurant account.

    Creates account with 30-day free trial.
    """
    # Check if email already exists
    existing = db.query(RestaurantAccount).filter(
        RestaurantAccount.owner_email == signup_data.owner_email
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new restaurant account
    account = RestaurantAccount(
        business_name=signup_data.business_name,
        owner_email=signup_data.owner_email,
        password_hash=get_password_hash(signup_data.password),
        phone=signup_data.phone,
        subscription_tier=SubscriptionTier.FREE.value,
        subscription_status=SubscriptionStatus.TRIAL.value,
        platform_commission_rate=10.0,
        commission_enabled=True,
        trial_ends_at=datetime.now() + timedelta(days=30),
        onboarding_completed=False,
        is_active=True
    )

    db.add(account)
    db.commit()
    db.refresh(account)

    # Create access token
    access_token = create_access_token(
        data={
            "sub": str(account.id),
            "email": account.owner_email,
            "role": "restaurant"
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": account.id,
            "email": account.owner_email,
            "business_name": account.business_name,
            "role": "restaurant",
            "trial_ends_at": account.trial_ends_at.isoformat() if account.trial_ends_at else None
        }
    }


@router.post("/login", response_model=LoginResponse)
async def login_restaurant(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login for restaurant accounts.

    Uses OAuth2 password flow (username = email, password = password).
    """
    # Find restaurant account
    account = db.query(RestaurantAccount).filter(
        RestaurantAccount.owner_email == form_data.username
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if password hash exists
    if not account.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account password not set. Please contact support.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(form_data.password, account.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if account is active
    if not account.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account suspended. Contact support."
        )

    # Create access token
    access_token = create_access_token(
        data={
            "sub": str(account.id),
            "email": account.owner_email,
            "role": "restaurant"
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": account.id,
            "email": account.owner_email,
            "business_name": account.business_name,
            "role": "restaurant",
            "subscription_tier": account.subscription_tier,
            "subscription_status": account.subscription_status,
            "trial_ends_at": account.trial_ends_at.isoformat() if account.trial_ends_at else None
        }
    }


@router.post("/admin/login", response_model=LoginResponse)
async def login_admin(
    login_data: AdminLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login for platform admin.

    Hardcoded credentials for now - move to database later.
    """
    # Check admin credentials
    if login_data.email != ADMIN_EMAIL or login_data.password != ADMIN_PASSWORD:
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
    db: Session = Depends(get_db)
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
    account = db.query(RestaurantAccount).filter(
        RestaurantAccount.id == current_user["account_id"]
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    return {
        "id": account.id,
        "email": account.owner_email,
        "business_name": account.business_name,
        "role": "restaurant",
        "subscription_tier": account.subscription_tier,
        "subscription_status": account.subscription_status,
        "trial_ends_at": account.trial_ends_at.isoformat() if account.trial_ends_at else None,
        "is_active": account.is_active
    }
