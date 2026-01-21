"""
MCP Tools API for Restaurant Voice Agent.

Exposes restaurant operations as MCP tools that Retell's LLM can call.
Tools: get_menu, create_order, get_restaurant_info, check_hours
"""

import json
import logging
from typing import Optional, List, Dict
from datetime import datetime, date, time
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from backend.database import get_db, SupabaseDB

router = APIRouter(prefix="/mcp-tools", tags=["MCP Tools"])
logger = logging.getLogger(__name__)


# ==================== Request/Response Models ====================

class MenuItemResponse(BaseModel):
    """Menu item details."""
    id: int
    name: str
    description: Optional[str] = None
    price: float
    category: Optional[str] = None
    is_available: bool = True


class MenuResponse(BaseModel):
    """Full menu response."""
    restaurant_name: str
    items: List[MenuItemResponse]
    categories: List[str]


class OrderItemRequest(BaseModel):
    """Single item in an order."""
    item_name: str = Field(..., description="Name of the menu item")
    quantity: int = Field(default=1, ge=1, description="Quantity to order")
    special_instructions: Optional[str] = Field(None, description="Special requests like 'no onions'")


class CreateOrderRequest(BaseModel):
    """Request to create an order."""
    customer_name: str = Field(..., description="Customer's name")
    customer_phone: str = Field(..., description="Customer's phone number")
    items: List[OrderItemRequest] = Field(..., description="List of items to order")
    order_type: str = Field(default="pickup", description="pickup or delivery")
    delivery_address: Optional[str] = Field(None, description="Address if delivery")
    special_instructions: Optional[str] = Field(None, description="Overall order notes")


class OrderResponse(BaseModel):
    """Order confirmation response."""
    order_id: int
    status: str
    total: float
    estimated_time: str
    items_summary: str


class RestaurantInfoResponse(BaseModel):
    """Restaurant information."""
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    hours_today: str
    is_open_now: bool
    accepts_orders: bool


# ==================== MCP Tool Endpoints ====================

class RetellFunctionCall(BaseModel):
    """Retell custom function call body."""
    call: Optional[Dict] = None
    args: Optional[Dict] = None
    name: Optional[str] = None


@router.post(
    "/identify-restaurant",
    summary="Identify restaurant from call",
    description="Look up which restaurant is associated with this call. ALWAYS call this first at the start of every call."
)
async def identify_restaurant(
    request: Request,
    db: SupabaseDB = Depends(get_db)
):
    """Look up restaurant from the call's to_number (agent_number)."""
    try:
        body = await request.json()
        logger.info(f"identify-restaurant called with body: {body}")

        # Extract phone number from Retell's call object
        call_data = body.get("call", {})
        phone_number = call_data.get("to_number") or call_data.get("agent_number")

        if not phone_number:
            # Try args
            args = body.get("args", {})
            phone_number = args.get("phone_number")

        if not phone_number:
            return {
                "found": False,
                "message": "Could not determine phone number from call"
            }

        logger.info(f"Looking up restaurant for phone: {phone_number}")

    except Exception as e:
        logger.error(f"Error parsing request: {e}")
        return {"found": False, "message": "Error parsing request"}

    # Look up restaurant by their assigned phone number
    restaurant = db.query_one("restaurant_accounts", {"twilio_phone_number": phone_number})

    if not restaurant:
        # Try without + prefix
        clean_number = phone_number.lstrip('+')
        # Use ilike for partial match
        result = db.table("restaurant_accounts").select("*").ilike(
            "twilio_phone_number", f"%{clean_number}"
        ).limit(1).execute()
        restaurant = result.data[0] if result.data else None

    if not restaurant:
        return {
            "found": False,
            "message": f"No restaurant found for phone {phone_number}"
        }

    return {
        "found": True,
        "restaurant_id": restaurant["id"],
        "restaurant_name": restaurant["business_name"],
        "phone": restaurant.get("owner_phone"),
        "greeting": f"Thanks for calling {restaurant['business_name']}! How can I help you today?"
    }


@router.get(
    "/get-restaurant-by-phone",
    summary="Get restaurant by phone number",
    description="Look up which restaurant is associated with a phone number."
)
async def get_restaurant_by_phone(
    phone_number: str = Query(..., description="The phone number that received the call (E.164 format like +18329254593)"),
    db: SupabaseDB = Depends(get_db)
):
    """Look up restaurant by the phone number that received the call."""
    # Look up restaurant by their assigned Twilio/Retell phone number
    restaurant = db.query_one("restaurant_accounts", {"twilio_phone_number": phone_number})

    if not restaurant:
        # Try without + prefix
        clean_number = phone_number.lstrip('+')
        result = db.table("restaurant_accounts").select("*").ilike(
            "twilio_phone_number", f"%{clean_number}"
        ).limit(1).execute()
        restaurant = result.data[0] if result.data else None

    if not restaurant:
        return {
            "found": False,
            "message": "No restaurant found for this phone number"
        }

    return {
        "found": True,
        "restaurant_id": restaurant["id"],
        "restaurant_name": restaurant["business_name"],
        "phone": restaurant.get("owner_phone"),
        "greeting": f"Hi, thanks for calling {restaurant['business_name']}! How can I help you today?"
    }


@router.get(
    "/get-menu",
    response_model=MenuResponse,
    summary="Get restaurant menu",
    description="Returns the full menu with all available items, prices, and categories. Use this when customer asks about the menu, prices, or what's available."
)
async def get_menu(
    restaurant_id: int = Query(..., description="Restaurant ID"),
    category: Optional[str] = Query(None, description="Filter by category (e.g., 'appetizers', 'main course')"),
    db: SupabaseDB = Depends(get_db)
):
    """Get the restaurant menu."""
    # Get restaurant
    restaurant = db.query_one("restaurant_accounts", {"id": restaurant_id})

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # Get active menus for this restaurant
    menus = db.table("menus").select("id").eq(
        "account_id", restaurant_id
    ).eq("is_active", True).execute()

    if not menus.data:
        return MenuResponse(
            restaurant_name=restaurant["business_name"],
            items=[],
            categories=[]
        )

    menu_ids = [m["id"] for m in menus.data]

    # Get categories for these menus
    categories_result = db.table("menu_categories").select("*").in_(
        "menu_id", menu_ids
    ).execute()

    all_categories = categories_result.data or []
    category_map = {cat["id"]: cat["name"] for cat in all_categories}
    category_ids = list(category_map.keys())

    # Get menu items for these categories
    if not category_ids:
        return MenuResponse(
            restaurant_name=restaurant["business_name"],
            items=[],
            categories=[]
        )

    items_query = db.table("menu_items").select("*").in_(
        "category_id", category_ids
    ).eq("is_available", True)

    # Filter by category name if provided
    if category:
        # Find matching category IDs
        matching_cat_ids = [
            cat["id"] for cat in all_categories
            if category.lower() in (cat.get("name") or "").lower()
        ]
        if matching_cat_ids:
            items_query = db.table("menu_items").select("*").in_(
                "category_id", matching_cat_ids
            ).eq("is_available", True)
        else:
            # No matching categories
            return MenuResponse(
                restaurant_name=restaurant["business_name"],
                items=[],
                categories=sorted(set(cat["name"] for cat in all_categories if cat.get("name")))
            )

    items_result = items_query.execute()
    items = items_result.data or []

    # Get unique category names
    categories = sorted(set(cat["name"] for cat in all_categories if cat.get("name")))

    return MenuResponse(
        restaurant_name=restaurant["business_name"],
        items=[
            MenuItemResponse(
                id=item["id"],
                name=item["name"],
                description=item.get("description"),
                price=item["price_cents"] / 100.0 if item.get("price_cents") else 0.0,
                category=category_map.get(item.get("category_id"), ""),
                is_available=item.get("is_available", True)
            )
            for item in items
        ],
        categories=categories
    )


@router.post(
    "/create-order",
    response_model=OrderResponse,
    summary="Create a new order",
    description="Creates a new order for the customer. Use this after confirming all items, quantities, and customer details. Returns order confirmation with total and estimated time."
)
async def create_order(
    restaurant_id: int = Query(..., description="Restaurant ID"),
    order: CreateOrderRequest = ...,
    db: SupabaseDB = Depends(get_db)
):
    """Create a new order."""
    # Get restaurant
    restaurant = db.query_one("restaurant_accounts", {"id": restaurant_id})

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # Get active menus for this restaurant
    menus = db.table("menus").select("id").eq(
        "account_id", restaurant_id
    ).eq("is_active", True).execute()

    menu_ids = [m["id"] for m in (menus.data or [])]

    if not menu_ids:
        raise HTTPException(status_code=400, detail="No active menu found for restaurant")

    # Get categories for these menus
    categories_result = db.table("menu_categories").select("id").in_(
        "menu_id", menu_ids
    ).execute()
    category_ids = [c["id"] for c in (categories_result.data or [])]

    # Look up menu items and calculate total
    total = Decimal("0.00")
    order_items_data = []
    items_summary_parts = []

    for item_req in order.items:
        # Find menu item by name
        items_result = db.table("menu_items").select("*").in_(
            "category_id", category_ids
        ).ilike("name", f"%{item_req.item_name}%").eq(
            "is_available", True
        ).limit(1).execute()

        menu_item = items_result.data[0] if items_result.data else None

        if not menu_item:
            raise HTTPException(
                status_code=400,
                detail=f"Item '{item_req.item_name}' not found on menu"
            )

        # price_cents is in cents, convert to dollars for calculation
        item_price = Decimal(str(menu_item["price_cents"])) / 100
        item_total = item_price * item_req.quantity
        total += item_total

        order_items_data.append({
            "menu_item": menu_item,
            "quantity": item_req.quantity,
            "special_instructions": item_req.special_instructions,
            "price": item_price
        })

        items_summary_parts.append(f"{item_req.quantity}x {menu_item['name']}")

    # Build order items JSON
    order_items_json = json.dumps([
        {
            "menu_item_id": item["menu_item"]["id"],
            "name": item["menu_item"]["name"],
            "quantity": item["quantity"],
            "unit_price": float(item["price"]) if item["price"] else 0.0,
            "special_instructions": item["special_instructions"]
        }
        for item in order_items_data
    ])

    # Convert total to cents
    total_cents = int(total * 100)

    # Create order
    new_order = db.insert("orders", {
        "account_id": restaurant_id,
        "customer_name": order.customer_name,
        "customer_phone": order.customer_phone,
        "order_type": order.order_type,
        "delivery_address": order.delivery_address,
        "special_instructions": order.special_instructions,
        "status": "pending",
        "order_items": order_items_json,
        "subtotal": total_cents,
        "tax": 0,
        "total": total_cents
    })

    # Estimate time based on order type
    estimated_time = "15-20 minutes" if order.order_type == "pickup" else "30-45 minutes"

    logger.info(f"Order {new_order['id']} created for {order.customer_name}: {items_summary_parts}")

    return OrderResponse(
        order_id=new_order["id"],
        status="confirmed",
        total=float(total),
        estimated_time=estimated_time,
        items_summary=", ".join(items_summary_parts)
    )


@router.get(
    "/get-restaurant-info",
    response_model=RestaurantInfoResponse,
    summary="Get restaurant information",
    description="Returns restaurant details including name, address, phone, and current hours. Use this when customer asks about location, hours, or contact info."
)
async def get_restaurant_info(
    restaurant_id: int = Query(..., description="Restaurant ID"),
    db: SupabaseDB = Depends(get_db)
):
    """Get restaurant information."""
    restaurant = db.query_one("restaurant_accounts", {"id": restaurant_id})

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # Get actual operating hours from database
    now = datetime.now()
    day_name = now.strftime("%A")
    current_day = now.weekday()  # 0=Monday, 6=Sunday

    # Check if restaurant is open today
    operating_days = restaurant.get("operating_days") or [0, 1, 2, 3, 4, 5, 6]  # Default: all days
    is_operating_today = current_day in operating_days

    # Get opening/closing times
    opening_time = restaurant.get("opening_time") or "09:00"
    closing_time = restaurant.get("closing_time") or "22:00"

    # Determine if currently open
    is_open = False
    if is_operating_today:
        try:
            open_hour, open_min = map(int, opening_time.split(":"))
            close_hour, close_min = map(int, closing_time.split(":"))
            current_minutes = now.hour * 60 + now.minute
            open_minutes = open_hour * 60 + open_min
            close_minutes = close_hour * 60 + close_min
            is_open = open_minutes <= current_minutes < close_minutes
        except:
            is_open = 9 <= now.hour < 22  # Fallback

    # Format hours for display
    def format_time(t):
        try:
            h, m = map(int, t.split(":"))
            period = "AM" if h < 12 else "PM"
            h = h % 12 or 12
            return f"{h}:{m:02d} {period}"
        except:
            return t

    hours_today = f"{format_time(opening_time)} - {format_time(closing_time)}" if is_operating_today else "Closed"

    return RestaurantInfoResponse(
        name=restaurant["business_name"],
        phone=restaurant.get("owner_phone") or restaurant.get("phone"),
        address=restaurant.get("address"),
        hours_today=f"{day_name}: {hours_today}",
        is_open_now=is_open,
        accepts_orders=is_open
    )


@router.get(
    "/check-item-availability",
    summary="Check if a specific item is available",
    description="Checks if a specific menu item is available. Use this when customer asks about a specific dish."
)
async def check_item_availability(
    restaurant_id: int = Query(..., description="Restaurant ID"),
    item_name: str = Query(..., description="Name of the item to check"),
    db: SupabaseDB = Depends(get_db)
):
    """Check if a menu item is available."""
    # Get active menus for this restaurant
    menus = db.table("menus").select("id").eq(
        "account_id", restaurant_id
    ).eq("is_active", True).execute()

    menu_ids = [m["id"] for m in (menus.data or [])]

    if not menu_ids:
        return {
            "available": False,
            "item_name": item_name,
            "reason": "No active menu found"
        }

    # Get categories for these menus
    categories_result = db.table("menu_categories").select("id").in_(
        "menu_id", menu_ids
    ).execute()
    category_ids = [c["id"] for c in (categories_result.data or [])]

    if not category_ids:
        return {
            "available": False,
            "item_name": item_name,
            "reason": "Item not found on menu"
        }

    # Search for available item
    items_result = db.table("menu_items").select("*").in_(
        "category_id", category_ids
    ).ilike("name", f"%{item_name}%").eq(
        "is_available", True
    ).limit(1).execute()

    menu_item = items_result.data[0] if items_result.data else None

    if menu_item:
        return {
            "available": True,
            "item_name": menu_item["name"],
            "price": menu_item["price_cents"] / 100.0 if menu_item.get("price_cents") else 0.0,
            "description": menu_item.get("description")
        }
    else:
        # Check if item exists but unavailable
        unavailable_result = db.table("menu_items").select("*").in_(
            "category_id", category_ids
        ).ilike("name", f"%{item_name}%").limit(1).execute()

        unavailable = unavailable_result.data[0] if unavailable_result.data else None

        if unavailable:
            return {
                "available": False,
                "item_name": unavailable["name"],
                "reason": "Currently unavailable"
            }
        else:
            return {
                "available": False,
                "item_name": item_name,
                "reason": "Item not found on menu"
            }


@router.get(
    "/get-order-status",
    summary="Get order status",
    description="Check the status of an existing order. Use when customer asks about their order."
)
async def get_order_status(
    order_id: int = Query(..., description="Order ID to check"),
    db: SupabaseDB = Depends(get_db)
):
    """Get order status."""
    order = db.query_one("orders", {"id": order_id})

    if not order:
        return {
            "found": False,
            "message": "Order not found. Please check the order number."
        }

    return {
        "found": True,
        "order_id": order["id"],
        "status": order["status"],
        "customer_name": order["customer_name"],
        "total": order["total"] / 100.0 if order.get("total") else 0.0,
        "order_type": order.get("order_type"),
        "created_at": order["created_at"] if order.get("created_at") else None
    }


# ==================== Retell Custom Tool Endpoints (POST) ====================
# These POST endpoints are optimized for Retell AI Custom Tools integration.
# They accept args in the request body and extract call metadata automatically.


class RetellToolRequest(BaseModel):
    """Standard Retell Custom Tool request format."""
    call: Optional[Dict] = None
    args: Optional[Dict] = None


@router.post(
    "/tools/get-menu",
    summary="Get restaurant menu (Retell Tool)",
    description="Returns the full menu. Call this when customer asks about menu, prices, or what's available."
)
async def retell_get_menu(
    request: RetellToolRequest,
    db: SupabaseDB = Depends(get_db)
):
    """Retell Custom Tool: Get menu for restaurant."""
    args = request.args or {}
    restaurant_id = args.get("restaurant_id")
    category = args.get("category")

    if not restaurant_id:
        return {"error": "restaurant_id is required"}

    restaurant = db.query_one("restaurant_accounts", {"id": restaurant_id})

    if not restaurant:
        return {"error": "Restaurant not found"}

    # Get active menus for this restaurant
    menus = db.table("menus").select("id").eq(
        "account_id", restaurant_id
    ).eq("is_active", True).execute()

    menu_ids = [m["id"] for m in (menus.data or [])]

    if not menu_ids:
        return {
            "restaurant_name": restaurant["business_name"],
            "items": [],
            "categories": []
        }

    # Get categories for these menus
    categories_result = db.table("menu_categories").select("*").in_(
        "menu_id", menu_ids
    ).execute()

    all_categories = categories_result.data or []
    category_map = {cat["id"]: cat["name"] for cat in all_categories}
    category_ids = list(category_map.keys())

    if not category_ids:
        return {
            "restaurant_name": restaurant["business_name"],
            "items": [],
            "categories": []
        }

    # Get menu items
    if category:
        # Find matching category IDs
        matching_cat_ids = [
            cat["id"] for cat in all_categories
            if category.lower() in (cat.get("name") or "").lower()
        ]
        if matching_cat_ids:
            items_result = db.table("menu_items").select("*").in_(
                "category_id", matching_cat_ids
            ).eq("is_available", True).execute()
        else:
            items_result = type('obj', (object,), {'data': []})()
    else:
        items_result = db.table("menu_items").select("*").in_(
            "category_id", category_ids
        ).eq("is_available", True).execute()

    items = items_result.data or []

    return {
        "restaurant_name": restaurant["business_name"],
        "items": [
            {
                "name": item["name"],
                "description": item.get("description"),
                "price": f"${item['price_cents'] / 100:.2f}" if item.get("price_cents") else "$0.00",
                "category": category_map.get(item.get("category_id"), "")
            }
            for item in items
        ],
        "categories": sorted(set(cat["name"] for cat in all_categories if cat.get("name")))
    }


@router.post(
    "/tools/check-hours",
    summary="Check restaurant operating hours (Retell Tool)",
    description="Check if the restaurant is currently open and get today's hours. Use when customer asks about hours or if you're open."
)
async def retell_check_hours(
    request: RetellToolRequest,
    db: SupabaseDB = Depends(get_db)
):
    """Retell Custom Tool: Check operating hours."""
    args = request.args or {}
    restaurant_id = args.get("restaurant_id")

    if not restaurant_id:
        return {"error": "restaurant_id is required"}

    restaurant = db.query_one("restaurant_accounts", {"id": restaurant_id})

    if not restaurant:
        return {"error": "Restaurant not found"}

    now = datetime.now()
    day_name = now.strftime("%A")
    current_day = now.weekday()

    operating_days = restaurant.get("operating_days") or [0, 1, 2, 3, 4, 5, 6]
    is_operating_today = current_day in operating_days

    opening_time = restaurant.get("opening_time") or "09:00"
    closing_time = restaurant.get("closing_time") or "22:00"

    is_open = False
    if is_operating_today:
        try:
            open_hour, open_min = map(int, opening_time.split(":"))
            close_hour, close_min = map(int, closing_time.split(":"))
            current_minutes = now.hour * 60 + now.minute
            open_minutes = open_hour * 60 + open_min
            close_minutes = close_hour * 60 + close_min
            is_open = open_minutes <= current_minutes < close_minutes
        except:
            is_open = 9 <= now.hour < 22

    def format_time_12h(t):
        try:
            h, m = map(int, t.split(":"))
            period = "AM" if h < 12 else "PM"
            h = h % 12 or 12
            return f"{h}:{m:02d} {period}"
        except:
            return t

    if is_operating_today:
        hours_message = f"We're open today ({day_name}) from {format_time_12h(opening_time)} to {format_time_12h(closing_time)}."
    else:
        hours_message = f"We're closed today ({day_name})."

    if is_open:
        status_message = "We're currently open and accepting orders!"
    else:
        status_message = f"We're currently closed. We open at {format_time_12h(opening_time)}." if is_operating_today else "We're closed today."

    return {
        "is_open": is_open,
        "hours_today": hours_message,
        "status": status_message,
        "opening_time": format_time_12h(opening_time),
        "closing_time": format_time_12h(closing_time),
        "day": day_name
    }


@router.post(
    "/tools/create-order",
    summary="Create a food order (Retell Tool)",
    description="Creates a new order after confirming items with customer. Requires customer_name, customer_phone, and items list."
)
async def retell_create_order(
    request: RetellToolRequest,
    db: SupabaseDB = Depends(get_db)
):
    """Retell Custom Tool: Create an order."""
    args = request.args or {}
    restaurant_id = args.get("restaurant_id")
    customer_name = args.get("customer_name")
    customer_phone = args.get("customer_phone")
    items = args.get("items", [])  # List of {item_name, quantity}
    order_type = args.get("order_type", "pickup")
    delivery_address = args.get("delivery_address")
    special_instructions = args.get("special_instructions")

    if not restaurant_id:
        return {"error": "restaurant_id is required"}
    if not customer_name:
        return {"error": "customer_name is required"}
    if not customer_phone:
        return {"error": "customer_phone is required"}
    if not items:
        return {"error": "At least one item is required"}

    restaurant = db.query_one("restaurant_accounts", {"id": restaurant_id})

    if not restaurant:
        return {"error": "Restaurant not found"}

    # Get active menus for this restaurant
    menus = db.table("menus").select("id").eq(
        "account_id", restaurant_id
    ).eq("is_active", True).execute()

    menu_ids = [m["id"] for m in (menus.data or [])]

    if not menu_ids:
        return {"error": "No active menu found for restaurant"}

    # Get categories for these menus
    categories_result = db.table("menu_categories").select("id").in_(
        "menu_id", menu_ids
    ).execute()
    category_ids = [c["id"] for c in (categories_result.data or [])]

    # Process items and calculate total
    total = Decimal("0.00")
    order_items_data = []
    items_summary = []

    for item_req in items:
        item_name = item_req.get("item_name") or item_req.get("name")
        quantity = item_req.get("quantity", 1)

        if not item_name:
            continue

        items_result = db.table("menu_items").select("*").in_(
            "category_id", category_ids
        ).ilike("name", f"%{item_name}%").eq(
            "is_available", True
        ).limit(1).execute()

        menu_item = items_result.data[0] if items_result.data else None

        if not menu_item:
            return {"error": f"Item '{item_name}' not found on menu or unavailable"}

        item_price = Decimal(str(menu_item["price_cents"])) / 100
        total += item_price * quantity

        order_items_data.append({
            "menu_item_id": menu_item["id"],
            "name": menu_item["name"],
            "quantity": quantity,
            "unit_price": float(item_price)
        })
        items_summary.append(f"{quantity}x {menu_item['name']}")

    total_cents = int(total * 100)

    new_order = db.insert("orders", {
        "account_id": restaurant_id,
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "order_type": order_type,
        "delivery_address": delivery_address,
        "special_instructions": special_instructions,
        "status": "pending",
        "order_items": json.dumps(order_items_data),
        "subtotal": total_cents,
        "tax": 0,
        "total": total_cents
    })

    estimated_time = "15-20 minutes" if order_type == "pickup" else "30-45 minutes"

    logger.info(f"Retell order {new_order['id']} created: {items_summary}")

    return {
        "success": True,
        "order_id": new_order["id"],
        "total": f"${total:.2f}",
        "items_summary": ", ".join(items_summary),
        "estimated_time": estimated_time,
        "confirmation_message": f"Great! I've placed your order. Your order number is {new_order['id']}. The total is ${total:.2f}. It should be ready in about {estimated_time}."
    }


@router.post(
    "/tools/check-item",
    summary="Check if item is available (Retell Tool)",
    description="Check if a specific menu item is available and get its price. Use when customer asks about a specific dish."
)
async def retell_check_item(
    request: RetellToolRequest,
    db: SupabaseDB = Depends(get_db)
):
    """Retell Custom Tool: Check item availability."""
    args = request.args or {}
    restaurant_id = args.get("restaurant_id")
    item_name = args.get("item_name")

    if not restaurant_id or not item_name:
        return {"error": "restaurant_id and item_name are required"}

    # Get active menus for this restaurant
    menus = db.table("menus").select("id").eq(
        "account_id", restaurant_id
    ).eq("is_active", True).execute()

    menu_ids = [m["id"] for m in (menus.data or [])]

    if not menu_ids:
        return {
            "found": False,
            "message": f"Sorry, I couldn't find '{item_name}' on our menu."
        }

    # Get categories for these menus
    categories_result = db.table("menu_categories").select("id").in_(
        "menu_id", menu_ids
    ).execute()
    category_ids = [c["id"] for c in (categories_result.data or [])]

    if not category_ids:
        return {
            "found": False,
            "message": f"Sorry, I couldn't find '{item_name}' on our menu."
        }

    # Search for item
    items_result = db.table("menu_items").select("*").in_(
        "category_id", category_ids
    ).ilike("name", f"%{item_name}%").limit(1).execute()

    menu_item = items_result.data[0] if items_result.data else None

    if not menu_item:
        return {
            "found": False,
            "message": f"Sorry, I couldn't find '{item_name}' on our menu."
        }

    if not menu_item.get("is_available", True):
        return {
            "found": True,
            "available": False,
            "item_name": menu_item["name"],
            "message": f"Sorry, {menu_item['name']} is currently unavailable."
        }

    price_str = f"${menu_item['price_cents'] / 100:.2f}" if menu_item.get("price_cents") else "$0.00"
    return {
        "found": True,
        "available": True,
        "item_name": menu_item["name"],
        "price": price_str,
        "description": menu_item.get("description"),
        "message": f"Yes, we have {menu_item['name']} for {price_str}. {menu_item.get('description') or ''}"
    }
