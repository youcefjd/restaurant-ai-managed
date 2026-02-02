"""
Multi-tenant platform models for restaurant accounts, menus, and subscriptions.

This module extends the base models to support a multi-tenant SaaS platform
where multiple restaurant businesses can sign up and manage their own operations.
"""

from datetime import datetime
from typing import List, Optional
from enum import Enum
from decimal import Decimal

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Numeric,
    UniqueConstraint, CheckConstraint, Index, JSON
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func

from backend.database import Base


class SubscriptionTier(str, Enum):
    """Subscription tier levels."""
    FREE = "free"        # Trial - 15% commission
    STARTER = "starter"  # $49/month - 0% commission
    GROWTH = "growth"    # $149/month - 3% commission
    SCALE = "scale"      # $299/month - 3% commission


# Default commission rates per tier (admins can override per-restaurant)
TIER_COMMISSION_RATES = {
    "free": 15.0,      # Trial: 15% commission
    "starter": 0.0,    # $49/mo flat fee, no commission
    "growth": 3.0,     # $149/mo + 3% commission
    "scale": 3.0,      # $299/mo + 3% commission
}


def get_default_commission_for_tier(tier: str) -> float:
    """Get the default commission rate for a subscription tier."""
    return TIER_COMMISSION_RATES.get(tier, 15.0)  # Default to 15% if unknown


class SubscriptionStatus(str, Enum):
    """Subscription status."""
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"


class DietaryTag(str, Enum):
    """Dietary restriction tags."""
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    GLUTEN_FREE = "gluten_free"
    DAIRY_FREE = "dairy_free"
    NUT_FREE = "nut_free"
    HALAL = "halal"
    KOSHER = "kosher"
    KETO = "keto"
    SPICY = "spicy"


class RestaurantAccount(Base):
    """
    Restaurant business account (multi-tenant).

    Represents a restaurant business that can have multiple locations,
    manage menus, and receive orders/bookings.

    Attributes:
        id: Primary key
        business_name: Legal business name
        owner_name: Owner/primary contact name
        owner_email: Owner email (login)
        owner_phone: Owner phone number
        twilio_phone_number: Assigned Twilio number for AI calls
        subscription_tier: Current subscription level
        subscription_status: Subscription status
        stripe_customer_id: Stripe customer ID
        stripe_account_id: Stripe Connect account ID (for payouts)
        platform_commission_rate: Commission % (e.g., 10.0 for 10%)
        onboarding_completed: Whether setup is complete
        is_active: Whether account is active
        trial_ends_at: When trial period ends
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "restaurant_accounts"

    id = Column(Integer, primary_key=True, index=True)
    business_name = Column(String(255), nullable=False, index=True)
    owner_name = Column(String(255), nullable=True)  # Made optional for backward compatibility
    owner_email = Column(String(255), nullable=False, unique=True, index=True)
    owner_phone = Column(String(20), nullable=True)  # Made optional
    phone = Column(String(20), nullable=True)  # Restaurant contact phone
    password_hash = Column(String(255), nullable=True)  # For authentication

    # Twilio integration
    twilio_phone_number = Column(String(20), nullable=True, unique=True)

    # Operating hours
    opening_time = Column(String(10), nullable=True)  # Format: "HH:MM" (e.g., "09:00")
    closing_time = Column(String(10), nullable=True)  # Format: "HH:MM" (e.g., "22:00")
    operating_days = Column(JSON, nullable=True)  # Array of weekdays: [0,1,2,3,4,5,6] (Mon-Sun)

    # Subscription
    subscription_tier = Column(String(20), nullable=False, default=SubscriptionTier.FREE.value)
    subscription_status = Column(String(20), nullable=False, default=SubscriptionStatus.TRIAL.value)

    # Stripe integration
    stripe_customer_id = Column(String(255), nullable=True, unique=True)
    stripe_account_id = Column(String(255), nullable=True, unique=True)  # Stripe Connect

    # Platform settings
    platform_commission_rate = Column(Numeric(5, 2), nullable=False, default=10.0)  # 10%
    commission_enabled = Column(Boolean, nullable=False, default=True)  # Enable/disable commission
    onboarding_completed = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)

    # Trial limits
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    trial_order_limit = Column(Integer, nullable=False, default=10)  # Max orders during trial
    trial_orders_used = Column(Integer, nullable=False, default=0)  # Orders used so far

    # Toast POS integration
    toast_enabled = Column(Boolean, nullable=False, default=False)
    toast_client_id = Column(String(255), nullable=True)
    toast_client_secret_encrypted = Column(Text, nullable=True)
    toast_restaurant_guid = Column(String(255), nullable=True)
    toast_encryption_key_id = Column(String(100), nullable=True)
    toast_public_key = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    locations = relationship("Restaurant", back_populates="account", cascade="all, delete-orphan")
    menus = relationship("Menu", back_populates="account", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint('platform_commission_rate >= 0 AND platform_commission_rate <= 100',
                       name='check_commission_rate_valid'),
    )

    @validates('owner_email')
    def validate_email(self, key: str, email: str) -> str:
        """Validate email format."""
        if not email or '@' not in email:
            raise ValueError("Invalid email format")
        return email.lower().strip()

    def __repr__(self) -> str:
        return f"<RestaurantAccount(id={self.id}, business_name='{self.business_name}')>"


class Menu(Base):
    """
    Restaurant menu.

    A restaurant account can have multiple menus (e.g., Lunch, Dinner, Brunch).

    Attributes:
        id: Primary key
        account_id: Foreign key to restaurant account
        name: Menu name (e.g., "Dinner Menu", "Lunch Specials")
        description: Menu description
        is_active: Whether menu is currently available
        available_days: JSON array of weekdays (0=Monday, 6=Sunday)
        available_start_time: When menu becomes available each day
        available_end_time: When menu stops being available
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("restaurant_accounts.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    available_days = Column(JSON, nullable=True)  # [0,1,2,3,4] for Mon-Fri
    available_start_time = Column(String(10), nullable=True)  # "11:00"
    available_end_time = Column(String(10), nullable=True)  # "22:00"
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    account = relationship("RestaurantAccount", back_populates="menus")
    categories = relationship("MenuCategory", back_populates="menu", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Menu(id={self.id}, name='{self.name}')>"


class MenuCategory(Base):
    """
    Menu category (e.g., Appetizers, Main Course, Desserts).

    Attributes:
        id: Primary key
        menu_id: Foreign key to menu
        name: Category name
        description: Category description
        display_order: Sort order for display
        created_at: Creation timestamp
    """
    __tablename__ = "menu_categories"

    id = Column(Integer, primary_key=True, index=True)
    menu_id = Column(Integer, ForeignKey("menus.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    display_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    menu = relationship("Menu", back_populates="categories")
    items = relationship("MenuItem", back_populates="category", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_menu_category_order', 'menu_id', 'display_order'),
    )

    def __repr__(self) -> str:
        return f"<MenuCategory(id={self.id}, name='{self.name}')>"


class MenuItem(Base):
    """
    Individual menu item.

    Attributes:
        id: Primary key
        category_id: Foreign key to menu category
        name: Item name
        description: Item description
        price_cents: Price in cents
        dietary_tags: JSON array of dietary tags
        is_available: Whether item is currently available
        image_url: Optional image URL
        preparation_time_minutes: Estimated prep time
        display_order: Sort order within category
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("menu_categories.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price_cents = Column(Integer, nullable=False)
    dietary_tags = Column(JSON, nullable=True)  # ["vegetarian", "gluten_free"]
    is_available = Column(Boolean, nullable=False, default=True)
    image_url = Column(String(500), nullable=True)
    preparation_time_minutes = Column(Integer, nullable=True)
    display_order = Column(Integer, nullable=False, default=0)
    toast_item_guid = Column(String(255), nullable=True)  # Manual mapping to Toast menu item
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    category = relationship("MenuCategory", back_populates="items")
    modifiers = relationship("MenuModifier", back_populates="item", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint('price_cents >= 0', name='check_price_non_negative'),
        Index('idx_category_item_order', 'category_id', 'display_order'),
    )

    def __repr__(self) -> str:
        return f"<MenuItem(id={self.id}, name='{self.name}', price=${self.price_cents/100:.2f})>"


class MenuModifier(Base):
    """
    Menu item modifier (e.g., "No tomato", "Extra cheese", "Make it spicy").

    Attributes:
        id: Primary key
        item_id: Foreign key to menu item
        name: Modifier name
        price_adjustment_cents: Price change (can be negative)
        is_default: Whether this modifier is applied by default
        modifier_group: Optional grouping (e.g., "Sauce", "Size")
        created_at: Creation timestamp
    """
    __tablename__ = "menu_modifiers"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    price_adjustment_cents = Column(Integer, nullable=False, default=0)
    is_default = Column(Boolean, nullable=False, default=False)
    modifier_group = Column(String(100), nullable=True)  # "Size", "Sauce", "Add-ons"
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    item = relationship("MenuItem", back_populates="modifiers")

    def __repr__(self) -> str:
        price_str = f"+${self.price_adjustment_cents/100:.2f}" if self.price_adjustment_cents > 0 else ""
        return f"<MenuModifier(id={self.id}, name='{self.name}'{price_str})>"


class NotificationType(str, Enum):
    """Admin notification types."""
    RESTAURANT_SIGNUP = "restaurant_signup"
    TRIAL_EXPIRING = "trial_expiring"
    TRIAL_EXPIRED = "trial_expired"
    PAYMENT_FAILED = "payment_failed"
    HIGH_VOLUME = "high_volume"


class AdminNotification(Base):
    """
    Admin notifications for platform events.

    Tracks important events like new signups, trial expirations, etc.
    """
    __tablename__ = "admin_notifications"

    id = Column(Integer, primary_key=True, index=True)
    notification_type = Column(String(50), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    account_id = Column(Integer, ForeignKey("restaurant_accounts.id", ondelete="SET NULL"), nullable=True)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    account = relationship("RestaurantAccount", backref="notifications")

    __table_args__ = (
        Index('idx_notification_unread', 'is_read', 'created_at'),
    )

    def __repr__(self) -> str:
        return f"<AdminNotification(id={self.id}, type={self.notification_type})>"


class TranscriptType(str, Enum):
    """Enum for transcript types."""
    SMS = "sms"
    VOICE = "voice"


class Transcript(Base):
    """
    Transcript model for storing SMS and voice call conversations.
    
    Attributes:
        id: Primary key
        account_id: Foreign key to restaurant account
        transcript_type: Type of transcript (sms or voice)
        customer_phone: Customer's phone number
        twilio_phone: Restaurant's Twilio phone number
        conversation_id: Unique identifier for the conversation (CallSid for voice, MessageSid for SMS)
        messages: JSON array of conversation messages
        summary: Optional summary of the conversation
        outcome: Outcome of the conversation (booking_created, order_placed, inquiry, etc.)
        created_at: Transcript creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "transcripts"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("restaurant_accounts.id", ondelete="CASCADE"), nullable=False)
    transcript_type = Column(String(20), nullable=False)  # "sms" or "voice"
    customer_phone = Column(String(20), nullable=False, index=True)
    twilio_phone = Column(String(20), nullable=True)  # Restaurant's Twilio number
    conversation_id = Column(String(255), nullable=False, index=True)  # CallSid or MessageSid
    messages = Column(JSON, nullable=False)  # Array of {role: "user"|"assistant", content: str, timestamp: str}
    summary = Column(Text, nullable=True)
    outcome = Column(String(100), nullable=True)  # "booking_created", "order_placed", "inquiry", etc.
    duration_seconds = Column(Integer, nullable=True)  # For voice calls
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    account = relationship("RestaurantAccount", backref="transcripts")
    
    __table_args__ = (
        Index('idx_account_transcripts', 'account_id', 'created_at'),
        Index('idx_transcript_type', 'transcript_type', 'created_at'),
    )
    
    @validates('transcript_type')
    def validate_transcript_type(self, key: str, transcript_type: str) -> str:
        """Validate transcript type."""
        if transcript_type not in [t.value for t in TranscriptType]:
            raise ValueError(f"Invalid transcript type: {transcript_type}")
        return transcript_type
    
    def __repr__(self) -> str:
        return f"<Transcript(id={self.id}, type={self.transcript_type}, phone={self.customer_phone})>"
