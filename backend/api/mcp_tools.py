"""
MCP Tools API for Restaurant Voice Agent.

Exposes restaurant operations as MCP tools that Retell's LLM can call.
Tools: get_menu, create_order, get_restaurant_info, check_hours
"""

import logging
from typing import Optional, List, Dict
from datetime import datetime, date, time
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models_platform import RestaurantAccount, MenuItem, Menu, MenuCategory
from backend.models import Order

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
    db: Session = Depends(get_db)
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
    restaurant = db.query(RestaurantAccount).filter(
        RestaurantAccount.twilio_phone_number == phone_number
    ).first()

    if not restaurant:
        # Try without + prefix
        clean_number = phone_number.lstrip('+')
        restaurant = db.query(RestaurantAccount).filter(
            RestaurantAccount.twilio_phone_number.like(f"%{clean_number}")
        ).first()

    if not restaurant:
        return {
            "found": False,
            "message": f"No restaurant found for phone {phone_number}"
        }

    return {
        "found": True,
        "restaurant_id": restaurant.id,
        "restaurant_name": restaurant.business_name,
        "phone": restaurant.owner_phone,
        "greeting": f"Thanks for calling {restaurant.business_name}! How can I help you today?"
    }


@router.get(
    "/get-restaurant-by-phone",
    summary="Get restaurant by phone number",
    description="Look up which restaurant is associated with a phone number."
)
async def get_restaurant_by_phone(
    phone_number: str = Query(..., description="The phone number that received the call (E.164 format like +18329254593)"),
    db: Session = Depends(get_db)
):
    """Look up restaurant by the phone number that received the call."""
    # Look up restaurant by their assigned Twilio/Retell phone number
    restaurant = db.query(RestaurantAccount).filter(
        RestaurantAccount.twilio_phone_number == phone_number
    ).first()

    if not restaurant:
        # Try without + prefix
        clean_number = phone_number.lstrip('+')
        restaurant = db.query(RestaurantAccount).filter(
            RestaurantAccount.twilio_phone_number.like(f"%{clean_number}")
        ).first()

    if not restaurant:
        return {
            "found": False,
            "message": "No restaurant found for this phone number"
        }

    return {
        "found": True,
        "restaurant_id": restaurant.id,
        "restaurant_name": restaurant.business_name,
        "phone": restaurant.owner_phone,
        "greeting": f"Hi, thanks for calling {restaurant.business_name}! How can I help you today?"
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
    db: Session = Depends(get_db)
):
    """Get the restaurant menu."""
    # Get restaurant
    restaurant = db.query(RestaurantAccount).filter(
        RestaurantAccount.id == restaurant_id
    ).first()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # Get menu items through Menu -> MenuCategory -> MenuItem
    query = db.query(MenuItem).join(
        MenuCategory, MenuItem.category_id == MenuCategory.id
    ).join(
        Menu, MenuCategory.menu_id == Menu.id
    ).filter(
        Menu.account_id == restaurant_id,
        Menu.is_active == True,
        MenuItem.is_available == True
    )

    if category:
        query = query.filter(MenuCategory.name.ilike(f"%{category}%"))

    items = query.all()

    # Get unique categories
    all_categories = db.query(MenuCategory).join(
        Menu, MenuCategory.menu_id == Menu.id
    ).filter(
        Menu.account_id == restaurant_id,
        Menu.is_active == True
    ).all()
    categories = list(set(cat.name for cat in all_categories if cat.name))

    # Get category names for items
    category_map = {cat.id: cat.name for cat in all_categories}

    return MenuResponse(
        restaurant_name=restaurant.business_name,
        items=[
            MenuItemResponse(
                id=item.id,
                name=item.name,
                description=item.description,
                price=item.price_cents / 100.0 if item.price_cents else 0.0,
                category=category_map.get(item.category_id, ""),
                is_available=item.is_available
            )
            for item in items
        ],
        categories=sorted(categories)
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
    db: Session = Depends(get_db)
):
    """Create a new order."""
    # Get restaurant
    restaurant = db.query(RestaurantAccount).filter(
        RestaurantAccount.id == restaurant_id
    ).first()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # Look up menu items and calculate total
    total = Decimal("0.00")
    order_items_data = []
    items_summary_parts = []

    for item_req in order.items:
        # Find menu item by name through Menu -> MenuCategory -> MenuItem
        menu_item = db.query(MenuItem).join(
            MenuCategory, MenuItem.category_id == MenuCategory.id
        ).join(
            Menu, MenuCategory.menu_id == Menu.id
        ).filter(
            Menu.account_id == restaurant_id,
            MenuItem.name.ilike(f"%{item_req.item_name}%"),
            MenuItem.is_available == True
        ).first()

        if not menu_item:
            raise HTTPException(
                status_code=400,
                detail=f"Item '{item_req.item_name}' not found on menu"
            )

        # price_cents is in cents, convert to dollars for calculation
        item_price = Decimal(str(menu_item.price_cents)) / 100
        item_total = item_price * item_req.quantity
        total += item_total

        order_items_data.append({
            "menu_item": menu_item,
            "quantity": item_req.quantity,
            "special_instructions": item_req.special_instructions,
            "price": item_price
        })

        items_summary_parts.append(f"{item_req.quantity}x {menu_item.name}")

    # Build order items JSON
    import json
    order_items_json = json.dumps([
        {
            "menu_item_id": item["menu_item"].id,
            "name": item["menu_item"].name,
            "quantity": item["quantity"],
            "unit_price": float(item["price"]) if item["price"] else 0.0,
            "special_instructions": item["special_instructions"]
        }
        for item in order_items_data
    ])

    # Convert total to cents
    total_cents = int(total * 100)

    # Create order
    new_order = Order(
        account_id=restaurant_id,
        customer_name=order.customer_name,
        customer_phone=order.customer_phone,
        order_type=order.order_type,
        delivery_address=order.delivery_address,
        special_instructions=order.special_instructions,
        status="pending",
        order_items=order_items_json,
        subtotal=total_cents,
        tax=0,
        total=total_cents
    )
    db.add(new_order)
    db.commit()

    # Estimate time based on order type
    estimated_time = "15-20 minutes" if order.order_type == "pickup" else "30-45 minutes"

    logger.info(f"Order {new_order.id} created for {order.customer_name}: {items_summary_parts}")

    return OrderResponse(
        order_id=new_order.id,
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
    db: Session = Depends(get_db)
):
    """Get restaurant information."""
    restaurant = db.query(RestaurantAccount).filter(
        RestaurantAccount.id == restaurant_id
    ).first()

    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # Determine if open (simplified - assumes 11am-10pm daily)
    now = datetime.now()
    is_open = 11 <= now.hour < 22

    # Get hours string
    day_name = now.strftime("%A")
    hours_today = "11:00 AM - 10:00 PM"  # Default hours

    return RestaurantInfoResponse(
        name=restaurant.business_name,
        phone=restaurant.owner_phone,
        address=getattr(restaurant, 'address', None),
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
    db: Session = Depends(get_db)
):
    """Check if a menu item is available."""
    menu_item = db.query(MenuItem).join(
        MenuCategory, MenuItem.category_id == MenuCategory.id
    ).join(
        Menu, MenuCategory.menu_id == Menu.id
    ).filter(
        Menu.account_id == restaurant_id,
        MenuItem.name.ilike(f"%{item_name}%"),
        MenuItem.is_available == True
    ).first()

    if menu_item:
        return {
            "available": True,
            "item_name": menu_item.name,
            "price": menu_item.price_cents / 100.0 if menu_item.price_cents else 0.0,
            "description": menu_item.description
        }
    else:
        # Check if item exists but unavailable
        unavailable = db.query(MenuItem).join(
            MenuCategory, MenuItem.category_id == MenuCategory.id
        ).join(
            Menu, MenuCategory.menu_id == Menu.id
        ).filter(
            Menu.account_id == restaurant_id,
            MenuItem.name.ilike(f"%{item_name}%")
        ).first()

        if unavailable:
            return {
                "available": False,
                "item_name": unavailable.name,
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
    db: Session = Depends(get_db)
):
    """Get order status."""
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        return {
            "found": False,
            "message": "Order not found. Please check the order number."
        }

    return {
        "found": True,
        "order_id": order.id,
        "status": order.status,
        "customer_name": order.customer_name,
        "total": order.total / 100.0 if order.total else 0.0,
        "order_type": order.order_type,
        "created_at": order.created_at.isoformat() if order.created_at else None
    }
