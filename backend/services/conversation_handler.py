"""
AI-powered conversation handler for voice and text interactions.

Uses Gemini or OpenAI via llm_service to understand customer intent and extract booking information
from natural language conversations.
"""

import os
import re
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, date, time, timedelta
from pathlib import Path

# Try to import zoneinfo (Python 3.9+) or pytz for timezone support
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from pytz import timezone as ZoneInfo  # Fallback for older Python

# Try to import dateutil for flexible time parsing
try:
    from dateutil import parser as date_parser
    DATEUTIL_AVAILABLE = True
except ImportError:
    DATEUTIL_AVAILABLE = False
    date_parser = None

from backend.database import SupabaseDB
from backend.services.llm_service import llm_service

logger = logging.getLogger(__name__)

# Table names
RESTAURANT_ACCOUNTS_TABLE = "restaurant_accounts"
MENUS_TABLE = "menus"
MENU_CATEGORIES_TABLE = "menu_categories"
MENU_ITEMS_TABLE = "menu_items"
MENU_MODIFIERS_TABLE = "menu_modifiers"
ORDERS_TABLE = "orders"
CUSTOMERS_TABLE = "customers"
BOOKINGS_TABLE = "bookings"
TABLES_TABLE = "tables"
RESTAURANTS_TABLE = "restaurants"


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
        db: SupabaseDB,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        call_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process customer message and determine response.

        Args:
            message: Customer's message (from speech-to-text or SMS)
            phone: Customer's phone number
            restaurant_id: ID of the restaurant being called
            context: Conversation context (previous exchanges, gathered data)
            db: Database instance
            conversation_history: List of previous messages [{"role": "user/assistant", "content": "..."}]
            call_id: Unique identifier for the call/conversation (for linking to transcripts)

        Returns:
            Response dict with type, message, and next steps
        """
        if not self.enabled:
            return {
                "type": "error",
                "message": "AI service not available. Please try again later."
            }

        try:
            # Store call_id in context for linking orders to transcripts
            if call_id:
                context["call_id"] = call_id

            # Get or create customer
            customer = db.query_one(CUSTOMERS_TABLE, {"phone": phone})

            # Get menu data for menu-aware responses using the specific restaurant
            account = db.query_one(RESTAURANT_ACCOUNTS_TABLE, {"id": restaurant_id})

            if not account:
                logger.error(f"Restaurant account not found: {restaurant_id}")
                return {
                    "type": "error",
                    "message": "Restaurant information not available. Please try again later."
                }

            menu_data = None
            # Fetch full menu structure for this specific restaurant from database
            try:
                menus = db.query_all(MENUS_TABLE, {"account_id": account["id"]})
                menu_data = {
                    "business_name": account.get("business_name"),
                    "menus": []
                }

                for menu in menus:
                    menu_dict = {
                        "id": menu["id"],
                        "name": menu["name"],
                        "description": menu.get("description"),
                        "categories": []
                    }

                    categories = db.query_all(MENU_CATEGORIES_TABLE, {"menu_id": menu["id"]})
                    for category in categories:
                        category_dict = {
                            "id": category["id"],
                            "name": category["name"],
                            "items": []
                        }

                        items = db.query_all(MENU_ITEMS_TABLE, {"category_id": category["id"]})
                        for item in items:
                            item_dict = {
                                "id": item["id"],
                                "name": item["name"],
                                "description": item.get("description"),
                                "price_cents": item.get("price_cents"),
                                "dietary_tags": item.get("dietary_tags") or [],
                                "aliases": item.get("aliases") or [],
                                "modifiers": []
                            }

                            if item.get("modifiers"):
                                modifiers = db.query_all(MENU_MODIFIERS_TABLE, {"item_id": item["id"]})
                                for mod in modifiers:
                                    item_dict["modifiers"].append({
                                        "id": mod["id"],
                                        "name": mod["name"],
                                        "price_adjustment_cents": mod.get("price_adjustment_cents")
                                    })

                            category_dict["items"].append(item_dict)

                        menu_dict["categories"].append(category_dict)

                    menu_data["menus"].append(menu_dict)

            except Exception as e:
                logger.warning(f"Failed to fetch menu for restaurant {restaurant_id}: {e}")

            # Add menu_data to context for price lookups in cart handling
            if menu_data:
                context["menu_data"] = menu_data

            # Build system prompt (using template if available, otherwise legacy method)
            if self.system_prompt_template:
                system_prompt = self._build_system_prompt_from_template(context, customer, menu_data, account)
            else:
                system_prompt = self._build_system_prompt(context, customer, menu_data, account)

            user_message = self._build_user_message(message, context)

            # Call LLM service (non-streaming for now - voice handler handles streaming separately)
            # Limit conversation history to last 12 messages (6 turns) to balance context vs latency
            recent_history = conversation_history[-12:] if conversation_history and len(conversation_history) > 12 else conversation_history

            ai_response = await self.llm_service.generate_complete_response(
                system_prompt=system_prompt,
                user_message=user_message,
                conversation_history=recent_history,
                temperature=0.5,  # Lower temperature for faster, more consistent responses
                max_tokens=1024  # Enough for JSON response
            )

            logger.info(f"AI response (first 1500 chars): {ai_response[:1500]}")

            # Parse AI response
            result = self._parse_ai_response(ai_response)
            logger.info(f"Parsed intent: {result.get('intent')}, message: {result.get('message', '')[:200]}")

            # Fallback: Try to detect name corrections from user message if AI didn't capture it
            # This handles cases where customer says "No, my name is John" or "Actually it's Sarah"
            if context.get("customer_name") and not result.get("customer_name"):
                name_correction = self._detect_name_correction(message)
                if name_correction:
                    result["customer_name"] = name_correction
                    logger.info(f"Detected name correction from message: '{name_correction}'")

            # Fallback: Try to detect time corrections from user message if AI didn't capture it
            # This handles cases where customer says "Actually, make that 7pm" or "Change it to 6:30"
            if context.get("pickup_time") and not result.get("time"):
                time_correction = self._detect_time_correction(message)
                if time_correction:
                    result["time"] = time_correction
                    logger.info(f"Detected time correction from message: '{time_correction}'")

            # IMPORTANT: Preserve customer info from AI response in context for ALL intents
            # This prevents losing name/time when AI returns need_more_info or other intents
            if result.get("customer_name"):
                new_name = result["customer_name"].strip()
                old_name = context.get("customer_name", "")
                # Always update to the latest name from AI (handles corrections)
                if new_name:
                    context["customer_name"] = new_name
                    if old_name and old_name != new_name:
                        logger.info(f"Name CORRECTED from '{old_name}' to '{new_name}'")
                    else:
                        logger.info(f"Preserved customer_name in context: {new_name}")
            if result.get("time"):
                new_time = result["time"].strip()
                old_time = context.get("pickup_time", "")
                if new_time:
                    context["pickup_time"] = new_time
                    if old_time and old_time != new_time:
                        logger.info(f"Pickup time CHANGED from '{old_time}' to '{new_time}'")
                    else:
                        logger.info(f"Preserved pickup_time in context: {new_time}")
            if result.get("special_requests"):
                existing_requests = context.get("special_requests", "")
                if existing_requests:
                    context["special_requests"] = f"{existing_requests}; {result['special_requests']}"
                else:
                    context["special_requests"] = result["special_requests"]
            # Track if a pairing suggestion was made so we don't suggest again
            if result.get("suggestion_made"):
                context["suggestion_made"] = True
                logger.info("Marked suggestion_made in context")

            # Check if we're awaiting a name for an order and got one
            if context.get("awaiting_name") and context.get("pending_order_items"):
                customer_name = result.get("customer_name", "").strip()
                if customer_name:
                    logger.info(f"Got customer name '{customer_name}' while awaiting_name, continuing order flow")
                    # Override intent to continue order
                    result["intent"] = "place_order"
                    result["order_items"] = context.get("pending_order_items", [])

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
                return await self._handle_cart_update(result, phone, db, merged_context, account)

            elif result["intent"] == "confirm_order":
                # Customer is done adding items - finalize the order
                ai_context = result.get("context", {})
                merged_context = {**context, **ai_context}
                return await self._finalize_order(result, phone, db, merged_context, account)

            elif result["intent"] == "book_table":
                return await self._handle_booking(result, phone, db, context)

            elif result["intent"] == "check_availability":
                return await self._handle_availability(result, db, context)

            elif result["intent"] == "cancel_booking":
                return await self._handle_cancellation(result, phone, db)

            elif result["intent"] == "need_more_info":
                # Always use message field - question field may contain internal notes
                return {
                    "type": "gather",
                    "message": result.get("message") or "Could you provide more details?",
                    "context": result.get("context", context)
                }

            elif result["intent"] == "end_call_abuse":
                # Caller is being abusive/inappropriate - end the call politely
                logger.warning(f"Ending call due to abuse/inappropriate behavior from {phone}")
                return {
                    "type": "hangup",
                    "message": result.get("message", "I'm not able to continue this call, but I hope you have a good day. Goodbye.")
                }

            elif result["intent"] == "goodbye":
                # Check if there's a pending cart that should be finalized
                cart_items = context.get("cart_items", [])
                if cart_items:
                    logger.info(f"Goodbye intent with cart items - finalizing order first")
                    # Redirect to finalize the order
                    return await self._finalize_order(result, phone, db, context, account)

                # Safeguard: Only end call if customer actually said goodbye
                # Look for goodbye-like phrases in the original message
                goodbye_phrases = ["bye", "goodbye", "thanks", "thank you", "that's all", "that's it", "have a good", "see you"]
                message_lower = message.lower()
                customer_said_goodbye = any(phrase in message_lower for phrase in goodbye_phrases)

                # Also check if order was just confirmed (customer might be done)
                order_confirmed = context.get("order_confirmed", False)

                if not customer_said_goodbye and not order_confirmed:
                    # AI incorrectly detected goodbye - ask if they need anything else instead
                    logger.info(f"Goodbye intent without goodbye phrase in '{message}' - asking for clarification")
                    return {
                        "type": "gather",
                        "message": "Is there anything else I can help you with?",
                        "context": context
                    }

                return {
                    "type": "goodbye",
                    "message": result.get("message", "Thank you for calling! Have a great day!")
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

    def _build_system_prompt(self, context: Dict, customer: Optional[Dict], menu_data: Optional[Dict] = None, account: Optional[Dict] = None) -> str:
        """Build system prompt for Claude with menu awareness."""
        customer_info = ""
        if customer:
            customer_info = f"\nCustomer name: {customer.get('name')}\nPrevious orders: {customer.get('total_bookings', 0)}"

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
                                menu_info += f"        * {mod['name']}{price_str}\n"

        # Get operating hours info
        hours_info = ""
        if account:
            if account.get("opening_time") and account.get("closing_time"):
                days_str = ""
                if account.get("operating_days"):
                    op_days = account["operating_days"]
                    # Handle both formats: list of strings or list of indices
                    if op_days and isinstance(op_days[0], str):
                        days_str = ", ".join(op_days)
                    else:
                        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                        days_str = ", ".join([day_names[d] for d in sorted(op_days)])

                hours_info = f"\n\nOPERATING HOURS:\n"
                hours_info += f"Hours: {account['opening_time']} - {account['closing_time']}\n"
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

**Item Not Found - Suggest Alternatives:**
- If they ask for something not on the menu, say "We don't have [item], but we do have [similar item] which is really popular!"
- Suggest 1-2 similar items from the actual menu that match their preference

**Recommendations & Upselling (be helpful, not pushy):**
- After adding items, suggest ONE complementary pairing: "That goes great with our Garlic Naan!" or "Would you like to add a mango lassi to go with that?"
- For curry dishes -> suggest naan or rice
- For appetizers -> suggest a main course
- For mains -> suggest a drink or dessert
- If they seem undecided, ask about preferences: "Do you prefer something spicy or mild?" "Are you looking for vegetarian options?"
- Keep suggestions brief and natural - don't list multiple options

**Gathering Order Details:**
- **REQUIRED**: Always gather: exact item name, quantity, any add-ons, their name, pickup time
- **PICKUP TIME**: Ask "When would you like to pick this up?" - accept "ASAP", "in 30 minutes", "at 6pm", etc.
  - Set the "time" field in your response (e.g., "ASAP", "18:00", "in 30 minutes")
  - If they say "now" or "as soon as possible" -> time: "ASAP"
- **NAME HANDLING**:
  - If customer info shows a name (returning customer), confirm: "Is this still for [Name]?"
  - If no customer info (new customer), ask: "What name should I put this under?"
  - If customer provides a different name, use the new name
- Be conversational - "Great choice!" "That's one of our favorites!" "Perfect!"
- If they decline an upsell, move on cheerfully - never push twice

**Handling Unclear or Off-Topic Requests:**
- If you don't understand, ask for clarification once: "I didn't quite catch that. Could you say that again?"
- If the request is completely unrelated to food/orders/reservations, gently redirect: "I can help with orders, menu questions, or reservations. Is there something I can help you with?"
- NEVER make up information - if unsure, say so

**Ending the Call:**
- When customer says "bye", "goodbye", "that's all", "nothing else", "I'm done" -> use intent "goodbye"
- After confirming an order, if customer says "no" to "anything else?" -> use intent "goodbye" with a friendly farewell
- When ending: "Thank you for calling [restaurant name]! Have a great day!"

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
- All orders are pay at pickup - do NOT ask about payment method

Today's date: {datetime.now().strftime('%Y-%m-%d')}
Be conversational, helpful, and accurate about menu items and pricing."""

    def _build_system_prompt_from_template(
        self,
        context: Dict,
        customer: Optional[Dict],
        menu_data: Optional[Dict] = None,
        account: Optional[Dict] = None
    ) -> str:
        """Build system prompt from markdown template with placeholders."""
        if not self.system_prompt_template:
            # Fallback to old method
            return self._build_system_prompt(context, customer, menu_data, account)

        try:
            prompt = self.system_prompt_template

            # Replace placeholders - use restaurant's timezone
            restaurant_tz = account.get("timezone", "America/New_York") if account else "America/New_York"
            try:
                tz = ZoneInfo(restaurant_tz)
                now = datetime.now(tz)
            except Exception:
                now = datetime.now()

            prompt = prompt.replace("{{now}}", now.isoformat())
            prompt = prompt.replace("{{current_date}}", now.strftime('%Y-%m-%d'))
            prompt = prompt.replace("{{current_datetime}}", now.strftime('%A, %B %d, %Y at %I:%M %p'))

            if account:
                prompt = prompt.replace("{{restaurant_name}}", account.get("business_name") or "our restaurant")
                prompt = prompt.replace("{{opening_time}}", account.get("opening_time") or "N/A")
                prompt = prompt.replace("{{closing_time}}", account.get("closing_time") or "N/A")

                # Format operating days
                if account.get("operating_days"):
                    op_days = account["operating_days"]
                    # Handle both formats: list of strings or list of indices
                    if op_days and isinstance(op_days[0], str):
                        days_str = ", ".join(op_days)
                    else:
                        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                        days_str = ", ".join([day_names[d] for d in sorted(op_days)])
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
                            if item.get('aliases'):
                                menu_str += f" (also heard as: {', '.join(item['aliases'])})"
                            menu_str += f"\n      {item['description']}\n"
                            if item.get('modifiers'):
                                menu_str += "      Customizations:\n"
                                for mod in item['modifiers']:
                                    price_str = f" (+${mod['price_adjustment_cents']/100:.2f})" if mod['price_adjustment_cents'] > 0 else ""
                                    menu_str += f"        * {mod['name']}{price_str}\n"
            else:
                menu_str = "\n\nRESTAURANT MENU:\nNo menu items available.\n"

            prompt = prompt.replace("{{menu_data}}", menu_str)

            # Add current context
            context_json = json.dumps(context)
            prompt = prompt.replace("{{context}}", context_json)

            # Customer info
            customer_info = ""
            if customer:
                customer_info = f"\nCustomer name: {customer.get('name')}\nPrevious orders: {customer.get('total_bookings', 0)}"
            prompt = prompt.replace("{{customer_info}}", customer_info)

            return prompt

        except Exception as e:
            logger.error(f"Error building prompt from template: {str(e)}")
            # Fallback to old method
            return self._build_system_prompt(context, customer, menu_data, account)

    def _build_user_message(self, message: str, context: Dict) -> str:
        """Build user message with context."""
        return f"Customer says: {message}\n\nExtracted information so far: {json.dumps(context)}"

    def _detect_name_correction(self, message: str) -> Optional[str]:
        """
        Detect if the user is correcting their name in the message.
        Returns the corrected name if detected, None otherwise.
        """
        message_lower = message.lower().strip()

        # Common correction patterns
        correction_patterns = [
            # "No, my name is John" / "No it's John"
            r"(?:no|nope|actually|sorry)[,\s]+(?:my name is|it'?s|i'?m|this is|the name is|call me)\s+([a-zA-Z]+)",
            # "It's John, not Jon"
            r"(?:it'?s|i'?m|my name is)\s+([a-zA-Z]+)[,\s]+not\s+",
            # "John, not Jon"
            r"^([a-zA-Z]+)[,\s]+not\s+[a-zA-Z]+$",
            # "Actually John" / "No, John"
            r"(?:no|nope|actually)[,\s]+([a-zA-Z]+)$",
            # "My name is John" (when there's already a name in context, this is likely a correction)
            r"(?:my name is|i'?m|this is|the name is|call me)\s+([a-zA-Z]+)",
        ]

        for pattern in correction_patterns:
            match = re.search(pattern, message_lower, re.IGNORECASE)
            if match:
                name = match.group(1).strip().title()
                if len(name) >= 2:  # Valid name should be at least 2 chars
                    return name

        return None

    def _detect_time_correction(self, message: str) -> Optional[str]:
        """
        Detect if the user is correcting their pickup time in the message.
        Returns the corrected time if detected, None otherwise.
        """
        message_lower = message.lower().strip()

        # Common time correction patterns
        correction_patterns = [
            # "Actually, make it 7pm" / "Change it to 6:30"
            r"(?:actually|no|change\s+(?:it\s+)?to|make\s+(?:it|that))[,\s]+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)",
            # "No, 7pm" / "Actually 6:30"
            r"(?:no|nope|actually)[,\s]+(\d{1,2}(?::\d{2})?\s*(?:am|pm))",
            # "Let's do 7 instead" / "Make it 7pm instead"
            r"(?:let'?s\s+(?:do|make\s+it)|make\s+it)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*(?:instead)?",
            # "7pm, not 6pm" / "7 not 6"
            r"(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)[,\s]+(?:not|instead\s+of)",
            # "Change to 30 minutes" / "Make it in an hour"
            r"(?:change\s+(?:it\s+)?to|make\s+(?:it|that))\s+((?:\d+\s*(?:minutes?|mins?|hours?|hrs?))|(?:in\s+(?:an?\s+)?(?:hour|half\s+hour)))",
            # "Actually in 30 minutes"
            r"(?:actually|no)[,\s]+(in\s+\d+\s*(?:minutes?|mins?|hours?|hrs?))",
            # "Actually ASAP" / "Make it ASAP"
            r"(?:actually|change\s+(?:it\s+)?to|make\s+(?:it|that))[,\s]*(asap|as\s+soon\s+as\s+possible|now|right\s+now)",
        ]

        for pattern in correction_patterns:
            match = re.search(pattern, message_lower, re.IGNORECASE)
            if match:
                time_str = match.group(1).strip()
                if time_str:
                    # Normalize common variations
                    if time_str in ["asap", "as soon as possible", "now", "right now"]:
                        return "ASAP"
                    return time_str

        return None

    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude's JSON response."""
        try:
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                # Handle truncated response (no closing ```)
                if end == -1:
                    json_str = response_text[start:].strip()
                else:
                    json_str = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                if end == -1:
                    json_str = response_text[start:].strip()
                else:
                    json_str = response_text[start:end].strip()
            else:
                json_str = response_text.strip()

            # Try to parse as-is first
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # Try to extract the message from truncated JSON
                # Look for "message": "..." pattern
                message_match = re.search(r'"message"\s*:\s*"([^"]*)', json_str)
                intent_match = re.search(r'"intent"\s*:\s*"([^"]*)"', json_str)

                if message_match:
                    extracted_message = message_match.group(1)
                    # Clean up any trailing incomplete text
                    if extracted_message:
                        extracted_intent = intent_match.group(1) if intent_match else "menu_question"
                        logger.warning(f"Recovered truncated response: intent={extracted_intent}, message={extracted_message[:50]}...")
                        return {
                            "intent": extracted_intent,
                            "message": extracted_message
                        }
                raise  # Re-raise if we couldn't extract anything useful

        except json.JSONDecodeError:
            logger.error(f"Failed to parse AI response: {response_text}")
            return {"intent": "need_more_info", "question": "I didn't quite catch that. Could you repeat?"}

    async def _handle_booking(
        self,
        result: Dict,
        phone: str,
        db: SupabaseDB,
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
        customer = db.query_one(CUSTOMERS_TABLE, {"phone": phone})
        if not customer:
            customer_name = result.get("customer_name", "Guest")
            customer = db.insert(CUSTOMERS_TABLE, {
                "phone": phone,
                "name": customer_name
            })

        # Get first restaurant
        restaurants = db.query_all(RESTAURANTS_TABLE, limit=1)
        if not restaurants:
            return {
                "type": "error",
                "message": "I'm sorry, we're not taking reservations at this time."
            }
        restaurant = restaurants[0]

        # Parse date and time
        booking_date = datetime.strptime(result["date"], "%Y-%m-%d").date()
        booking_time = datetime.strptime(result["time"], "%H:%M:%S").time()

        # Find available table
        available_table = self._find_available_table(
            restaurant["id"],
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
        booking = db.insert(BOOKINGS_TABLE, {
            "restaurant_id": restaurant["id"],
            "table_id": available_table["id"],
            "customer_id": customer["id"],
            "booking_date": str(booking_date),
            "booking_time": str(booking_time),
            "party_size": result["party_size"],
            "duration_minutes": 120,
            "status": "confirmed"
        })

        # Send SMS confirmation
        try:
            from backend.services.sms_service import sms_service
            sms_service.send_booking_confirmation(booking, customer, restaurant)
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")

        return {
            "type": "confirmation",
            "booking": {
                "restaurant_name": restaurant["name"],
                "booking_date": booking_date,
                "booking_time": booking_time,
                "party_size": result["party_size"],
                "customer_name": customer["name"],
                "confirmation_id": booking["id"]
            }
        }

    async def _handle_availability(
        self,
        result: Dict,
        db: SupabaseDB,
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
        restaurants = db.query_all(RESTAURANTS_TABLE, limit=1)
        if not restaurants:
            return {"type": "error", "message": "Restaurant not available"}
        restaurant = restaurants[0]

        # Find available time slots
        booking_date = datetime.strptime(result["date"], "%Y-%m-%d").date()
        available_times = self._get_available_times(
            restaurant["id"],
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
        db: SupabaseDB
    ) -> Dict[str, Any]:
        """Handle booking cancellation."""
        customer = db.query_one(CUSTOMERS_TABLE, {"phone": phone})
        if not customer:
            return {
                "type": "error",
                "message": "I don't have any bookings under this phone number."
            }

        # Find active bookings using raw query since we need complex filtering
        today = datetime.now().date()
        query = db.table(BOOKINGS_TABLE).select("*").eq(
            "customer_id", customer["id"]
        ).eq(
            "status", "confirmed"
        ).gte(
            "booking_date", str(today)
        )
        result_data = query.execute()
        active_bookings = result_data.data or []

        if not active_bookings:
            return {
                "type": "gather",
                "message": "I don't see any upcoming reservations. Is there anything else I can help you with?"
            }

        # Cancel the most recent booking
        booking = active_bookings[0]
        db.update(BOOKINGS_TABLE, booking["id"], {"status": "cancelled"})

        # Send cancellation SMS
        try:
            from backend.services.sms_service import sms_service
            restaurant = db.query_one(RESTAURANTS_TABLE, {"id": booking["restaurant_id"]})
            if restaurant:
                sms_service.send_cancellation_confirmation(booking, customer, restaurant)
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")

        booking_date = datetime.strptime(booking["booking_date"], "%Y-%m-%d").date()
        return {
            "type": "gather",
            "message": f"I've cancelled your reservation for {booking_date.strftime('%B %d')}. Is there anything else I can help you with?"
        }

    async def _handle_operating_hours(
        self,
        account: Dict,
        result: Dict
    ) -> Dict[str, Any]:
        """Handle operating hours questions."""
        if not account.get("opening_time") or not account.get("closing_time"):
            return {
                "type": "gather",
                "message": "I'm sorry, I don't have the operating hours information available right now. Please contact the restaurant directly for their hours.",
                "context": {}
            }

        # Format operating days
        days_str = ""
        if account.get("operating_days"):
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            days_str = ", ".join([day_names[d] for d in sorted(account["operating_days"])])

        # Build response message
        message = f"We're open from {account['opening_time']} to {account['closing_time']}"
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
        db: SupabaseDB
    ) -> Optional[Dict]:
        """Find available table for booking."""
        # Get all active tables with sufficient capacity
        query = db.table(TABLES_TABLE).select("*").eq(
            "restaurant_id", restaurant_id
        ).gte(
            "capacity", party_size
        ).eq(
            "is_active", True
        )
        result = query.execute()
        tables = result.data or []

        # Check each table for conflicts
        for table in tables:
            # Get bookings for this table on this date
            conflicts_query = db.table(BOOKINGS_TABLE).select("*").eq(
                "table_id", table["id"]
            ).eq(
                "booking_date", str(booking_date)
            ).in_(
                "status", ["confirmed", "pending"]
            )
            conflicts_result = conflicts_query.execute()
            conflicts = conflicts_result.data or []

            # Check time overlap
            start_datetime = datetime.combine(booking_date, booking_time)
            end_datetime = start_datetime + timedelta(minutes=120)

            has_conflict = False
            for conflict in conflicts:
                conflict_time = datetime.strptime(conflict["booking_time"], "%H:%M:%S").time()
                conflict_start = datetime.combine(booking_date, conflict_time)
                conflict_end = conflict_start + timedelta(minutes=conflict["duration_minutes"])

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
        db: SupabaseDB
    ) -> List[time]:
        """Get list of available time slots."""
        restaurant = db.query_one(RESTAURANTS_TABLE, {"id": restaurant_id})
        if not restaurant:
            return []

        available_times = []

        # Generate time slots from opening to closing (every 30 minutes)
        opening_time = datetime.strptime(restaurant["opening_time"], "%H:%M:%S").time()
        closing_time = datetime.strptime(restaurant["closing_time"], "%H:%M:%S").time()

        current_time = datetime.combine(booking_date, opening_time)
        closing_datetime = datetime.combine(booking_date, closing_time)

        while current_time < closing_datetime - timedelta(hours=1):  # Stop 1 hour before closing
            # Check if table available at this time
            if self._find_available_table(restaurant_id, booking_date, current_time.time(), party_size, db):
                available_times.append(current_time.time())

            current_time += timedelta(minutes=30)

        return available_times[:5]  # Return first 5 available slots

    def _lookup_menu_item(self, item_name: str, menu_data: Dict) -> Optional[Dict]:
        """
        Look up a menu item by name, including alias matching for voice recognition.
        Returns the full item dict, or None if not found.
        """
        if not menu_data or not menu_data.get("menus"):
            return None

        item_name_lower = item_name.lower().strip()

        for menu in menu_data.get("menus", []):
            for category in menu.get("categories", []):
                for item in category.get("items", []):
                    menu_item_name = item.get("name", "").lower().strip()

                    # Check exact match or contains match on item name
                    if menu_item_name == item_name_lower or item_name_lower in menu_item_name or menu_item_name in item_name_lower:
                        return item

                    # Check aliases for phonetic matches (voice recognition mishearings)
                    aliases = item.get("aliases", [])
                    for alias in aliases:
                        alias_lower = alias.lower().strip()
                        if alias_lower == item_name_lower or item_name_lower in alias_lower or alias_lower in item_name_lower:
                            logger.info(f"Matched '{item_name}' to '{item['name']}' via alias '{alias}'")
                            return item

        return None

    def _lookup_menu_item_price(self, item_name: str, menu_data: Dict) -> int:
        """
        Look up the price of a menu item by name (case-insensitive fuzzy match).
        Returns price in cents, or 0 if not found.
        """
        item = self._lookup_menu_item(item_name, menu_data)
        if item:
            price = item.get("price_cents", 0)
            if price:
                logger.debug(f"Found price for '{item_name}': {price} cents")
                return price

        logger.warning(f"Could not find price for menu item: '{item_name}'")
        return 0

    def _build_special_instructions(
        self,
        pickup_note: str,
        result_requests: Optional[str],
        context_requests: Optional[str]
    ) -> str:
        """Build special instructions string from pickup note and special requests."""
        instructions = f"Pickup: {pickup_note}"

        # Combine special requests from result and context
        all_requests = []
        if context_requests and context_requests.strip():
            all_requests.append(context_requests.strip())
        if result_requests and result_requests.strip():
            # Avoid duplicates
            if result_requests.strip() not in all_requests:
                all_requests.append(result_requests.strip())

        if all_requests:
            instructions += f"\n{'; '.join(all_requests)}"

        return instructions

    async def _handle_cart_update(
        self,
        result: Dict,
        phone: str,
        db: SupabaseDB,
        context: Dict,
        account: Dict
    ) -> Dict[str, Any]:
        """
        Handle cart operations: add, remove, update quantity.
        Supports full CRUD operations on order items during the call.
        """
        # Get current cart from context or initialize empty
        cart_items = context.get("cart_items", [])

        # Get menu data for price lookups
        menu_data = context.get("menu_data", {})

        # Get new items from AI response
        new_items = result.get("order_items", [])

        if new_items:
            for new_item in new_items:
                item_name = new_item.get("item_name", "")
                action = new_item.get("action", "add").lower()  # Default to "add" for backwards compatibility
                quantity = new_item.get("quantity", 1)

                # Find existing item in cart (case-insensitive match)
                existing_idx = None
                for idx, cart_item in enumerate(cart_items):
                    if cart_item.get("item_name", "").lower() == item_name.lower():
                        existing_idx = idx
                        break

                if action == "remove":
                    # Remove item from cart entirely
                    if existing_idx is not None:
                        removed_item = cart_items.pop(existing_idx)
                        logger.info(f"Removed from cart: {removed_item.get('item_name')}")
                    else:
                        logger.warning(f"Tried to remove '{item_name}' but not in cart")

                elif action == "set":
                    # Set quantity to exact number (not add)
                    if quantity <= 0:
                        # Quantity 0 or negative = remove
                        if existing_idx is not None:
                            removed_item = cart_items.pop(existing_idx)
                            logger.info(f"Removed from cart (qty 0): {removed_item.get('item_name')}")
                    elif existing_idx is not None:
                        # Update existing item quantity
                        cart_items[existing_idx]["quantity"] = quantity
                        logger.info(f"Updated quantity: {item_name} → {quantity}")
                    else:
                        # Item not in cart, add it with specified quantity
                        new_item_copy = {k: v for k, v in new_item.items() if k != "action"}
                        new_item_copy["quantity"] = quantity
                        # Look up price from menu if missing or zero
                        if not new_item_copy.get("price_cents"):
                            new_item_copy["price_cents"] = self._lookup_menu_item_price(item_name, menu_data)
                        cart_items.append(new_item_copy)
                        logger.info(f"Added to cart (set): {quantity}x {item_name} @ {new_item_copy.get('price_cents')} cents")

                else:  # action == "add" or unspecified
                    # Add to existing quantity or add new item
                    if existing_idx is not None:
                        # Same item - add to existing quantity
                        cart_items[existing_idx]["quantity"] = cart_items[existing_idx].get("quantity", 1) + quantity
                        # Merge modifiers if any
                        existing_mods = cart_items[existing_idx].get("modifiers", [])
                        new_mods = new_item.get("modifiers", [])
                        if new_mods:
                            cart_items[existing_idx]["modifiers"] = list(set(existing_mods + new_mods))
                        logger.info(f"Added to cart: +{quantity} {item_name} (total: {cart_items[existing_idx]['quantity']})")
                    else:
                        # New item - add to cart (without the action field)
                        new_item_copy = {k: v for k, v in new_item.items() if k != "action"}
                        # Look up price from menu if missing or zero
                        if not new_item_copy.get("price_cents"):
                            new_item_copy["price_cents"] = self._lookup_menu_item_price(item_name, menu_data)
                        cart_items.append(new_item_copy)
                        logger.info(f"Added to cart: {quantity}x {item_name} @ {new_item_copy.get('price_cents')} cents")

            logger.info(f"Cart updated: {len(cart_items)} items - {[i.get('item_name') for i in cart_items]}")

        # Get customer name if provided
        customer_name = result.get("customer_name", "") or context.get("customer_name", "")

        # Get pickup time if provided
        pickup_time = result.get("time", "") or context.get("pickup_time", "")

        # Get special requests
        special_requests = result.get("special_requests", "") or context.get("special_requests", "")

        # Build updated context
        updated_context = {
            **context,
            "cart_items": cart_items,
            "customer_name": customer_name,
            "pickup_time": pickup_time,
            "special_requests": special_requests,
            "unclear_count": 0  # Reset since this was understood
        }

        # Use AI's response message (which should ask "anything else?")
        response_message = result.get("message", "")

        # If no message from AI, generate one
        if not response_message:
            items_list = ", ".join([f"{i.get('quantity', 1)}x {i.get('item_name')}" for i in cart_items])
            response_message = f"I've added that to your order. So far you have: {items_list}. Would you like anything else?"

        return {
            "type": "gather",
            "message": response_message,
            "context": updated_context
        }

    async def _finalize_order(
        self,
        result: Dict,
        phone: str,
        db: SupabaseDB,
        context: Dict,
        account: Dict
    ) -> Dict[str, Any]:
        """
        Finalize the order - check we have all required info and create the order.
        Called when customer says they're done adding items.
        """
        # Use cart from context, but also check if AI provided updated items
        cart_items = result.get("order_items", []) or context.get("cart_items", [])

        if not cart_items:
            return {
                "type": "gather",
                "message": result.get("message") or "It looks like you haven't added anything to your order yet. What would you like to order?",
                "context": context
            }

        # Check if we have customer name
        customer_name = result.get("customer_name", "") or context.get("customer_name", "")
        if not customer_name:
            # Use AI's message if provided, otherwise use default
            ai_message = result.get("message", "")
            if not ai_message or "name" not in ai_message.lower():
                ai_message = "May I have your name for the order?"
            return {
                "type": "gather",
                "message": ai_message,
                "context": {
                    **context,
                    "cart_items": cart_items,
                    "awaiting_name": True
                }
            }

        # Check if we have pickup time
        pickup_time = result.get("time", "") or context.get("pickup_time", "")
        if not pickup_time:
            # Use AI's message if provided, otherwise use default
            ai_message = result.get("message", "")
            if not ai_message or "pick" not in ai_message.lower():
                ai_message = "When would you like to pick this up?"
            return {
                "type": "gather",
                "message": ai_message,
                "context": {
                    **context,
                    "cart_items": cart_items,
                    "customer_name": customer_name,
                    "awaiting_pickup_time": True
                }
            }

        # We have everything - create the actual order
        # Pass cart items to the order creation
        result["order_items"] = cart_items
        result["customer_name"] = customer_name
        result["time"] = pickup_time

        return await self._handle_order(result, phone, db, context, account)

    async def _handle_order(
        self,
        result: Dict,
        phone: str,
        db: SupabaseDB,
        context: Dict,
        account: Dict
    ) -> Dict[str, Any]:
        """Handle takeout order placement."""
        import json as json_lib

        # Normalize phone number to E.164 format (digits only with + prefix)
        def normalize_phone(p):
            if not p:
                return p
            # Remove all non-digit characters except leading +
            digits = ''.join(c for c in p if c.isdigit())
            return '+' + digits if digits else p

        phone = normalize_phone(phone)
        phone_digits = phone.lstrip('+') if phone else ''

        # Get or create customer - try both with and without + prefix
        customer = db.query_one(CUSTOMERS_TABLE, {"phone": phone})
        if not customer:
            customer = db.query_one(CUSTOMERS_TABLE, {"phone": phone_digits})

        if customer:
            # Returning customer - check if they provided a new name
            new_name = result.get("customer_name", "").strip()
            if new_name and new_name != customer.get("name"):
                # Customer provided a different name, update it
                logger.info(f"Updating customer name from '{customer.get('name')}' to '{new_name}' for {phone}")
                try:
                    customer = db.update(CUSTOMERS_TABLE, customer["id"], {"name": new_name})
                except Exception as e:
                    logger.error(f"Failed to update customer name: {e}")
        else:
            # New customer - name is required
            customer_name = result.get("customer_name", "").strip()
            if not customer_name:
                # Save order items in context so they're not lost when asking for name
                order_items = result.get("order_items", [])
                return {
                    "type": "gather",
                    "message": "May I have your name for the order?",
                    "context": {
                        **context,
                        "pending_order_items": order_items,
                        "awaiting_name": True
                    }
                }
            try:
                customer = db.insert(CUSTOMERS_TABLE, {"phone": phone, "name": customer_name})
            except Exception as e:
                # Customer was created by another request, fetch them
                logger.warning(f"Failed to create customer, trying to fetch: {e}")
                customer = db.query_one(CUSTOMERS_TABLE, {"phone": phone})
                if not customer:
                    customer = db.query_one(CUSTOMERS_TABLE, {"phone": phone_digits})
                if not customer:
                    logger.error(f"Failed to create or find customer with phone {phone}")
                    return {
                        "type": "error",
                        "message": "I'm having trouble with your order. Please try again."
                    }

        # Get first restaurant location for this account
        restaurant = db.query_one(RESTAURANTS_TABLE, {"account_id": account["id"]})
        if not restaurant:
            return {
                "type": "error",
                "message": "Sorry, we're not taking orders at this time."
            }

        # Check if we have a pending order (customer responding with payment method)
        pending_order = context.get("pending_order")
        pending_order_items = context.get("pending_order_items")
        payment_method = context.get("payment_method")
        logger.info(f"Order handling: pending_order={bool(pending_order)}, pending_order_items={bool(pending_order_items)}, payment_method={payment_method}")

        if pending_order and payment_method:
            # Customer has responded with payment method, use pending order data
            order_items = pending_order.get("items", [])
            subtotal = pending_order.get("subtotal", 0)
            tax = pending_order.get("tax", 0)
            delivery_fee = pending_order.get("delivery_fee", 0)
            total = pending_order.get("total", 0)
        else:
            # Check for pending order items from name gathering step
            order_items = result.get("order_items", []) or pending_order_items or []
            if not order_items:
                return {
                    "type": "gather",
                    "message": "What would you like to order?",
                    "context": context
                }

            # Calculate totals
            subtotal = sum(item.get("price_cents", 0) * item.get("quantity", 1) for item in order_items)
            tax = int(subtotal * 0.08)  # 8% tax
            # Only add delivery fee for actual delivery orders (not pickup)
            is_delivery = context.get("delivery_address") and context.get("delivery_address") != "Pickup"
            delivery_fee = 500 if is_delivery else 0  # $5 delivery fee only for delivery
            total = subtotal + tax + delivery_fee

        # For now, all orders are pay at pickup (card payment not yet implemented)
        payment_method = "pickup"

        # Parse pickup time from AI response
        pickup_time_str = result.get("time", "") or context.get("pickup_time", "")
        scheduled_time = None
        pickup_note = "ASAP"

        if pickup_time_str and pickup_time_str.upper() != "ASAP":
            pickup_note = pickup_time_str
            # Try to parse time formats
            try:
                time_lower = pickup_time_str.lower().strip()
                now = datetime.now()

                # Handle "in X minutes" or "X minutes"
                minutes_match = re.search(r'(\d+)\s*min', time_lower)
                if minutes_match:
                    minutes = int(minutes_match.group(1))
                    scheduled_time = now + timedelta(minutes=minutes)
                    logger.info(f"Parsed '{pickup_time_str}' as {minutes} minutes from now: {scheduled_time}")

                # Handle "in X hours" or "X hours"
                elif re.search(r'(\d+)\s*hour', time_lower):
                    hours_match = re.search(r'(\d+)\s*hour', time_lower)
                    hours = int(hours_match.group(1))
                    scheduled_time = now + timedelta(hours=hours)
                    logger.info(f"Parsed '{pickup_time_str}' as {hours} hours from now: {scheduled_time}")

                # Handle "in half an hour" or "30 min"
                elif 'half' in time_lower and 'hour' in time_lower:
                    scheduled_time = now + timedelta(minutes=30)
                    logger.info(f"Parsed '{pickup_time_str}' as 30 minutes from now: {scheduled_time}")

                # Handle explicit time (e.g., "6pm", "18:00", "6:30 PM", "8 PM")
                elif ":" in pickup_time_str or "pm" in time_lower or "am" in time_lower or re.search(r'\d', time_lower):
                    if DATEUTIL_AVAILABLE:
                        parsed_time = date_parser.parse(pickup_time_str, fuzzy=True)
                        scheduled_time = now.replace(
                            hour=parsed_time.hour,
                            minute=parsed_time.minute,
                            second=0,
                            microsecond=0
                        )
                    else:
                        # Fallback: try to extract hour from common formats like "8pm", "8 pm", "20:00"
                        hour_match = re.search(r'(\d{1,2})(?::(\d{2}))?(?:\s*)?(am|pm)?', time_lower)
                        if hour_match:
                            hour = int(hour_match.group(1))
                            minute = int(hour_match.group(2)) if hour_match.group(2) else 0
                            am_pm = hour_match.group(3)
                            if am_pm == 'pm' and hour < 12:
                                hour += 12
                            elif am_pm == 'am' and hour == 12:
                                hour = 0
                            scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

                    # If the time is in the past, assume tomorrow
                    if scheduled_time and scheduled_time < now:
                        scheduled_time += timedelta(days=1)
                    logger.info(f"Parsed '{pickup_time_str}' as specific time: {scheduled_time}")

            except Exception as e:
                logger.warning(f"Could not parse pickup time '{pickup_time_str}': {e}")

        # Create order with payment info
        order_data = {
            "account_id": account["id"],  # Multi-tenant: link to restaurant account
            "restaurant_id": restaurant["id"],
            "customer_id": customer["id"],
            "customer_name": customer.get("name"),
            "customer_phone": phone,
            "order_date": datetime.now().isoformat(),
            "scheduled_time": scheduled_time.isoformat() if scheduled_time else None,
            "delivery_address": context.get("delivery_address", "Pickup"),
            "order_items": json_lib.dumps(order_items),
            "subtotal": subtotal,
            "tax": tax,
            "delivery_fee": delivery_fee if context.get("delivery_address") else 0,
            "total": total,
            "status": "pending",
            "payment_method": payment_method,
            "payment_status": "paid" if payment_method == "card" else "unpaid",
            "special_instructions": self._build_special_instructions(pickup_note, result.get('special_requests'), context.get('special_requests')),
            "conversation_id": context.get("call_id")  # Link to transcript
        }
        order = db.insert(ORDERS_TABLE, order_data)

        # Track trial order usage (successful AI-processed order)
        if account.get("subscription_status") == "trial":
            trial_orders_used = (account.get("trial_orders_used") or 0) + 1
            db.update(RESTAURANT_ACCOUNTS_TABLE, account["id"], {"trial_orders_used": trial_orders_used})
            logger.info(f"Trial order tracked for account {account['id']}: {trial_orders_used}/{account.get('trial_order_limit', 10)} orders used")

            # Check if trial limit reached
            if trial_orders_used >= (account.get("trial_order_limit") or 10):
                logger.warning(f"Account {account['id']} has reached trial order limit")

        # Send SMS confirmation
        try:
            from backend.services.sms_service import sms_service
            items_text = ", ".join([
                f"{item.get('quantity', 1)}x {item.get('item_name')}"
                for item in order_items
            ])
            # Build pickup time text for SMS
            if pickup_note and pickup_note != "ASAP":
                pickup_text = f"Pickup at {pickup_note}"
            else:
                pickup_text = "Ready in 15-20 minutes"

            confirmation_msg = f"""Your order #{order['id']} is confirmed!

{items_text}

Total: ${total / 100:.2f}
{pickup_text}
Payment: {payment_method}

Thank you!"""
            # Use restaurant's Twilio phone number for SMS if available
            from_number = account.get("twilio_phone_number")
            sms_service.send_sms(phone, confirmation_msg, from_number=from_number)
        except Exception as e:
            logger.error(f"Failed to send order confirmation SMS: {str(e)}")

        # Print to kitchen
        try:
            from backend.services.kitchen_printer import kitchen_printer
            order_dict = {
                "id": order["id"],
                "customer_name": customer.get("name"),
                "customer_phone": phone,
                "order_items": json_lib.dumps(order_items),
                "total": total,
                "payment_method": payment_method,
                "payment_status": order.get("payment_status"),
                "delivery_address": order.get("delivery_address"),
                "special_requests": result.get("special_requests")
            }
            kitchen_printer.print_order(order_dict)
            logger.info(f"Order #{order['id']} printed to kitchen")
        except Exception as e:
            logger.error(f"Failed to print order to kitchen: {str(e)}")

        # Build confirmation message with order recap
        items_recap = ", ".join([
            f"{item.get('quantity', 1)} {item.get('item_name')}"
            for item in order_items
        ])
        total_dollars = total / 100

        message = f"Your order is confirmed! Just to recap, you have {items_recap} for a total of ${total_dollars:.2f}. "
        message += f"Order number {order['id']} for {customer.get('name')}. "
        if pickup_note and pickup_note != "ASAP":
            message += f"We'll have it ready for pickup at {pickup_note}. "
        else:
            message += "We'll have it ready in about 15-20 minutes. "
        message += "You can pay when you pick up. Is there anything else I can help you with?"

        # Clear cart from context since order is complete, but keep call going
        # Include order total in context so AI can answer follow-up questions about the total
        return {
            "type": "gather",  # Don't hang up - wait for customer to say goodbye
            "message": message,
            "context": {
                "order_id": order["id"],
                "order_total": total_dollars,
                "order_items_recap": items_recap,
                "cart_items": [],
                "order_confirmed": True
            }
        }


# Global conversation handler instance
conversation_handler = ConversationHandler()
