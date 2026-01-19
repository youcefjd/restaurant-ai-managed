"""
Retell AI custom functions webhook endpoint.

This endpoint handles function calls from Retell AI agents during voice conversations.
Retell will call these functions when the agent needs to perform actions like:
- Querying menu items
- Checking table availability
- Creating reservations
- Placing orders
- Getting operating hours
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, date, time, timedelta
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Restaurant, Table, Customer, Booking, BookingStatus, Order, OrderStatus
from backend.models_platform import RestaurantAccount, Menu, MenuCategory, MenuItem, MenuModifier
from backend.services.sms_service import sms_service
from backend.services.kitchen_printer import kitchen_printer

router = APIRouter()
logger = logging.getLogger(__name__)


def normalize_phone(phone: str) -> str:
    """Normalize phone number to E.164 format."""
    if not phone:
        return ""
    phone = phone.strip()
    if not phone.startswith('+'):
        phone = '+' + phone
    return phone


@router.post("/custom-functions")
async def retell_custom_functions(request: Request, db: Session = Depends(get_db)):
    """
    Handle Retell AI custom function calls during voice conversations.
    
    Retell will call this endpoint with function names and parameters when
    the agent needs to perform actions like creating orders or reservations.
    
    Expected request format from Retell:
    {
        "function_name": "create_order",
        "parameters": {...},
        "call_metadata": {
            "from_number": "+1234567890",
            "to_number": "+0987654321",
            "call_id": "unique-call-id"
        }
    }
    """
    try:
        body = await request.json()
        function_name = body.get("function_name")
        parameters = body.get("parameters", {})
        call_metadata = body.get("call_metadata", {})
        
        logger.info(f"Retell custom function call: {function_name} with params: {parameters}")
        
        # Get restaurant from call metadata (to_number is restaurant's Twilio number)
        to_number = normalize_phone(call_metadata.get("to_number", ""))
        restaurant = None
        if to_number:
            restaurant = db.query(RestaurantAccount).filter(
                RestaurantAccount.twilio_phone_number == to_number
            ).first()
        
        if not restaurant:
            logger.warning(f"No restaurant found for number: {to_number}")
            return {
                "status": "error",
                "message": "Restaurant not found"
            }
        
        # Route to appropriate function handler
        if function_name == "get_menu_items":
            return await handle_get_menu_items(restaurant.id, parameters, db)
        elif function_name == "check_table_availability":
            return await handle_check_availability(restaurant.id, parameters, db)
        elif function_name == "create_reservation":
            return await handle_create_reservation(restaurant.id, parameters, call_metadata, db)
        elif function_name == "create_order":
            return await handle_create_order(restaurant.id, parameters, call_metadata, db)
        elif function_name == "get_operating_hours":
            return await handle_get_operating_hours(restaurant, parameters)
        else:
            logger.warning(f"Unknown function name: {function_name}")
            return {
                "status": "error",
                "message": f"Unknown function: {function_name}"
            }
            
    except Exception as e:
        logger.error(f"Error handling Retell custom function: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": f"Internal error: {str(e)}"
        }


async def handle_get_menu_items(restaurant_id: int, params: Dict, db: Session) -> Dict[str, Any]:
    """Get menu items for restaurant. Can filter by category, dietary tags, or search query."""
    try:
        account = db.query(RestaurantAccount).filter(RestaurantAccount.id == restaurant_id).first()
        if not account:
            return {"status": "error", "message": "Restaurant not found"}
        
        menus = db.query(Menu).filter(Menu.account_id == account.id, Menu.is_active == True).all()
        
        all_items = []
        for menu in menus:
            categories = db.query(MenuCategory).filter(MenuCategory.menu_id == menu.id).all()
            for category in categories:
                items_query = db.query(MenuItem).filter(
                    MenuItem.category_id == category.id,
                    MenuItem.is_available == True
                )
                
                # Apply filters
                search_query = params.get("search_query", "").lower()
                dietary_tag = params.get("dietary_tag")
                category_name = params.get("category_name")
                
                if search_query:
                    items_query = items_query.filter(
                        (MenuItem.name.ilike(f"%{search_query}%")) |
                        (MenuItem.description.ilike(f"%{search_query}%"))
                    )
                
                if dietary_tag:
                    items_query = items_query.filter(
                        MenuItem.dietary_tags.contains([dietary_tag])
                    )
                
                items = items_query.all()
                
                for item in items:
                    modifiers = db.query(MenuModifier).filter(MenuModifier.item_id == item.id).all()
                    all_items.append({
                        "id": item.id,
                        "name": item.name,
                        "description": item.description,
                        "price_cents": item.price_cents,
                        "price_dollars": item.price_cents / 100.0,
                        "category": category.name,
                        "dietary_tags": item.dietary_tags or [],
                        "modifiers": [
                            {
                                "name": mod.name,
                                "price_adjustment_cents": mod.price_adjustment_cents
                            }
                            for mod in modifiers
                        ]
                    })
        
        return {
            "status": "success",
            "items": all_items,
            "count": len(all_items)
        }
    except Exception as e:
        logger.error(f"Error getting menu items: {str(e)}")
        return {"status": "error", "message": str(e)}


async def handle_check_availability(restaurant_id: int, params: Dict, db: Session) -> Dict[str, Any]:
    """Check table availability for a given date, time, and party size."""
    try:
        # Parse parameters
        booking_date_str = params.get("date")
        party_size = params.get("party_size")
        booking_time_str = params.get("time")  # Optional
        
        if not booking_date_str or not party_size:
            return {
                "status": "error",
                "message": "Missing required parameters: date and party_size"
            }
        
        booking_date = datetime.strptime(booking_date_str, "%Y-%m-%d").date()
        booking_time = None
        if booking_time_str:
            booking_time = datetime.strptime(booking_time_str, "%H:%M:%S").time()
        
        # Get restaurant location
        restaurant = db.query(Restaurant).filter(Restaurant.account_id == restaurant_id).first()
        if not restaurant:
            return {"status": "error", "message": "Restaurant location not found"}
        
        # Find available tables
        tables = db.query(Table).filter(
            Table.restaurant_id == restaurant.id,
            Table.capacity >= party_size,
            Table.is_active == True
        ).all()
        
        if booking_time:
            # Check specific time
            available_table = _find_available_table(restaurant.id, booking_date, booking_time, party_size, db)
            return {
                "status": "success",
                "available": available_table is not None,
                "has_tables": len(tables) > 0
            }
        else:
            # Get all available time slots for the day
            available_times = _get_available_times(restaurant.id, booking_date, party_size, db)
            return {
                "status": "success",
                "available_times": [t.strftime("%H:%M") for t in available_times],
                "available_count": len(available_times)
            }
            
    except Exception as e:
        logger.error(f"Error checking availability: {str(e)}")
        return {"status": "error", "message": str(e)}


async def handle_create_reservation(
    restaurant_id: int,
    params: Dict,
    call_metadata: Dict,
    db: Session
) -> Dict[str, Any]:
    """Create a table reservation."""
    try:
        # Parse parameters
        booking_date_str = params.get("date")
        booking_time_str = params.get("time")
        party_size = params.get("party_size")
        customer_name = params.get("customer_name", "Guest")
        customer_phone = normalize_phone(call_metadata.get("from_number", ""))
        
        if not booking_date_str or not booking_time_str or not party_size:
            return {
                "status": "error",
                "message": "Missing required parameters: date, time, and party_size"
            }
        
        booking_date = datetime.strptime(booking_date_str, "%Y-%m-%d").date()
        booking_time = datetime.strptime(booking_time_str, "%H:%M:%S").time()
        
        # Get or create customer
        customer = db.query(Customer).filter(Customer.phone == customer_phone).first()
        if not customer:
            customer = Customer(phone=customer_phone, name=customer_name)
            db.add(customer)
            db.flush()
        
        # Get restaurant location
        restaurant = db.query(Restaurant).filter(Restaurant.account_id == restaurant_id).first()
        if not restaurant:
            return {"status": "error", "message": "Restaurant location not found"}
        
        # Find available table
        available_table = _find_available_table(restaurant.id, booking_date, booking_time, party_size, db)
        if not available_table:
            return {
                "status": "error",
                "message": "No tables available at that time",
                "suggestion": "Try a different time"
            }
        
        # Create booking
        booking = Booking(
            restaurant_id=restaurant.id,
            table_id=available_table.id,
            customer_id=customer.id,
            booking_date=booking_date,
            booking_time=booking_time,
            party_size=party_size,
            duration_minutes=90,
            status=BookingStatus.CONFIRMED
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)
        
        # Send SMS confirmation
        try:
            sms_service.send_booking_confirmation(booking, customer, restaurant)
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
        
        return {
            "status": "success",
            "booking_id": booking.id,
            "date": booking_date_str,
            "time": booking_time_str,
            "party_size": party_size,
            "table_number": available_table.table_number,
            "confirmation_number": booking.id
        }
        
    except Exception as e:
        logger.error(f"Error creating reservation: {str(e)}")
        db.rollback()
        return {"status": "error", "message": str(e)}


async def handle_create_order(
    restaurant_id: int,
    params: Dict,
    call_metadata: Dict,
    db: Session
) -> Dict[str, Any]:
    """Create a takeout/delivery order."""
    try:
        # Parse parameters
        order_items = params.get("items", [])  # List of {item_name, quantity, modifiers, price_cents}
        customer_name = params.get("customer_name", "")
        customer_phone = normalize_phone(call_metadata.get("from_number", ""))
        delivery_address = params.get("delivery_address")
        payment_method = params.get("payment_method", "pickup")  # "card" or "pickup"
        special_instructions = params.get("special_instructions", "")
        
        if not order_items:
            return {"status": "error", "message": "No items in order"}
        
        if not customer_name:
            return {"status": "error", "message": "Customer name required"}
        
        # Get or create customer
        customer = db.query(Customer).filter(Customer.phone == customer_phone).first()
        if customer:
            if customer_name and customer_name != customer.name:
                customer.name = customer_name
                db.flush()
        else:
            customer = Customer(phone=customer_phone, name=customer_name)
            db.add(customer)
            db.flush()
        
        # Get restaurant location
        account = db.query(RestaurantAccount).filter(RestaurantAccount.id == restaurant_id).first()
        restaurant = db.query(Restaurant).filter(Restaurant.account_id == restaurant_id).first()
        if not restaurant:
            return {"status": "error", "message": "Restaurant location not found"}
        
        # Calculate totals
        subtotal = sum(item.get("price_cents", 0) * item.get("quantity", 1) for item in order_items)
        tax = int(subtotal * 0.08)  # 8% tax
        delivery_fee = 500 if delivery_address else 0  # $5 delivery fee
        total = subtotal + tax + delivery_fee
        
        # Create order
        order = Order(
            restaurant_id=restaurant.id,
            customer_id=customer.id,
            customer_name=customer.name,
            customer_phone=customer_phone,
            order_date=datetime.now(),
            delivery_address=delivery_address or "Pickup",
            order_items=json.dumps(order_items),
            subtotal=subtotal,
            tax=tax,
            delivery_fee=delivery_fee,
            total=total,
            status=OrderStatus.PENDING.value,
            payment_method=payment_method,
            payment_status="paid" if payment_method == "card" else "unpaid",
            special_instructions=special_instructions
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        
        # Send SMS confirmation
        try:
            items_text = ", ".join([
                f"{item.get('quantity', 1)}x {item.get('item_name')}"
                for item in order_items
            ])
            confirmation_msg = f"""Your order #{order.id} is confirmed!

{items_text}

Total: ${total / 100:.2f}
Payment: {payment_method}

We'll have it ready in 15-20 minutes. Thank you!"""
            from_number = account.twilio_phone_number if account else None
            sms_service.send_sms(customer_phone, confirmation_msg, from_number=from_number)
        except Exception as e:
            logger.error(f"Failed to send order confirmation SMS: {str(e)}")
        
        # Print to kitchen
        try:
            order_dict = {
                "id": order.id,
                "customer_name": customer.name,
                "customer_phone": customer_phone,
                "order_items": json.dumps(order_items),
                "total": total,
                "payment_method": payment_method,
                "payment_status": order.payment_status,
                "delivery_address": order.delivery_address,
                "special_requests": special_instructions
            }
            kitchen_printer.print_order(order_dict)
        except Exception as e:
            logger.error(f"Failed to print order to kitchen: {str(e)}")
        
        return {
            "status": "success",
            "order_id": order.id,
            "total": total,
            "total_dollars": total / 100.0,
            "estimated_time": "15-20 minutes",
            "confirmation_number": order.id
        }
        
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        db.rollback()
        return {"status": "error", "message": str(e)}


async def handle_get_operating_hours(restaurant: RestaurantAccount, params: Dict) -> Dict[str, Any]:
    """Get operating hours for restaurant."""
    try:
        return {
            "status": "success",
            "opening_time": restaurant.opening_time or "N/A",
            "closing_time": restaurant.closing_time or "N/A",
            "operating_days": restaurant.operating_days or [],
            "formatted": f"{restaurant.opening_time} - {restaurant.closing_time}" if restaurant.opening_time and restaurant.closing_time else "Hours not set"
        }
    except Exception as e:
        logger.error(f"Error getting operating hours: {str(e)}")
        return {"status": "error", "message": str(e)}


# Helper functions (reused from conversation_handler)
def _find_available_table(
    restaurant_id: int,
    booking_date: date,
    booking_time: time,
    party_size: int,
    db: Session
) -> Optional[Table]:
    """Find available table for booking."""
    tables = db.query(Table).filter(
        Table.restaurant_id == restaurant_id,
        Table.capacity >= party_size,
        Table.is_active == True
    ).all()

    for table in tables:
        conflicts = db.query(Booking).filter(
            Booking.table_id == table.id,
            Booking.booking_date == booking_date,
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING])
        ).all()

        start_datetime = datetime.combine(booking_date, booking_time)
        end_datetime = start_datetime + timedelta(minutes=90)

        has_conflict = False
        for conflict in conflicts:
            conflict_start = datetime.combine(booking_date, conflict.booking_time)
            conflict_end = conflict_start + timedelta(minutes=conflict.duration_minutes)

            if not (end_datetime <= conflict_start or start_datetime >= conflict_end):
                has_conflict = True
                break

        if not has_conflict:
            return table

    return None


def _get_available_times(
    restaurant_id: int,
    booking_date: date,
    party_size: int,
    db: Session
) -> List[time]:
    """Get list of available time slots."""
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        return []

    available_times = []
    
    # Default hours if not set
    opening_str = restaurant.opening_time or "11:00"
    closing_str = restaurant.closing_time or "22:00"
    
    try:
        opening_hour, opening_min = map(int, opening_str.split(":"))
        closing_hour, closing_min = map(int, closing_str.split(":"))
        
        current_time = datetime.combine(booking_date, time(opening_hour, opening_min))
        closing_time = datetime.combine(booking_date, time(closing_hour, closing_min))
        
        while current_time < closing_time - timedelta(hours=1):
            if _find_available_table(restaurant_id, booking_date, current_time.time(), party_size, db):
                available_times.append(current_time.time())
            current_time += timedelta(minutes=30)
    except Exception as e:
        logger.error(f"Error parsing hours: {e}")
    
    return available_times[:5]  # Return first 5 available slots
