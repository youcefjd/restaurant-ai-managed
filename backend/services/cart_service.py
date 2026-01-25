"""
Cart Service for Voice Ordering.

Provides Supabase-backed persistent cart storage for voice calls.
Replaces in-memory cart storage to survive server restarts.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from backend.database import SupabaseDB

logger = logging.getLogger(__name__)

# Table name
VOICE_CARTS_TABLE = "voice_carts"


class CartService:
    """Service for managing voice ordering carts in Supabase."""

    def __init__(self):
        """Initialize cart service."""
        logger.info("Cart service initialized (Supabase-backed)")

    def get_cart(self, call_id: str, db: SupabaseDB) -> Optional[Dict[str, Any]]:
        """
        Get cart by call_id.

        Args:
            call_id: Unique call identifier
            db: Database instance

        Returns:
            Cart dict with items, or None if not found
        """
        try:
            cart = db.query_one(VOICE_CARTS_TABLE, {"call_id": call_id})
            if cart:
                # Parse items from JSONB
                items = cart.get("items")
                if isinstance(items, str):
                    items = json.loads(items)
                cart["items"] = items or []
            return cart
        except Exception as e:
            logger.error(f"Error getting cart {call_id}: {e}")
            return None

    def create_cart(
        self,
        call_id: str,
        restaurant_id: Optional[int],
        customer_phone: Optional[str],
        db: SupabaseDB
    ) -> Dict[str, Any]:
        """
        Create a new cart.

        Args:
            call_id: Unique call identifier
            restaurant_id: Restaurant ID
            customer_phone: Customer's phone number
            db: Database instance

        Returns:
            Created cart dict
        """
        try:
            cart_data = {
                "call_id": call_id,
                "restaurant_id": restaurant_id,
                "customer_phone": customer_phone,
                "items": json.dumps([]),
                "expires_at": (datetime.utcnow() + timedelta(hours=2)).isoformat()
            }
            cart = db.insert(VOICE_CARTS_TABLE, cart_data)
            cart["items"] = []
            logger.info(f"Created cart for call {call_id}, restaurant {restaurant_id}")
            return cart
        except Exception as e:
            logger.error(f"Error creating cart {call_id}: {e}")
            # Return a temporary in-memory cart as fallback
            return {
                "call_id": call_id,
                "restaurant_id": restaurant_id,
                "customer_phone": customer_phone,
                "items": [],
                "_in_memory": True
            }

    def get_or_create_cart(
        self,
        call_id: str,
        restaurant_id: Optional[int],
        db: SupabaseDB,
        customer_phone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get existing cart or create new one.

        Args:
            call_id: Unique call identifier
            restaurant_id: Restaurant ID (used if creating)
            db: Database instance
            customer_phone: Customer's phone number

        Returns:
            Cart dict
        """
        cart = self.get_cart(call_id, db)
        if cart:
            # Update restaurant_id if provided and not set
            if restaurant_id and not cart.get("restaurant_id"):
                self.update_cart(call_id, {"restaurant_id": restaurant_id}, db)
                cart["restaurant_id"] = restaurant_id
            return cart
        return self.create_cart(call_id, restaurant_id, customer_phone, db)

    def update_cart(
        self,
        call_id: str,
        updates: Dict[str, Any],
        db: SupabaseDB
    ) -> Optional[Dict[str, Any]]:
        """
        Update cart fields.

        Args:
            call_id: Unique call identifier
            updates: Fields to update
            db: Database instance

        Returns:
            Updated cart or None
        """
        try:
            # If updating items, serialize to JSON
            if "items" in updates and isinstance(updates["items"], list):
                updates["items"] = json.dumps(updates["items"])

            # Use raw Supabase update since our helper uses id column
            result = db.table(VOICE_CARTS_TABLE).update(updates).eq("call_id", call_id).execute()
            if result.data:
                cart = result.data[0]
                # Parse items back
                if isinstance(cart.get("items"), str):
                    cart["items"] = json.loads(cart["items"])
                return cart
            return None
        except Exception as e:
            logger.error(f"Error updating cart {call_id}: {e}")
            return None

    def save_cart(self, call_id: str, items: List[Dict], db: SupabaseDB) -> bool:
        """
        Save cart items.

        Args:
            call_id: Unique call identifier
            items: List of cart items
            db: Database instance

        Returns:
            True if successful
        """
        try:
            result = self.update_cart(call_id, {"items": items}, db)
            return result is not None
        except Exception as e:
            logger.error(f"Error saving cart {call_id}: {e}")
            return False

    def add_item(
        self,
        call_id: str,
        item: Dict[str, Any],
        db: SupabaseDB
    ) -> Optional[Dict[str, Any]]:
        """
        Add item to cart.

        Args:
            call_id: Unique call identifier
            item: Item to add (name, quantity, price_cents, etc.)
            db: Database instance

        Returns:
            Updated cart or None
        """
        cart = self.get_cart(call_id, db)
        if not cart:
            logger.warning(f"Cart not found for add_item: {call_id}")
            return None

        items = cart.get("items", [])
        item_name = item.get("name", "").lower()

        # Check if item already exists
        existing_idx = None
        for idx, existing in enumerate(items):
            if existing.get("name", "").lower() == item_name:
                existing_idx = idx
                break

        if existing_idx is not None:
            # Update quantity of existing item
            items[existing_idx]["quantity"] = items[existing_idx].get("quantity", 1) + item.get("quantity", 1)
            # Merge special requests
            if item.get("special_requests"):
                existing_requests = items[existing_idx].get("special_requests", "")
                if existing_requests:
                    items[existing_idx]["special_requests"] = f"{existing_requests}; {item['special_requests']}"
                else:
                    items[existing_idx]["special_requests"] = item["special_requests"]
        else:
            items.append(item)

        self.save_cart(call_id, items, db)
        cart["items"] = items
        logger.info(f"Added {item.get('quantity', 1)}x {item.get('name')} to cart {call_id}")
        return cart

    def remove_item(
        self,
        call_id: str,
        item_name: str,
        db: SupabaseDB
    ) -> Optional[Dict[str, Any]]:
        """
        Remove item from cart.

        Args:
            call_id: Unique call identifier
            item_name: Name of item to remove
            db: Database instance

        Returns:
            Updated cart or None
        """
        cart = self.get_cart(call_id, db)
        if not cart:
            return None

        items = cart.get("items", [])
        item_name_lower = item_name.lower()

        # Find and remove item
        new_items = []
        removed = False
        for item in items:
            if not removed and item_name_lower in item.get("name", "").lower():
                removed = True
                logger.info(f"Removed {item.get('name')} from cart {call_id}")
            else:
                new_items.append(item)

        if removed:
            self.save_cart(call_id, new_items, db)
            cart["items"] = new_items

        return cart

    def delete_cart(self, call_id: str, db: SupabaseDB) -> bool:
        """
        Delete a cart entirely.

        Args:
            call_id: Unique call identifier
            db: Database instance

        Returns:
            True if deleted
        """
        try:
            db.table(VOICE_CARTS_TABLE).delete().eq("call_id", call_id).execute()
            logger.info(f"Deleted cart for call {call_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting cart {call_id}: {e}")
            return False

    def calculate_totals(
        self,
        items: List[Dict],
        tax_rate: float = 0.08
    ) -> Dict[str, int]:
        """
        Calculate cart totals.

        Args:
            items: List of cart items
            tax_rate: Tax rate as decimal (default 8%)

        Returns:
            Dict with subtotal, tax, total (all in cents)
        """
        subtotal = sum(
            item.get("price_cents", 0) * item.get("quantity", 1)
            for item in items
        )
        tax = int(subtotal * tax_rate)
        total = subtotal + tax
        return {
            "subtotal": subtotal,
            "tax": tax,
            "total": total
        }

    def cleanup_expired(self, db: SupabaseDB) -> int:
        """
        Clean up expired carts.

        Args:
            db: Database instance

        Returns:
            Number of deleted carts
        """
        try:
            # Call the PostgreSQL function
            result = db.table(VOICE_CARTS_TABLE).delete().lt(
                "expires_at",
                datetime.utcnow().isoformat()
            ).execute()
            count = len(result.data) if result.data else 0
            if count > 0:
                logger.info(f"Cleaned up {count} expired carts")
            return count
        except Exception as e:
            logger.error(f"Error cleaning up expired carts: {e}")
            return 0


# Global cart service instance
cart_service = CartService()
