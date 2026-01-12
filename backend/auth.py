"""
Authentication and Authorization Module

Handles JWT token generation, password hashing, and user authentication.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import os

from backend.database import get_db
from backend.models_platform import RestaurantAccount

# Security configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production-use-openssl-rand-hex-32")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """Hash a password."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token (user_id, role, etc.)
        expires_delta: Optional expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Dict:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT token to decode

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise credentials_exception


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Dict:
    """
    Get the current authenticated user from JWT token.

    Args:
        token: JWT token from Authorization header
        db: Database session

    Returns:
        User info dict with id, email, role, account_id

    Raises:
        HTTPException: If user not found or token invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
        user_id_str: str = payload.get("sub")
        role: str = payload.get("role")

        if user_id_str is None:
            raise credentials_exception

        # Convert user_id from string to int
        user_id = int(user_id_str)

        # For admin users
        if role == "admin":
            return {
                "id": user_id,
                "role": "admin",
                "email": payload.get("email"),
                "account_id": None
            }

        # For restaurant users
        account = db.query(RestaurantAccount).filter(RestaurantAccount.id == user_id).first()
        if account is None:
            raise credentials_exception

        return {
            "id": account.id,
            "role": "restaurant",
            "email": account.owner_email,
            "account_id": account.id,
            "business_name": account.business_name
        }
    except HTTPException:
        raise
    except Exception as e:
        raise credentials_exception


async def get_current_restaurant(
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> RestaurantAccount:
    """
    Get current restaurant account (requires restaurant role).

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        RestaurantAccount object

    Raises:
        HTTPException: If user is not a restaurant owner
    """
    if current_user["role"] != "restaurant":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. Restaurant account required."
        )

    account = db.query(RestaurantAccount).filter(
        RestaurantAccount.id == current_user["account_id"]
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant account not found"
        )

    return account


async def get_current_admin(
    current_user: Dict = Depends(get_current_user)
) -> Dict:
    """
    Verify current user is an admin.

    Args:
        current_user: Current authenticated user

    Returns:
        User info dict

    Raises:
        HTTPException: If user is not an admin
    """
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. Admin access required."
        )

    return current_user


def create_admin_user(email: str, password: str, db: Session) -> Dict:
    """
    Create an admin user (for initial setup only).

    Args:
        email: Admin email
        password: Admin password
        db: Database session

    Returns:
        Access token
    """
    # This is a simple implementation
    # In production, store admin users in a separate table
    hashed_password = get_password_hash(password)

    # For now, we'll just create a token
    # You should store admin users in database
    access_token = create_access_token(
        data={"sub": 1, "email": email, "role": "admin"}
    )

    return {"access_token": access_token, "token_type": "bearer"}
