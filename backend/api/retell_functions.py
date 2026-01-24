"""
Retell Function Calling API Endpoints.

These endpoints are called by Retell's native LLM when it needs to perform
actions like fetching menu data, adding items to cart, or creating orders.

This architecture provides much lower latency than custom WebSocket LLM
because Retell's LLM handles the conversation flow natively.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from backend.database import get_db, SupabaseDB

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory cart storage (keyed by call_id)
# In production, consider Redis for persistence across restarts
active_carts: Dict[str, Dict[str, Any]] = {}


# ==================== Pydantic Models ====================

# Retell sends requests in format: {"call": {...}, "name": "func_name", "args": {...}}
# We need to handle both the nested `args` format from Retell and direct parameters for testing

class RetellCallInfo(BaseModel):
    """Call information from Retell."""
    call_id: Optional[str] = None
    call_type: Optional[str] = None
    agent_id: Optional[str] = None


class GetMenuArgs(BaseModel):
    """Arguments for get_menu function."""
    restaurant_id: Optional[int] = None
    category: Optional[str] = None
    include_prices: Optional[bool] = False  # Only include prices if explicitly asked


class GetMenuRequest(BaseModel):
    """Request to get menu items - handles both Retell format and direct calls."""
    # Retell format fields
    call: Optional[RetellCallInfo] = None
    name: Optional[str] = None
    args: Optional[GetMenuArgs] = None
    # Direct format fields (for testing)
    call_id: Optional[str] = None
    restaurant_id: Optional[int] = None
    category: Optional[str] = None
    include_prices: Optional[bool] = False

    def get_restaurant_id(self) -> Optional[int]:
        """Get restaurant_id from either format."""
        if self.args and self.args.restaurant_id:
            return self.args.restaurant_id
        return self.restaurant_id

    def get_call_id(self) -> Optional[str]:
        """Get call_id from either format."""
        if self.call and self.call.call_id:
            return self.call.call_id
        return self.call_id

    def get_category(self) -> Optional[str]:
        """Get category from either format."""
        if self.args and self.args.category:
            return self.args.category
        return self.category

    def get_include_prices(self) -> bool:
        """Check if prices should be included."""
        if self.args and self.args.include_prices:
            return self.args.include_prices
        return self.include_prices or False


class AddToCartArgs(BaseModel):
    """Arguments for add_to_cart function."""
    restaurant_id: Optional[int] = None
    item_name: Optional[str] = None
    quantity: Optional[int] = 1
    special_requests: Optional[str] = None


class AddToCartRequest(BaseModel):
    """Request to add item to cart."""
    # Retell format
    call: Optional[RetellCallInfo] = None
    name: Optional[str] = None
    args: Optional[AddToCartArgs] = None
    # Direct format
    call_id: Optional[str] = None
    restaurant_id: Optional[int] = None
    item_name: Optional[str] = None
    quantity: int = 1
    special_requests: Optional[str] = None

    def get_restaurant_id(self) -> Optional[int]:
        if self.args and self.args.restaurant_id:
            return self.args.restaurant_id
        return self.restaurant_id

    def get_call_id(self) -> Optional[str]:
        if self.call and self.call.call_id:
            return self.call.call_id
        return self.call_id

    def get_item_name(self) -> Optional[str]:
        if self.args and self.args.item_name:
            return self.args.item_name
        return self.item_name

    def get_quantity(self) -> int:
        if self.args and self.args.quantity:
            return self.args.quantity
        return self.quantity

    def get_special_requests(self) -> Optional[str]:
        if self.args and self.args.special_requests:
            return self.args.special_requests
        return self.special_requests


class RemoveFromCartArgs(BaseModel):
    """Arguments for remove_from_cart function."""
    restaurant_id: Optional[int] = None
    item_name: Optional[str] = None


class RemoveFromCartRequest(BaseModel):
    """Request to remove item from cart."""
    call: Optional[RetellCallInfo] = None
    name: Optional[str] = None
    args: Optional[RemoveFromCartArgs] = None
    call_id: Optional[str] = None
    restaurant_id: Optional[int] = None
    item_name: Optional[str] = None

    def get_restaurant_id(self) -> Optional[int]:
        if self.args and self.args.restaurant_id:
            return self.args.restaurant_id
        return self.restaurant_id

    def get_call_id(self) -> Optional[str]:
        if self.call and self.call.call_id:
            return self.call.call_id
        return self.call_id

    def get_item_name(self) -> Optional[str]:
        if self.args and self.args.item_name:
            return self.args.item_name
        return self.item_name


class GetCartArgs(BaseModel):
    """Arguments for get_cart function."""
    restaurant_id: Optional[int] = None


class GetCartRequest(BaseModel):
    """Request to get current cart."""
    call: Optional[RetellCallInfo] = None
    name: Optional[str] = None
    args: Optional[GetCartArgs] = None
    call_id: Optional[str] = None
    restaurant_id: Optional[int] = None

    def get_restaurant_id(self) -> Optional[int]:
        if self.args and self.args.restaurant_id:
            return self.args.restaurant_id
        return self.restaurant_id

    def get_call_id(self) -> Optional[str]:
        if self.call and self.call.call_id:
            return self.call.call_id
        return self.call_id


class CreateOrderArgs(BaseModel):
    """Arguments for create_order function."""
    restaurant_id: Optional[int] = None
    customer_name: Optional[str] = None
    pickup_time: Optional[str] = None


class CreateOrderRequest(BaseModel):
    """Request to create/finalize order."""
    call: Optional[RetellCallInfo] = None
    name: Optional[str] = None
    args: Optional[CreateOrderArgs] = None
    call_id: Optional[str] = None
    restaurant_id: Optional[int] = None
    customer_name: Optional[str] = None
    pickup_time: Optional[str] = None

    def get_restaurant_id(self) -> Optional[int]:
        if self.args and self.args.restaurant_id:
            return self.args.restaurant_id
        return self.restaurant_id

    def get_call_id(self) -> Optional[str]:
        if self.call and self.call.call_id:
            return self.call.call_id
        return self.call_id

    def get_customer_name(self) -> Optional[str]:
        if self.args and self.args.customer_name:
            return self.args.customer_name
        return self.customer_name

    def get_pickup_time(self) -> Optional[str]:
        if self.args and self.args.pickup_time:
            return self.args.pickup_time
        return self.pickup_time


class GetHoursArgs(BaseModel):
    """Arguments for get_hours function."""
    restaurant_id: Optional[int] = None


class GetHoursRequest(BaseModel):
    """Request to get operating hours."""
    call: Optional[RetellCallInfo] = None
    name: Optional[str] = None
    args: Optional[GetHoursArgs] = None
    call_id: Optional[str] = None
    restaurant_id: Optional[int] = None

    def get_restaurant_id(self) -> Optional[int]:
        if self.args and self.args.restaurant_id:
            return self.args.restaurant_id
        return self.restaurant_id

    def get_call_id(self) -> Optional[str]:
        if self.call and self.call.call_id:
            return self.call.call_id
        return self.call_id


# ==================== Helper Functions ====================

def get_restaurant_id_from_call(call_id: str) -> Optional[int]:
    """Get restaurant ID associated with a call."""
    cart = active_carts.get(call_id, {})
    return cart.get("restaurant_id")


def get_or_create_cart(call_id: str, restaurant_id: int = None) -> Dict[str, Any]:
    """Get existing cart or create new one."""
    if call_id not in active_carts:
        active_carts[call_id] = {
            "call_id": call_id,
            "restaurant_id": restaurant_id,
            "items": [],
            "special_requests": [],
            "created_at": datetime.now().isoformat()
        }
    elif restaurant_id and not active_carts[call_id].get("restaurant_id"):
        active_carts[call_id]["restaurant_id"] = restaurant_id
    return active_carts[call_id]


def lookup_menu_item(item_name: str, menu_data: Dict) -> Optional[Dict]:
    """Look up a menu item by name (fuzzy match)."""
    if not menu_data or not menu_data.get("menus"):
        return None

    item_name_lower = item_name.lower().strip()

    for menu in menu_data.get("menus", []):
        for category in menu.get("categories", []):
            for item in category.get("items", []):
                menu_item_name = item.get("name", "").lower().strip()

                # Check exact match or contains match
                if (menu_item_name == item_name_lower or
                    item_name_lower in menu_item_name or
                    menu_item_name in item_name_lower):
                    return item

                # Check aliases
                for alias in item.get("aliases", []):
                    alias_lower = alias.lower().strip()
                    if alias_lower == item_name_lower or item_name_lower in alias_lower:
                        return item

    return None


def fetch_menu_data(db: SupabaseDB, restaurant_id: int) -> Dict[str, Any]:
    """Fetch full menu data for a restaurant."""
    account = db.query_one("restaurant_accounts", {"id": restaurant_id})
    if not account:
        return {}

    menu_data = {
        "business_name": account.get("business_name"),
        "menus": []
    }

    menus = db.query_all("menus", {"account_id": restaurant_id})
    for menu in menus:
        menu_dict = {
            "id": menu["id"],
            "name": menu["name"],
            "categories": []
        }

        categories = db.query_all("menu_categories", {"menu_id": menu["id"]})
        for category in categories:
            category_dict = {
                "id": category["id"],
                "name": category["name"],
                "items": []
            }

            items = db.query_all("menu_items", {"category_id": category["id"]})
            for item in items:
                category_dict["items"].append({
                    "id": item["id"],
                    "name": item["name"],
                    "description": item.get("description", ""),
                    "price_cents": item.get("price_cents", 0),
                    "price_dollars": item.get("price_cents", 0) / 100,
                    "dietary_tags": item.get("dietary_tags") or [],
                    "aliases": item.get("aliases") or []
                })

            menu_dict["categories"].append(category_dict)
        menu_data["menus"].append(menu_dict)

    return menu_data


def parse_pickup_time(time_str: str) -> tuple[Optional[datetime], str]:
    """Parse pickup time string into datetime and display string."""
    import re

    time_lower = time_str.lower().strip()
    now = datetime.now()

    # Handle ASAP
    if time_lower in ["asap", "now", "as soon as possible", "right now"]:
        return None, "ASAP"

    # Handle "in X minutes"
    minutes_match = re.search(r'(\d+)\s*min', time_lower)
    if minutes_match:
        minutes = int(minutes_match.group(1))
        scheduled = now + timedelta(minutes=minutes)
        return scheduled, f"in {minutes} minutes"

    # Handle "in X hours" or "X hours"
    hours_match = re.search(r'(\d+)\s*hour', time_lower)
    if hours_match:
        hours = int(hours_match.group(1))
        scheduled = now + timedelta(hours=hours)
        return scheduled, f"in {hours} hour{'s' if hours > 1 else ''}"

    # Handle "half hour" / "30 minutes"
    if 'half' in time_lower and 'hour' in time_lower:
        scheduled = now + timedelta(minutes=30)
        return scheduled, "in 30 minutes"

    # Handle specific time (e.g., "6pm", "6:30 PM")
    time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', time_lower)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2)) if time_match.group(2) else 0
        am_pm = time_match.group(3)

        if am_pm == 'pm' and hour < 12:
            hour += 12
        elif am_pm == 'am' and hour == 12:
            hour = 0

        scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # If time is in past, assume tomorrow
        if scheduled < now:
            scheduled += timedelta(days=1)

        display = scheduled.strftime("%I:%M %p").lstrip("0")
        return scheduled, display

    return None, time_str


# ==================== Function Endpoints ====================

@router.post("/get_menu")
async def get_menu(request: GetMenuRequest, db: SupabaseDB = Depends(get_db)):
    """
    Get menu items for the restaurant.
    Called by Retell LLM when customer asks about menu.
    """
    try:
        # Get restaurant_id from request (handles both Retell and direct formats)
        restaurant_id = request.get_restaurant_id()
        call_id = request.get_call_id()
        category = request.get_category()
        include_prices = request.get_include_prices()

        if not restaurant_id and call_id:
            cart = active_carts.get(call_id, {})
            restaurant_id = cart.get("restaurant_id")

        if not restaurant_id:
            logger.warning(f"No restaurant_id provided")
            return JSONResponse({
                "success": False,
                "message": "Restaurant not identified. Please try again."
            })

        menu_data = fetch_menu_data(db, restaurant_id)

        # Format menu for voice response
        items_list = []
        categories_found = set()
        for menu in menu_data.get("menus", []):
            for cat in menu.get("categories", []):
                # Filter by category if specified
                if category:
                    if category.lower() not in cat["name"].lower():
                        continue

                categories_found.add(cat["name"])
                for item in cat.get("items", []):
                    items_list.append({
                        "name": item["name"],
                        "price": f"${item['price_dollars']:.0f}",
                        "description": item.get("description", "")[:100],
                        "category": cat["name"]
                    })

        # Build a SHORT, conversational message - just highlight popular items
        if items_list:
            if category:
                # User asked about a specific category - list those items briefly
                cat_items = items_list[:5]
                if include_prices:
                    items_text = ", ".join([f"{i['name']} for {i['price']}" for i in cat_items])
                else:
                    items_text = ", ".join([i['name'] for i in cat_items])
                message = f"We have {items_text}."
                if len(items_list) > 5:
                    message += " And a few more."
            else:
                # General menu question - pick 3 items from different categories, NO PRICES
                # Try to get variety by picking from different categories
                seen_categories = set()
                featured_items = []
                for item in items_list:
                    if item["category"] not in seen_categories and len(featured_items) < 3:
                        featured_items.append(item["name"])
                        seen_categories.add(item["category"])

                # Fill remaining slots if we don't have 3 yet
                if len(featured_items) < 3:
                    for item in items_list:
                        if item["name"] not in featured_items and len(featured_items) < 3:
                            featured_items.append(item["name"])

                if featured_items:
                    categories_text = ", ".join(sorted(seen_categories)[:3]) if len(seen_categories) > 1 else "more"
                    message = f"Popular items include {', '.join(featured_items)}. We also have {categories_text}. What sounds good?"
                else:
                    message = "What are you in the mood for today?"
        else:
            message = "Let me know what you're in the mood for - tacos, burritos, something else?"

        return JSONResponse({
            "success": True,
            "message": message,
            "restaurant_name": menu_data.get("business_name", "the restaurant"),
            "items": items_list[:20],  # Full list available if LLM needs it
            "total_items": len(items_list)
        })

    except Exception as e:
        logger.error(f"Error in get_menu: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "message": "Error fetching menu"
        })


@router.post("/add_to_cart")
async def add_to_cart(request: AddToCartRequest, db: SupabaseDB = Depends(get_db)):
    """
    Add an item to the customer's cart.
    Called by Retell LLM when customer orders an item.
    """
    try:
        # Get parameters (handles both Retell and direct formats)
        restaurant_id = request.get_restaurant_id()
        call_id = request.get_call_id()
        item_name = request.get_item_name()
        quantity = request.get_quantity()
        special_requests = request.get_special_requests()

        cart_key = call_id or f"restaurant_{restaurant_id}"
        cart = get_or_create_cart(cart_key, restaurant_id)

        if not restaurant_id:
            restaurant_id = cart.get("restaurant_id")

        if not restaurant_id:
            return JSONResponse({
                "success": False,
                "message": "Restaurant not identified"
            })

        # Look up the menu item
        menu_data = fetch_menu_data(db, restaurant_id)
        menu_item = lookup_menu_item(item_name, menu_data)

        if not menu_item:
            # Return available alternatives
            return JSONResponse({
                "success": False,
                "message": f"'{item_name}' is not on our menu",
                "suggestion": "Please check our menu for available items"
            })

        # Check if item already in cart
        existing_idx = None
        for idx, item in enumerate(cart["items"]):
            if item["name"].lower() == menu_item["name"].lower():
                existing_idx = idx
                break

        if existing_idx is not None:
            # Update quantity
            cart["items"][existing_idx]["quantity"] += quantity
            if special_requests:
                existing_requests = cart["items"][existing_idx].get("special_requests", "")
                if existing_requests:
                    cart["items"][existing_idx]["special_requests"] = f"{existing_requests}; {special_requests}"
                else:
                    cart["items"][existing_idx]["special_requests"] = special_requests
        else:
            # Add new item
            cart["items"].append({
                "name": menu_item["name"],
                "quantity": quantity,
                "price_cents": menu_item["price_cents"],
                "special_requests": special_requests or ""
            })

        # Calculate cart total
        subtotal = sum(item["price_cents"] * item["quantity"] for item in cart["items"])
        tax = int(subtotal * 0.08)
        total = subtotal + tax

        logger.info(f"Added to cart: {quantity}x {menu_item['name']} for call {call_id}")

        item_price = menu_item['price_cents'] / 100
        quantity_text = f"{quantity} " if quantity > 1 else ""
        special_text = f" with {special_requests}" if special_requests else ""
        message = f"Got it, {quantity_text}{menu_item['name']}{special_text} for ${item_price:.0f}. Your total is ${total / 100:.0f}. Anything else?"

        return JSONResponse({
            "success": True,
            "message": message,
            "added_item": {
                "name": menu_item["name"],
                "quantity": quantity,
                "price": f"${item_price:.0f}"
            },
            "cart_total": f"${total / 100:.0f}",
            "cart_item_count": sum(item["quantity"] for item in cart["items"])
        })

    except Exception as e:
        logger.error(f"Error in add_to_cart: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "message": "Error adding item to cart"
        })


@router.post("/remove_from_cart")
async def remove_from_cart(request: RemoveFromCartRequest, db: SupabaseDB = Depends(get_db)):
    """
    Remove an item from the customer's cart.
    """
    try:
        # Get parameters (handles both Retell and direct formats)
        restaurant_id = request.get_restaurant_id()
        call_id = request.get_call_id()
        item_name = request.get_item_name()

        cart_key = call_id or f"restaurant_{restaurant_id}"
        cart = active_carts.get(cart_key)
        if not cart:
            return JSONResponse({
                "success": False,
                "message": "No cart found"
            })

        # Find and remove item
        item_name_lower = item_name.lower()
        removed = False
        for idx, item in enumerate(cart["items"]):
            if item["name"].lower() == item_name_lower or item_name_lower in item["name"].lower():
                removed_item = cart["items"].pop(idx)
                removed = True
                logger.info(f"Removed from cart: {removed_item['name']} for call {call_id}")
                break

        if not removed:
            return JSONResponse({
                "success": False,
                "message": f"I don't see {item_name} in your order. Would you like me to tell you what's in your cart?"
            })

        # Calculate new total
        subtotal = sum(item["price_cents"] * item["quantity"] for item in cart["items"])
        tax = int(subtotal * 0.08)
        total = subtotal + tax

        if cart["items"]:
            message = f"Done, I removed the {item_name}. Your new total is ${total / 100:.0f}. Anything else?"
        else:
            message = f"Done, I removed the {item_name}. Your cart is now empty. What would you like to order?"

        return JSONResponse({
            "success": True,
            "message": message,
            "removed_item": item_name,
            "cart_total": f"${total / 100:.0f}",
            "cart_item_count": sum(item["quantity"] for item in cart["items"])
        })

    except Exception as e:
        logger.error(f"Error in remove_from_cart: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "message": "Error removing item"
        })


@router.post("/get_cart")
async def get_cart(request: GetCartRequest, db: SupabaseDB = Depends(get_db)):
    """
    Get current cart contents.
    """
    try:
        # Get parameters (handles both Retell and direct formats)
        restaurant_id = request.get_restaurant_id()
        call_id = request.get_call_id()

        cart_key = call_id or f"restaurant_{restaurant_id}"
        cart = active_carts.get(cart_key)
        if not cart or not cart.get("items"):
            return JSONResponse({
                "success": True,
                "items": [],
                "message": "Your cart is empty. What would you like to order?",
                "cart_total": "$0"
            })

        # Calculate totals
        subtotal = sum(item["price_cents"] * item["quantity"] for item in cart["items"])
        tax = int(subtotal * 0.08)
        total = subtotal + tax

        items_summary = [
            {
                "name": item["name"],
                "quantity": item["quantity"],
                "price": f"${item['price_cents'] * item['quantity'] / 100:.0f}",
                "special_requests": item.get("special_requests", "")
            }
            for item in cart["items"]
        ]

        # Build speakable message
        items_text = ", ".join([
            f"{item['quantity']} {item['name']}" if item['quantity'] > 1 else item['name']
            for item in items_summary
        ])
        message = f"You have {items_text}. Total is ${total / 100:.0f}. Anything else?"

        return JSONResponse({
            "success": True,
            "message": message,
            "items": items_summary,
            "cart_total": f"${total / 100:.0f}",
            "cart_item_count": sum(item["quantity"] for item in cart["items"])
        })

    except Exception as e:
        logger.error(f"Error in get_cart: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "message": "Error fetching cart"
        })


@router.post("/create_order")
async def create_order(request: CreateOrderRequest, db: SupabaseDB = Depends(get_db)):
    """
    Create/finalize the order.
    Called when customer provides name and pickup time.
    """
    try:
        # Get parameters (handles both Retell and direct formats)
        restaurant_id = request.get_restaurant_id()
        call_id = request.get_call_id()
        customer_name = request.get_customer_name()
        pickup_time = request.get_pickup_time()

        cart_key = call_id or f"restaurant_{restaurant_id}"
        cart = active_carts.get(cart_key)
        if not cart or not cart.get("items"):
            return JSONResponse({
                "success": False,
                "message": "Cart is empty. Please add items first."
            })

        restaurant_id = restaurant_id or cart.get("restaurant_id")
        if not restaurant_id:
            return JSONResponse({
                "success": False,
                "message": "Restaurant not identified"
            })

        # Get restaurant info
        account = db.query_one("restaurant_accounts", {"id": restaurant_id})
        restaurant = db.query_one("restaurants", {"account_id": restaurant_id})

        if not account or not restaurant:
            return JSONResponse({
                "success": False,
                "message": "Restaurant configuration error"
            })

        # Get or create customer
        # For now, create with minimal info - can be enhanced later
        customer = db.query_one("customers", {"name": customer_name})
        if not customer:
            customer = db.insert("customers", {
                "name": customer_name,
                "phone": cart.get("customer_phone", "")
            })

        # Calculate totals
        subtotal = sum(item["price_cents"] * item["quantity"] for item in cart["items"])
        tax = int(subtotal * 0.08)
        total = subtotal + tax

        # Parse pickup time
        scheduled_time, pickup_display = parse_pickup_time(pickup_time)

        # Build special instructions from all items
        special_instructions = f"Pickup: {pickup_display}"
        all_requests = []
        for item in cart["items"]:
            if item.get("special_requests"):
                all_requests.append(f"{item['name']}: {item['special_requests']}")
        if all_requests:
            special_instructions += "\n" + "\n".join(all_requests)

        # Create order
        order_data = {
            "account_id": restaurant_id,
            "restaurant_id": restaurant["id"],
            "customer_id": customer["id"],
            "customer_name": customer_name,
            "customer_phone": cart.get("customer_phone", ""),
            "order_date": datetime.now().isoformat(),
            "scheduled_time": scheduled_time.isoformat() if scheduled_time else None,
            "delivery_address": "Pickup",
            "order_items": json.dumps([
                {
                    "item_name": item["name"],
                    "quantity": item["quantity"],
                    "price_cents": item["price_cents"],
                    "special_requests": item.get("special_requests", "")
                }
                for item in cart["items"]
            ]),
            "subtotal": subtotal,
            "tax": tax,
            "delivery_fee": 0,
            "total": total,
            "status": "pending",
            "payment_method": "pickup",
            "payment_status": "unpaid",
            "special_instructions": special_instructions,
            "conversation_id": call_id
        }

        order = db.insert("orders", order_data)

        # Clear the cart
        if cart_key in active_carts:
            del active_carts[cart_key]

        logger.info(f"Created order #{order['id']} for {customer_name}")

        # Build order summary
        items_text = ", ".join([
            f"{item['quantity']} {item['name']}"
            for item in cart["items"]
        ])

        return JSONResponse({
            "success": True,
            "order_id": order["id"],
            "customer_name": customer_name,
            "items_summary": items_text,
            "total": f"${total / 100:.2f}",
            "pickup_time": pickup_display,
            "message": f"Order #{order['id']} confirmed for {customer_name}. {items_text} for ${total / 100:.0f}. Ready for pickup {pickup_display}."
        })

    except Exception as e:
        logger.error(f"Error in create_order: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "message": "Error creating order. Please try again."
        })


@router.post("/get_hours")
async def get_hours(request: GetHoursRequest, db: SupabaseDB = Depends(get_db)):
    """
    Get restaurant operating hours.
    """
    try:
        # Get parameters (handles both Retell and direct formats)
        restaurant_id = request.get_restaurant_id()
        call_id = request.get_call_id()

        if not restaurant_id and call_id:
            cart = active_carts.get(call_id, {})
            restaurant_id = cart.get("restaurant_id")

        if not restaurant_id:
            return JSONResponse({
                "success": False,
                "message": "Restaurant not identified"
            })

        account = db.query_one("restaurant_accounts", {"id": restaurant_id})

        if not account:
            return JSONResponse({
                "success": False,
                "message": "Restaurant not found"
            })

        opening = account.get("opening_time", "N/A")
        closing = account.get("closing_time", "N/A")

        days = account.get("operating_days", [])
        if days and isinstance(days[0], str):
            days_str = ", ".join(days)
        elif days:
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            days_str = ", ".join([day_names[d] for d in sorted(days)])
        else:
            days_str = "every day"

        return JSONResponse({
            "success": True,
            "opening_time": opening,
            "closing_time": closing,
            "operating_days": days_str,
            "message": f"We're open from {opening} to {closing}, {days_str}."
        })

    except Exception as e:
        logger.error(f"Error in get_hours: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "message": "Error fetching hours"
        })


# ==================== Call Initialization ====================

@router.post("/init_call")
async def init_call(request: Request, db: SupabaseDB = Depends(get_db)):
    """
    Initialize a call with restaurant context.
    Called when a new call starts to set up the cart with restaurant info.
    """
    try:
        data = await request.json()
        call_id = data.get("call_id")
        to_number = data.get("to_number")  # Restaurant's phone number
        from_number = data.get("from_number")  # Customer's phone number

        if not call_id:
            return JSONResponse({"success": False, "message": "Missing call_id"})

        # Look up restaurant by phone number
        restaurant_id = None
        if to_number:
            account = db.query_one("restaurant_accounts", {"retell_phone_number": to_number})
            if account:
                restaurant_id = account["id"]
                logger.info(f"Initialized call {call_id} for restaurant {account['business_name']}")

        # Create cart with restaurant context
        cart = get_or_create_cart(call_id, restaurant_id)
        cart["customer_phone"] = from_number

        return JSONResponse({
            "success": True,
            "call_id": call_id,
            "restaurant_id": restaurant_id
        })

    except Exception as e:
        logger.error(f"Error in init_call: {e}", exc_info=True)
        return JSONResponse({"success": False, "message": str(e)})
