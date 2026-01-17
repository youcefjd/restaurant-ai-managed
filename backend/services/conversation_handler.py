"""
AI-powered conversation handler for voice and text interactions.

Uses Gemini or OpenAI via openai_service to understand customer intent and extract booking information
from natural language conversations.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, date, time, timedelta
from sqlalchemy.orm import Session
from pathlib import Path

from backend.models import Restaurant, Table, Customer, Booking, BookingStatus
from backend.services.openai_service import llm_service

logger = logging.getLogger(__name__)


class ConversationHandler:
    """Handles conversation flow using AI to understand intent."""

    def __init__(self):
        """Initialize conversation handler with LLM service."""
        self.llm_service = llm_service
        self.enabled = llm_service.is_enabled()
        
        # Load system prompt template
        self.system_prompt_template = self._load_system_prompt_template()
        
        if self.enabled:
            logger.info(f"Conversation handler initialized with LLM provider: {llm_service.get_provider()}")
        else:
            logger.warning("LLM service not available - conversation handler disabled")
    
    def _load_system_prompt_template(self) -> str:
        """Load system prompt template from markdown file."""
        try:
            # Get the project root directory
            current_dir = Path(__file__).parent.parent.parent
            template_path = current_dir / "VOICE_AGENT_SYSTEM_PROMPT.md"
            
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    template = f.read()
                logger.info(f"Loaded system prompt template from {template_path}")
                return template
            else:
                logger.warning(f"System prompt template not found at {template_path}, using default")
                return ""  # Will fall back to old prompt building
        except Exception as e:
            logger.error(f"Failed to load system prompt template: {str(e)}")
            return ""

    async def process_message(
        self,
        message: str,
        phone: str,
        restaurant_id: int,
        context: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """
        Process customer message and determine response.

        Args:
            message: Customer's message (from speech-to-text or SMS)
            phone: Customer's phone number
            restaurant_id: ID of the restaurant being called
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

            # Get menu data for menu-aware responses using the specific restaurant
            from backend.models_platform import RestaurantAccount
            account = db.query(RestaurantAccount).filter(
                RestaurantAccount.id == restaurant_id
            ).first()

            if not account:
                logger.error(f"Restaurant account not found: {restaurant_id}")
                return {
                    "type": "error",
                    "message": "Restaurant information not available. Please try again later."
                }

            menu_data = None
            # Fetch full menu structure for this specific restaurant from database
            import requests
            try:
                from backend.models_platform import Menu, MenuCategory, MenuItem, MenuModifier

                menus = db.query(Menu).filter(Menu.account_id == account.id).all()
                menu_data = {
                    "business_name": account.business_name,
                    "menus": []
                }

                for menu in menus:
                    menu_dict = {
                        "id": menu.id,
                        "name": menu.name,
                        "description": menu.description,
                        "categories": []
                    }

                    categories = db.query(MenuCategory).filter(MenuCategory.menu_id == menu.id).all()
                    for category in categories:
                        category_dict = {
                            "id": category.id,
                            "name": category.name,
                            "items": []
                        }

                        items = db.query(MenuItem).filter(MenuItem.category_id == category.id).all()
                        for item in items:
                            item_dict = {
                                "id": item.id,
                                "name": item.name,
                                "description": item.description,
                                "price_cents": item.price_cents,
                                "dietary_tags": item.dietary_tags or [],
                                "modifiers": []
                            }

                            if item.modifiers:
                                modifiers = db.query(MenuModifier).filter(MenuModifier.item_id == item.id).all()
                                for mod in modifiers:
                                    item_dict["modifiers"].append({
                                        "id": mod.id,
                                        "name": mod.name,
                                        "price_adjustment_cents": mod.price_adjustment_cents
                                    })

                            category_dict["items"].append(item_dict)

                        menu_dict["categories"].append(category_dict)

                    menu_data["menus"].append(menu_dict)

            except Exception as e:
                logger.warning(f"Failed to fetch menu for restaurant {restaurant_id}: {e}")

            # Build system prompt (using template if available, otherwise legacy method)
            if self.system_prompt_template:
                system_prompt = self._build_system_prompt_from_template(context, customer, menu_data, account)
            else:
                system_prompt = self._build_system_prompt(context, customer, menu_data, account)
            
            user_message = self._build_user_message(message, context)

            # Call LLM service (non-streaming for now - voice handler handles streaming separately)
            ai_response = await self.llm_service.generate_complete_response(
                system_prompt=system_prompt,
                user_message=user_message,
                conversation_history=None,  # Could add conversation history here
                temperature=0.7,
                max_tokens=512
            )
            
            logger.info(f"AI response (first 500 chars): {ai_response[:500]}")

            # Parse AI response
            result = self._parse_ai_response(ai_response)
            logger.info(f"Parsed intent: {result.get('intent')}, context from AI: {result.get('context', {})}")

            # Handle different intents
            if result["intent"] == "menu_question":
                # AI already answered the question in the message
                return {
                    "type": "gather",
                    "message": result.get("message", "What else would you like to know about our menu?"),
                    "context": result.get("context", context)
                }

            elif result["intent"] == "operating_hours":
                return await self._handle_operating_hours(account, result)

            elif result["intent"] == "place_order":
                # Check if menu exists before processing order
                if not menu_data or not menu_data.get("menus") or not any(
                    menu.get("categories") and any(cat.get("items") for cat in menu["categories"])
                    for menu in menu_data["menus"]
                ):
                    return {
                        "type": "gather",
                        "message": "I'm sorry, we don't have a menu set up yet. Please check back later or contact the restaurant directly.",
                        "context": context
                    }
                # Merge AI's context updates with existing context
                ai_context = result.get("context", {})
                merged_context = {**context, **ai_context}
                logger.info(f"Merging contexts: original={context}, AI={ai_context}, merged={merged_context}")
                return await self._handle_order(result, phone, db, merged_context, account)

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

    def _build_system_prompt(self, context: Dict, customer: Optional[Customer], menu_data: Optional[Dict] = None, account=None) -> str:
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

        # Get operating hours info
        hours_info = ""
        if account:
            if account.opening_time and account.closing_time:
                days_str = ""
                if account.operating_days:
                    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                    days_str = ", ".join([day_names[d] for d in sorted(account.operating_days)])
                
                hours_info = f"\n\nOPERATING HOURS:\n"
                hours_info += f"Hours: {account.opening_time} - {account.closing_time}\n"
                if days_str:
                    hours_info += f"Days: {days_str}\n"
                hours_info += "\nUse ONLY this information when answering questions about operating hours. Do not make up hours.\n"

        return f"""You are a friendly, helpful AI assistant for {menu_data.get('business_name', 'our restaurant') if menu_data else 'a restaurant'}.

Your personality: Warm, conversational, and genuinely helpful. You want customers to have a great experience.

You help with:
1. **Operating Hours**: Answer when the restaurant is open (use ONLY provided hours)
2. **Menu Guidance**: Help customers discover menu items, explain dishes, recommend based on preferences
3. **Takeout Orders**: Take complete orders with all details
4. **Reservations**: Book tables and check availability

{hours_info}
{menu_info}
{customer_info}

**How to help customers order:**
- If they mention a dish not on the menu, suggest similar items we DO have
- If they're unsure, ask about their preferences (spicy? vegetarian? protein choice?) and recommend
- When they order, offer ONE thoughtful add-on (e.g., "Would you like extra chicken for $4?" or "Rice comes with that - want to add naan bread for $3?")
- Don't be pushy - if they decline, move on cheerfully
- **REQUIRED**: Always gather: exact item name, quantity, any add-ons, their name, pickup/delivery time
- **NAME HANDLING**:
  - If customer info shows a name (returning customer), confirm it friendly: "Is this still for [Name]?" or "Should I put this under [Name] again?"
  - If no customer info (new customer), ask for name: "May I have your name for the order?" or "What name should I put this under?"
  - If customer provides a different name, use the new name in customer_name field
- Be conversational - "Great choice!" "That's one of our favorites!" "Perfect!"

Current conversation context: {json.dumps(context)}

**IMPORTANT**: You MUST respond with ONLY valid JSON. No explanation, no markdown, just JSON.

Response format:
{{
    "intent": "operating_hours|menu_question|place_order|book_table|check_availability|cancel_booking|need_more_info|goodbye",
    "message": "your conversational response to customer",
    "customer_name": "customer's name if mentioned, otherwise empty string",
    "order_items": [
        {{"item_name": "exact menu item name", "quantity": 1, "modifiers": [], "price_cents": 1499}}
    ],
    "date": "YYYY-MM-DD",
    "time": "HH:MM:SS",
    "party_size": 0,
    "special_requests": "",
    "question": "",
    "context": {{}}
}}

**For place_order intent**:
- Match customer's request to exact menu items
- Use EXACT menu item names from the menu above
- Calculate price_cents from the menu (multiply dollars by 100)
- Example: "Butter Chicken" costs $14.99 = 1499 price_cents
- If context has "pending_order" and customer mentions payment method, use intent="place_order" again with the payment method in context

**CRITICAL - Payment Method Handling**:
If the context contains a "pending_order", you are waiting for the customer's payment method response.
When customer says anything like:
- "pay by card" / "card" / "credit card" → return context: {{"payment_method": "card"}}
- "pay when I pick up" / "cash" / "pay on pickup" / "pay later" → return context: {{"payment_method": "pickup"}}
Then return intent="place_order" (NOT "goodbye") so the order can be finalized in the database.
IMPORTANT: Do NOT copy the pending_order into your response context - only set payment_method.

Today's date: {datetime.now().strftime('%Y-%m-%d')}
Be conversational, helpful, and accurate about menu items and pricing."""

    def _build_system_prompt_from_template(
        self, 
        context: Dict, 
        customer: Optional[Customer], 
        menu_data: Optional[Dict] = None, 
        account=None
    ) -> str:
        """Build system prompt from markdown template with placeholders."""
        if not self.system_prompt_template:
            # Fallback to old method
            return self._build_system_prompt(context, customer, menu_data, account)
        
        try:
            prompt = self.system_prompt_template
            
            # Replace placeholders
            prompt = prompt.replace("{{now}}", datetime.now().isoformat())
            prompt = prompt.replace("{{current_date}}", datetime.now().strftime('%Y-%m-%d'))
            
            if account:
                prompt = prompt.replace("{{restaurant_name}}", account.business_name or "our restaurant")
                prompt = prompt.replace("{{opening_time}}", account.opening_time or "N/A")
                prompt = prompt.replace("{{closing_time}}", account.closing_time or "N/A")
                
                # Format operating days
                if account.operating_days:
                    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                    days_str = ", ".join([day_names[d] for d in sorted(account.operating_days)])
                else:
                    days_str = "Not specified"
                prompt = prompt.replace("{{operating_days}}", days_str)
            else:
                prompt = prompt.replace("{{restaurant_name}}", "our restaurant")
                prompt = prompt.replace("{{opening_time}}", "N/A")
                prompt = prompt.replace("{{closing_time}}", "N/A")
                prompt = prompt.replace("{{operating_days}}", "Not specified")
            
            # Format menu data
            menu_str = ""
            if menu_data and menu_data.get("menus"):
                menu_str = "\n\nRESTAURANT MENU:\n"
                for menu in menu_data["menus"]:
                    menu_str += f"\n{menu['name']}: {menu.get('description', '')}\n"
                    for category in menu["categories"]:
                        menu_str += f"\n  {category['name']}:\n"
                        for item in category["items"]:
                            menu_str += f"    - {item['name']} (${item['price_cents']/100:.2f})"
                            if item.get('dietary_tags'):
                                menu_str += f" [{', '.join(item['dietary_tags'])}]"
                            menu_str += f"\n      {item['description']}\n"
                            if item.get('modifiers'):
                                menu_str += "      Customizations:\n"
                                for mod in item['modifiers']:
                                    price_str = f" (+${mod['price_adjustment_cents']/100:.2f})" if mod['price_adjustment_cents'] > 0 else ""
                                    menu_str += f"        • {mod['name']}{price_str}\n"
            else:
                menu_str = "\n\nRESTAURANT MENU:\nNo menu items available.\n"
            
            prompt = prompt.replace("{{menu_data}}", menu_str)
            
            # Add current context
            context_json = json.dumps(context)
            prompt = prompt.replace("{{context}}", context_json)
            
            # Customer info
            customer_info = ""
            if customer:
                customer_info = f"\nCustomer name: {customer.name}\nPrevious orders: {customer.total_bookings}"
            prompt = prompt.replace("{{customer_info}}", customer_info)
            
            return prompt
            
        except Exception as e:
            logger.error(f"Error building prompt from template: {str(e)}")
            # Fallback to old method
            return self._build_system_prompt(context, customer, menu_data, account)

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

    async def _handle_operating_hours(
        self,
        account,
        result: Dict
    ) -> Dict[str, Any]:
        """Handle operating hours questions."""
        if not account.opening_time or not account.closing_time:
            return {
                "type": "gather",
                "message": "I'm sorry, I don't have the operating hours information available right now. Please contact the restaurant directly for their hours.",
                "context": {}
            }

        # Format operating days
        days_str = ""
        if account.operating_days:
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            days_str = ", ".join([day_names[d] for d in sorted(account.operating_days)])
        
        # Build response message
        message = f"We're open from {account.opening_time} to {account.closing_time}"
        if days_str:
            message += f" on {days_str}"
        message += ". Is there anything else I can help you with?"

        return {
            "type": "gather",
            "message": message,
            "context": {}
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

        # Normalize phone number (ensure + prefix)
        if phone and not phone.startswith('+'):
            phone = '+' + phone

        # Get or create customer
        from backend.models import Customer
        customer = db.query(Customer).filter(Customer.phone == phone).first()

        if customer:
            # Returning customer - check if they provided a new name
            new_name = result.get("customer_name", "").strip()
            if new_name and new_name != customer.name:
                # Customer provided a different name, update it
                logger.info(f"Updating customer name from '{customer.name}' to '{new_name}' for {phone}")
                customer.name = new_name
                db.flush()
        else:
            # New customer - name is required
            customer_name = result.get("customer_name", "").strip()
            if not customer_name:
                return {
                    "type": "gather",
                    "message": "May I have your name for the order?",
                    "context": context
                }
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

        # Check if we have a pending order (customer responding with payment method)
        pending_order = context.get("pending_order")
        payment_method = context.get("payment_method")
        logger.info(f"Order handling: pending_order={bool(pending_order)}, payment_method={payment_method}")

        if pending_order and payment_method:
            # Customer has responded with payment method, use pending order data
            order_items = pending_order.get("items", [])
            subtotal = pending_order.get("subtotal", 0)
            tax = pending_order.get("tax", 0)
            delivery_fee = pending_order.get("delivery_fee", 0)
            total = pending_order.get("total", 0)
        else:
            # New order or no payment method yet
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
        special_instructions=result.get("special_requests")
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
            # Use restaurant's Twilio phone number for SMS if available
            from_number = account.twilio_phone_number if account else None
            sms_service.send_sms(phone, confirmation_msg, from_number=from_number)
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

{"Payment will be processed when you pick up." if payment_method == "pickup" else "Payment confirmed."}

Is there anything else I can help you with?"""

        return {
            "type": "gather",
            "message": message,
            "context": {"order_id": order.id}
        }


# Global conversation handler instance
conversation_handler = ConversationHandler()
