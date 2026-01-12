"""
AI-powered conversation handler for voice and text interactions.

Uses local Ollama LLM to understand customer intent and extract booking information
from natural language conversations.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, date, time, timedelta
from sqlalchemy.orm import Session
import requests

from backend.models import Restaurant, Table, Customer, Booking, BookingStatus

logger = logging.getLogger(__name__)


class ConversationHandler:
    """Handles conversation flow using AI to understand intent."""

    def __init__(self):
        """Initialize conversation handler with Ollama."""
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama2")
        self.enabled = True  # Always enabled if Ollama is running

        # Test Ollama connection
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            if response.status_code == 200:
                logger.info(f"Ollama connection successful, using model: {self.ollama_model}")
            else:
                logger.warning("Ollama server not responding, AI features may be limited")
                self.enabled = False
        except Exception as e:
            logger.warning(f"Could not connect to Ollama at {self.ollama_url}: {str(e)}")
            self.enabled = False

    async def process_message(
        self,
        message: str,
        phone: str,
        context: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """
        Process customer message and determine response.

        Args:
            message: Customer's message (from speech-to-text or SMS)
            phone: Customer's phone number
            context: Conversation context (previous exchanges, gathered data)
            db: Database session

        Returns:
            Response dict with type, message, and next steps
        """
        if not self.enabled:
            return {
                "type": "error",
                "message": "AI service not available. Please try again later."
            }

        try:
            # Get or create customer
            customer = db.query(Customer).filter(Customer.phone == phone).first()

            # Get menu data for menu-aware responses
            # TODO: Associate phone number with restaurant account
            # For now, get the first restaurant account's menu
            from backend.models_platform import RestaurantAccount
            account = db.query(RestaurantAccount).first()
            menu_data = None
            if account:
                # Fetch full menu structure
                import requests
                try:
                    response = requests.get(f"http://localhost:8000/api/onboarding/accounts/{account.id}/menu-full")
                    if response.status_code == 200:
                        menu_data = response.json()
                except:
                    pass

            # Build prompt for Ollama
            system_prompt = self._build_system_prompt(context, customer, menu_data)
            user_message = self._build_user_message(message, context)

            # Call Ollama API
            full_prompt = f"{system_prompt}\n\n{user_message}"

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9
                    }
                },
                timeout=30
            )

            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code}")

            ai_response = response.json().get("response", "")

            # Parse AI response
            result = self._parse_ai_response(ai_response)

            # Handle different intents
            if result["intent"] == "menu_question":
                # AI already answered the question in the message
                return {
                    "type": "gather",
                    "message": result.get("message", "What else would you like to know about our menu?"),
                    "context": result.get("context", context)
                }

            elif result["intent"] == "place_order":
                return await self._handle_order(result, phone, db, context, account)

            elif result["intent"] == "book_table":
                return await self._handle_booking(result, phone, db, context)

            elif result["intent"] == "check_availability":
                return await self._handle_availability(result, db, context)

            elif result["intent"] == "cancel_booking":
                return await self._handle_cancellation(result, phone, db)

            elif result["intent"] == "need_more_info":
                return {
                    "type": "gather",
                    "message": result.get("question", "Could you provide more details?"),
                    "context": result.get("context", context)
                }

            elif result["intent"] == "goodbye":
                return {
                    "type": "goodbye",
                    "message": "Thank you for calling!"
                }

            else:
                return {
                    "type": "gather",
                    "message": result.get("message", "I can help you order food, make a reservation, or answer menu questions. What would you like?"),
                    "context": context
                }

        except Exception as e:
            logger.error(f"Error in conversation handler: {str(e)}", exc_info=True)
            return {
                "type": "error",
                "message": "I'm having trouble processing your request. Could you please try again?"
            }

    def _build_system_prompt(self, context: Dict, customer: Optional[Customer], menu_data: Optional[Dict] = None) -> str:
        """Build system prompt for Claude with menu awareness."""
        customer_info = ""
        if customer:
            customer_info = f"\nCustomer name: {customer.name}\nPrevious orders: {customer.total_bookings}"

        menu_info = ""
        if menu_data and menu_data.get("menus"):
            menu_info = "\n\nRESTAURANT MENU:\n"
            for menu in menu_data["menus"]:
                menu_info += f"\n{menu['name']}: {menu.get('description', '')}\n"
                for category in menu["categories"]:
                    menu_info += f"\n  {category['name']}:\n"
                    for item in category["items"]:
                        menu_info += f"    - {item['name']} (${item['price_cents']/100:.2f})"
                        if item.get('dietary_tags'):
                            menu_info += f" [{', '.join(item['dietary_tags'])}]"
                        menu_info += f"\n      {item['description']}\n"
                        if item.get('modifiers'):
                            menu_info += "      Customizations:\n"
                            for mod in item['modifiers']:
                                price_str = f" (+${mod['price_adjustment_cents']/100:.2f})" if mod['price_adjustment_cents'] > 0 else ""
                                menu_info += f"        • {mod['name']}{price_str}\n"

        return f"""You are a helpful AI assistant for {menu_data.get('business_name', 'our restaurant') if menu_data else 'a restaurant'}. You help with:

1. **Menu Questions**: Answer questions about items, prices, dietary options (vegetarian, vegan, halal, etc.)
2. **Takeout Orders**: Take food orders with customizations
3. **Reservations**: Book tables, check availability, cancel bookings

{menu_info}
{customer_info}

Current conversation context: {json.dumps(context)}

Respond with JSON in this format:
{{
    "intent": "menu_question|place_order|book_table|check_availability|cancel_booking|need_more_info|goodbye",
    "message": "response to customer",
    "order_items": [  // For place_order intent
        {{"item_name": "...", "quantity": 1, "modifiers": ["No tomato", "Extra sauce"], "price_cents": 1200}}
    ],
    "date": "YYYY-MM-DD" (for bookings),
    "time": "HH:MM:SS" (for bookings, 24-hour format),
    "party_size": number (for bookings),
    "customer_name": "name",
    "special_requests": "any special instructions",
    "question": "clarifying question" (if need_more_info),
    "context": {{
        "payment_method": "card|pay_on_arrival|cash",  // Extract from customer's response
        "delivery_address": "address if delivery"
    }} (updated context - merge with existing context)
}}

Today's date: {datetime.now().strftime('%Y-%m-%d')}
Be conversational, helpful, and accurate about menu items and pricing."""

    def _build_user_message(self, message: str, context: Dict) -> str:
        """Build user message with context."""
        return f"Customer says: {message}\n\nExtracted information so far: {json.dumps(context)}"

    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude's JSON response."""
        try:
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
            else:
                json_str = response_text.strip()

            return json.loads(json_str)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse AI response: {response_text}")
            return {"intent": "need_more_info", "question": "I didn't quite catch that. Could you repeat?"}

    async def _handle_booking(
        self,
        result: Dict,
        phone: str,
        db: Session,
        context: Dict
    ) -> Dict[str, Any]:
        """Handle booking creation."""
        # Check if we have all required information
        required = ["date", "time", "party_size"]
        missing = [field for field in required if field not in result]

        if missing:
            # Update context with what we have
            updated_context = {**context, **{k: v for k, v in result.items() if k in required}}
            return {
                "type": "gather",
                "message": self._get_missing_field_prompt(missing[0]),
                "context": updated_context
            }

        # Get or create customer
        customer = db.query(Customer).filter(Customer.phone == phone).first()
        if not customer:
            customer_name = result.get("customer_name", "Guest")
            customer = Customer(
                phone=phone,
                name=customer_name
            )
            db.add(customer)
            db.flush()

        # Get first restaurant (TODO: support multiple restaurants)
        restaurant = db.query(Restaurant).first()
        if not restaurant:
            return {
                "type": "error",
                "message": "I'm sorry, we're not taking reservations at this time."
            }

        # Parse date and time
        booking_date = datetime.strptime(result["date"], "%Y-%m-%d").date()
        booking_time = datetime.strptime(result["time"], "%H:%M:%S").time()

        # Find available table
        available_table = self._find_available_table(
            restaurant.id,
            booking_date,
            booking_time,
            result["party_size"],
            db
        )

        if not available_table:
            return {
                "type": "gather",
                "message": f"I'm sorry, we don't have a table available for {result['party_size']} at that time. Would you like to try a different time?",
                "context": context
            }

        # Create booking
        booking = Booking(
            restaurant_id=restaurant.id,
            table_id=available_table.id,
            customer_id=customer.id,
            booking_date=booking_date,
            booking_time=booking_time,
            party_size=result["party_size"],
            duration_minutes=120,
            status=BookingStatus.CONFIRMED
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)

        # Send SMS confirmation
        try:
            from backend.services.sms_service import sms_service
            sms_service.send_booking_confirmation(booking, customer, restaurant)
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")

        return {
            "type": "confirmation",
            "booking": {
                "restaurant_name": restaurant.name,
                "booking_date": booking_date,
                "booking_time": booking_time,
                "party_size": result["party_size"],
                "customer_name": customer.name,
                "confirmation_id": booking.id
            }
        }

    async def _handle_availability(
        self,
        result: Dict,
        db: Session,
        context: Dict
    ) -> Dict[str, Any]:
        """Handle availability check."""
        # Check if we have date and party size
        if "date" not in result or "party_size" not in result:
            updated_context = {**context, **{k: v for k, v in result.items() if k in ["date", "party_size"]}}
            missing = "date" if "date" not in result else "party_size"
            return {
                "type": "gather",
                "message": self._get_missing_field_prompt(missing),
                "context": updated_context
            }

        # Get restaurant
        restaurant = db.query(Restaurant).first()
        if not restaurant:
            return {"type": "error", "message": "Restaurant not available"}

        # Find available time slots
        booking_date = datetime.strptime(result["date"], "%Y-%m-%d").date()
        available_times = self._get_available_times(
            restaurant.id,
            booking_date,
            result["party_size"],
            db
        )

        return {
            "type": "availability",
            "available_times": available_times,
            "requested_date": booking_date,
            "party_size": result["party_size"],
            "context": {**context, "date": result["date"], "party_size": result["party_size"]}
        }

    async def _handle_cancellation(
        self,
        result: Dict,
        phone: str,
        db: Session
    ) -> Dict[str, Any]:
        """Handle booking cancellation."""
        customer = db.query(Customer).filter(Customer.phone == phone).first()
        if not customer:
            return {
                "type": "error",
                "message": "I don't have any bookings under this phone number."
            }

        # Find active bookings
        active_bookings = db.query(Booking).filter(
            Booking.customer_id == customer.id,
            Booking.status == BookingStatus.CONFIRMED,
            Booking.booking_date >= datetime.now().date()
        ).all()

        if not active_bookings:
            return {
                "type": "gather",
                "message": "I don't see any upcoming reservations. Is there anything else I can help you with?"
            }

        # Cancel the most recent booking
        booking = active_bookings[0]
        booking.status = BookingStatus.CANCELLED
        db.commit()

        # Send cancellation SMS
        try:
            from backend.services.sms_service import sms_service
            restaurant = db.query(Restaurant).filter(Restaurant.id == booking.restaurant_id).first()
            if restaurant:
                sms_service.send_cancellation_confirmation(booking, customer, restaurant)
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")

        return {
            "type": "gather",
            "message": f"I've cancelled your reservation for {booking.booking_date.strftime('%B %d')}. Is there anything else I can help you with?"
        }

    def _get_missing_field_prompt(self, field: str) -> str:
        """Get prompt for missing field."""
        prompts = {
            "date": "What date would you like to make a reservation for?",
            "time": "What time would you prefer?",
            "party_size": "How many people will be dining?",
            "customer_name": "May I have your name for the reservation?"
        }
        return prompts.get(field, "Could you provide more details?")

    def _find_available_table(
        self,
        restaurant_id: int,
        booking_date: date,
        booking_time: time,
        party_size: int,
        db: Session
    ) -> Optional[Table]:
        """Find available table for booking."""
        # Get all active tables with sufficient capacity
        tables = db.query(Table).filter(
            Table.restaurant_id == restaurant_id,
            Table.capacity >= party_size,
            Table.is_active == True
        ).all()

        # Check each table for conflicts
        for table in tables:
            conflicts = db.query(Booking).filter(
                Booking.table_id == table.id,
                Booking.booking_date == booking_date,
                Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING])
            ).all()

            # Check time overlap
            start_datetime = datetime.combine(booking_date, booking_time)
            end_datetime = start_datetime + timedelta(minutes=120)

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
        self,
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

        # Generate time slots from opening to closing (every 30 minutes)
        current_time = datetime.combine(booking_date, restaurant.opening_time)
        closing_time = datetime.combine(booking_date, restaurant.closing_time)

        while current_time < closing_time - timedelta(hours=1):  # Stop 1 hour before closing
            # Check if table available at this time
            if self._find_available_table(restaurant_id, booking_date, current_time.time(), party_size, db):
                available_times.append(current_time.time())

            current_time += timedelta(minutes=30)

        return available_times[:5]  # Return first 5 available slots


# Global conversation handler instance
async def _handle_order(
    self,
    result: Dict,
    phone: str,
    db: Session,
    context: Dict,
    account: 'RestaurantAccount'
) -> Dict[str, Any]:
    """Handle takeout order placement."""
    import json as json_lib
    from backend.models import Order, OrderStatus

    # Get or create customer
    from backend.models import Customer
    customer = db.query(Customer).filter(Customer.phone == phone).first()
    if not customer:
        customer_name = result.get("customer_name", "Guest")
        customer = Customer(phone=phone, name=customer_name)
        db.add(customer)
        db.flush()

    # Get first restaurant location for this account
    from backend.models import Restaurant
    restaurant = db.query(Restaurant).filter(Restaurant.account_id == account.id).first()
    if not restaurant:
        return {
            "type": "error",
            "message": "Sorry, we're not taking orders at this time."
        }

    # Parse order items
    order_items = result.get("order_items", [])
    if not order_items:
        return {
            "type": "gather",
            "message": "What would you like to order?",
            "context": context
        }

    # Calculate totals
    subtotal = sum(item.get("price_cents", 0) * item.get("quantity", 1) for item in order_items)
    tax = int(subtotal * 0.08)  # 8% tax
    delivery_fee = 500  # $5 delivery fee
    total = subtotal + tax + delivery_fee

    # Check if payment method is specified
    payment_method = context.get("payment_method")

    if not payment_method:
        # Ask how customer wants to pay
        items_text = "\\n".join([
            f"- {item.get('quantity', 1)}x {item.get('item_name')}"
            + (f" ({', '.join(item.get('modifiers', []))})" if item.get('modifiers') else "")
            for item in order_items
        ])

        return {
            "type": "gather",
            "message": f"""Perfect! Your order:

{items_text}

Total: ${total / 100:.2f}

Would you like to pay now by card or pay when you pick up?""",
            "context": {
                **context,
                "pending_order": {
                    "items": order_items,
                    "subtotal": subtotal,
                    "tax": tax,
                    "delivery_fee": delivery_fee,
                    "total": total
                }
            }
        }

    # Create order with payment info
    order = Order(
        restaurant_id=restaurant.id,
        customer_id=customer.id,
        customer_name=customer.name,
        customer_phone=phone,
        order_date=datetime.now(),
        delivery_address=context.get("delivery_address", "Pickup"),
        order_items=json_lib.dumps(order_items),
        subtotal=subtotal,
        tax=tax,
        delivery_fee=delivery_fee if context.get("delivery_address") else 0,
        total=total,
        status=OrderStatus.PENDING.value,
        payment_method=payment_method,
        payment_status="paid" if payment_method == "card" else "unpaid",
        special_requests=result.get("special_requests")
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # Send SMS confirmation
    try:
        from backend.services.sms_service import sms_service
        items_text = ", ".join([
            f"{item.get('quantity', 1)}x {item.get('item_name')}"
            for item in order_items
        ])
        confirmation_msg = f"""Your order #{order.id} is confirmed!

{items_text}

Total: ${total / 100:.2f}
Payment: {payment_method}

We'll have it ready in 15-20 minutes. Thank you!"""
        sms_service.send_sms(phone, confirmation_msg)
    except Exception as e:
        logger.error(f"Failed to send order confirmation SMS: {str(e)}")

    # Print to kitchen
    try:
        from backend.services.kitchen_printer import kitchen_printer
        order_dict = {
            "id": order.id,
            "customer_name": customer.name,
            "customer_phone": phone,
            "order_items": json_lib.dumps(order_items),
            "total": total,
            "payment_method": payment_method,
            "payment_status": order.payment_status,
            "delivery_address": order.delivery_address,
            "special_requests": result.get("special_requests")
        }
        kitchen_printer.print_order(order_dict)
        logger.info(f"Order #{order.id} printed to kitchen")
    except Exception as e:
        logger.error(f"Failed to print order to kitchen: {str(e)}")

    # Build confirmation message
    message = f"""Great! Your order #{order.id} is confirmed. We'll have it ready in about 15-20 minutes.

{"Payment will be processed when you pick up." if payment_method == "pay_on_arrival" else "Payment confirmed."}

Is there anything else I can help you with?"""

    return {
        "type": "gather",
        "message": message,
        "context": {"order_id": order.id}
    }


# Global conversation handler instance
conversation_handler = ConversationHandler()
