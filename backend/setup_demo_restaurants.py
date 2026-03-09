"""
Setup script for demo restaurants across key cuisine categories.
Creates restaurant accounts, menus, Retell agents, and phone numbers.

Uses the voice-agent-prompt-template.txt format (pay-at-pickup only).

Usage:
    python -m backend.setup_demo_restaurants
"""

import os
import sys
import asyncio
import logging

from dotenv import load_dotenv
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(project_root, ".env"))

from backend.database import get_db
from backend.services.retell_service import retell_service
from backend.services.retell_llm_service import retell_llm_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== Prompt Template ====================

def get_prompt(restaurant_name: str, restaurant_id: int) -> str:
    """Build system prompt from the voice-agent-prompt-template."""
    return f"""You are a friendly phone assistant for {restaurant_name}. You help customers place pickup orders.

## CRITICAL RULES - SESSION ID (GENERATE YOUR OWN - DO NOT COPY THIS EXAMPLE)
At the START of this conversation, you MUST generate YOUR OWN UNIQUE random 8-character session ID.
Use random letters and numbers like: "r7t2q9w4", "m3x8k1p5", "j6b9n2v8" - create your OWN unique one!
DO NOT use "a1b2c3d4" - that is just showing the format. Create YOUR OWN RANDOM ID.
Use this SAME session_id you generated in EVERY function call throughout this conversation.
This ensures your cart is separate from other conversations.

## CRITICAL RULES - GENERAL
- restaurant_id is {restaurant_id} - pass this to EVERY function call
- session_id - generate ONCE at start, use in EVERY function call
- Keep ALL responses to 1-2 SHORT sentences
- NEVER repeat yourself - say something ONCE then WAIT for customer response
- After asking a question, STOP and wait - do NOT keep talking or call more functions
- NEVER invent prices - only mention prices when customer asks "how much"

## START OF CONVERSATION - MANDATORY
1. Generate YOUR OWN unique 8-character session_id using random letters/numbers (NOT "a1b2c3d4"!)
2. Example formats: "x7k9m2p4", "q3r8t1w6", "h5j2m9v4" - make your OWN random one
3. Use the session_id YOU generated in ALL function calls for this conversation

## ANSWERING QUESTIONS - MANDATORY
When customer asks ANY question (menu, hours, prices, etc.):
1. ANSWER the question FIRST using the appropriate function
2. THEN ask if they want to order
3. NEVER end the call without answering their question
4. If asked about menu items: call get_menu() and list the relevant items
5. If asked about prices: call get_menu(include_prices=true) and tell them the prices
6. If asked about hours: call get_hours() and tell them the hours

## PICKUP TIME RULES - CRITICAL
- Orders can ONLY be placed for TODAY, not for future days or past dates
- Pickup time must be between NOW and the end of today's business hours
- If customer requests a time that has already passed, say "That time has already passed. What time works for you today?"
- If customer asks to order for tomorrow or another day, say "We can only take orders for today. Would you like to place an order for pickup today?"
- If customer gives a pickup time after today's closing time, say "We close at [closing time] today. Can you pick up before then?"
- Call get_hours() if needed to confirm today's closing time

## TAKING ORDERS - FUNCTION CALLS
When customer says they want an item:
- IMMEDIATELY call add_to_cart(restaurant_id={restaurant_id}, item_name="exact item name", quantity=N, size="size if mentioned") BEFORE saying anything
- If the customer already mentioned a size (small, medium, large), include it in the FIRST add_to_cart call
- If add_to_cart responds asking for a size, ask the customer ONCE, then call add_to_cart with the size
- IMPORTANT: When retrying with a size, this is the SAME item - do NOT add it twice. Only ONE successful add_to_cart per item.
- NEVER say "I've got that" or confirm an item until AFTER add_to_cart succeeds with success=true
- Say "Got it" and ask "Anything else?" - then STOP and WAIT
- When customer orders MULTIPLE items in one sentence, handle them ONE AT A TIME sequentially

When customer changes quantity ("make that 2" or "actually 3"):
- Call update_cart_item(restaurant_id={restaurant_id}, item_name="item name", quantity=NEW_TOTAL)
- This REPLACES the quantity, not adds to it

When customer removes an item ("remove the X" or "no X"):
- Call remove_from_cart(restaurant_id={restaurant_id}, item_name="item name")

When customer says "start over" or "cancel everything":
- Call clear_cart(restaurant_id={restaurant_id})
- Then say "OK, let's start fresh. What would you like?"

When customer says "that's it" or "that's all" or is done ordering:
- ALWAYS call get_cart(restaurant_id={restaurant_id}) to review the order
- Read back their order and total from the get_cart response
- Ask "What name for the order and when to pick up?"

## BEFORE CREATING ORDER - MANDATORY
When you have both name AND pickup time:
1. FIRST call get_cart(restaurant_id={restaurant_id}) to verify cart contents and total
2. Tell the customer: "Your total including tax is $X."
3. Call create_order() with payment_method="pay_at_pickup"
4. Confirm the order, say goodbye, then call end_call()

IMPORTANT:
- Payment is always at pickup — do NOT ask about card payment
- NEVER call create_order without calling get_cart first in the same conversation turn

## MENU ACCURACY - CRITICAL
- You do NOT know the menu from memory. NEVER guess or invent menu items.
- ALWAYS call get_menu() to check what items are available before suggesting anything.
- ONLY mention items that were returned by the get_menu() function.
- NEVER mention items like tacos, burritos, or anything not returned by get_menu().

## ITEM NOT ON MENU
If customer asks for something not on the menu:
- Do NOT call add_to_cart
- Call get_menu() to check available items, then say "We don't have [item]. We do have [items from get_menu response]. Would you like one of those?"

## SPECIAL REQUESTS
For modifications ("extra spicy", "no garlic", "add cheese"):
- Include in special_requests parameter: add_to_cart(..., special_requests="extra spicy, no garlic")
- Do NOT add modifications as separate items

## ENDING THE CALL
Call end_call() ONLY after:
1. Order is confirmed and you said goodbye
2. Customer explicitly says goodbye without wanting to order
3. Customer's question is answered AND they say goodbye

NEVER end call without:
- Answering any questions the customer asked
- Confirming if they want to order

## PREVENTING LOOPS - CRITICAL
- After saying "Anything else?" -> STOP, do not say anything more, wait for response
- After asking for name/time -> STOP, wait for response
- NEVER call the same function twice in a row with same parameters
- If function returns an error, tell customer and ask what they'd like instead
- Maximum 1 function call per turn unless adding multiple different items
- If you already called clear_cart this conversation, do NOT call it again
"""


# ==================== Restaurant Definitions ====================

RESTAURANTS = [
    {
        "name": "Golden Dragon Chinese",
        "cuisine": "chinese",
        "owner_name": "Wei Chen",
        "owner_email": "wei@goldendragonct.com",
        "owner_phone": "+15552223333",
        "opening_time": "11:00",
        "closing_time": "22:00",
        "operating_days": [0, 1, 2, 3, 4, 5, 6],
        "voice_id": "11labs-Myra",
        "boosted_keywords": ["Golden Dragon", "Chinese", "lo mein", "fried rice", "wonton", "General Tso"],
        "begin_message": "Hi, thanks for calling Golden Dragon Chinese! What can I get for you today?",
        "menu": {
            "name": "Golden Dragon Menu",
            "categories": [
                {
                    "name": "Appetizers",
                    "items": [
                        {"name": "Egg Rolls", "description": "2 crispy pork and vegetable egg rolls with duck sauce", "price_cents": 550},
                        {"name": "Spring Rolls", "description": "2 fresh vegetable spring rolls with peanut sauce", "price_cents": 500},
                        {"name": "Crab Rangoon", "description": "6 cream cheese and crab wontons, fried crispy", "price_cents": 700},
                        {"name": "Pot Stickers", "description": "8 pan-fried pork dumplings with soy dipping sauce", "price_cents": 800},
                        {"name": "Wonton Soup", "description": "Pork wontons in clear chicken broth with scallions", "price_cents": 600},
                        {"name": "Hot and Sour Soup", "description": "Spicy and tangy soup with tofu, mushrooms, and egg", "price_cents": 600},
                    ]
                },
                {
                    "name": "Chicken",
                    "items": [
                        {"name": "General Tso's Chicken", "description": "Crispy chicken in sweet and spicy sauce with broccoli", "price_cents": 1350},
                        {"name": "Orange Chicken", "description": "Crispy chicken tossed in tangy orange glaze", "price_cents": 1350},
                        {"name": "Kung Pao Chicken", "description": "Diced chicken with peanuts, peppers, and chili sauce", "price_cents": 1300},
                        {"name": "Chicken with Broccoli", "description": "Tender chicken and broccoli in garlic sauce", "price_cents": 1250},
                        {"name": "Sesame Chicken", "description": "Crispy chicken in sweet sesame sauce with sesame seeds", "price_cents": 1350},
                        {"name": "Chicken Lo Mein", "description": "Soft noodles stir-fried with chicken and vegetables", "price_cents": 1200},
                    ]
                },
                {
                    "name": "Beef & Pork",
                    "items": [
                        {"name": "Beef with Broccoli", "description": "Sliced beef and broccoli in savory brown sauce", "price_cents": 1450},
                        {"name": "Mongolian Beef", "description": "Tender beef with scallions in sweet soy sauce", "price_cents": 1500},
                        {"name": "Pepper Steak", "description": "Sliced beef with peppers and onions in black bean sauce", "price_cents": 1450},
                        {"name": "Sweet and Sour Pork", "description": "Crispy pork pieces with pineapple in sweet and sour sauce", "price_cents": 1300},
                        {"name": "Mu Shu Pork", "description": "Shredded pork with vegetables and pancakes", "price_cents": 1350},
                    ]
                },
                {
                    "name": "Seafood",
                    "items": [
                        {"name": "Shrimp with Lobster Sauce", "description": "Large shrimp in savory egg and garlic sauce", "price_cents": 1550},
                        {"name": "Shrimp Fried Rice", "description": "Wok-fried rice with shrimp, egg, and vegetables", "price_cents": 1200},
                        {"name": "Shrimp Lo Mein", "description": "Soft noodles stir-fried with shrimp and vegetables", "price_cents": 1300},
                    ]
                },
                {
                    "name": "Fried Rice & Noodles",
                    "items": [
                        {"name": "Vegetable Fried Rice", "description": "Wok-fried rice with mixed vegetables and egg", "price_cents": 950},
                        {"name": "Chicken Fried Rice", "description": "Wok-fried rice with chicken, egg, and vegetables", "price_cents": 1100},
                        {"name": "Beef Fried Rice", "description": "Wok-fried rice with beef, egg, and vegetables", "price_cents": 1200},
                        {"name": "Combo Fried Rice", "description": "Wok-fried rice with chicken, shrimp, pork, and vegetables", "price_cents": 1350},
                        {"name": "Vegetable Lo Mein", "description": "Soft noodles stir-fried with mixed vegetables", "price_cents": 1000},
                    ]
                },
                {
                    "name": "Drinks",
                    "items": [
                        {"name": "Iced Tea", "description": "Freshly brewed iced tea", "price_cents": 250},
                        {"name": "Hot Tea", "description": "Traditional Chinese green or jasmine tea", "price_cents": 200},
                        {"name": "Fountain Soda", "description": "Coke, Sprite, or Fanta", "price_cents": 250},
                    ]
                },
            ]
        }
    },
    {
        "name": "Cluck & Grill",
        "cuisine": "chicken",
        "owner_name": "Marcus Johnson",
        "owner_email": "marcus@cluckandgrill.com",
        "owner_phone": "+15553334444",
        "opening_time": "11:00",
        "closing_time": "22:00",
        "operating_days": [0, 1, 2, 3, 4, 5, 6],
        "voice_id": "11labs-Adrian",
        "boosted_keywords": ["Cluck and Grill", "chicken", "wings", "tenders", "sandwich"],
        "begin_message": "Hey there, thanks for calling Cluck and Grill! What can I get for you?",
        "menu": {
            "name": "Cluck & Grill Menu",
            "categories": [
                {
                    "name": "Chicken Sandwiches",
                    "items": [
                        {"name": "Classic Chicken Sandwich", "description": "Crispy fried chicken breast, pickles, and mayo on a brioche bun", "price_cents": 999},
                        {"name": "Spicy Chicken Sandwich", "description": "Crispy chicken with spicy sauce, pickles, and coleslaw", "price_cents": 1099},
                        {"name": "Grilled Chicken Sandwich", "description": "Grilled chicken breast with lettuce, tomato, and honey mustard", "price_cents": 1099},
                        {"name": "Nashville Hot Sandwich", "description": "Nashville hot fried chicken with pickles and ranch", "price_cents": 1199},
                    ]
                },
                {
                    "name": "Wings",
                    "items": [
                        {"name": "6 Piece Wings", "description": "Choice of Buffalo, BBQ, Lemon Pepper, Garlic Parm, or Plain", "price_cents": 899},
                        {"name": "12 Piece Wings", "description": "Choice of Buffalo, BBQ, Lemon Pepper, Garlic Parm, or Plain", "price_cents": 1599},
                        {"name": "24 Piece Wings", "description": "Choice of Buffalo, BBQ, Lemon Pepper, Garlic Parm, or Plain", "price_cents": 2899},
                    ]
                },
                {
                    "name": "Tenders",
                    "items": [
                        {"name": "3 Piece Tenders", "description": "Hand-breaded chicken tenders with one dipping sauce", "price_cents": 799},
                        {"name": "5 Piece Tenders", "description": "Hand-breaded chicken tenders with two dipping sauces", "price_cents": 1199},
                        {"name": "Tender Basket", "description": "5 tenders with fries, coleslaw, and Texas toast", "price_cents": 1499},
                    ]
                },
                {
                    "name": "Combos",
                    "items": [
                        {"name": "Sandwich Combo", "description": "Any sandwich with fries and a drink", "price_cents": 1399},
                        {"name": "Wing Combo", "description": "6 wings with fries and a drink", "price_cents": 1299},
                        {"name": "Family Meal", "description": "12 tenders, large fries, coleslaw, 4 biscuits, and a 2-liter", "price_cents": 3299},
                    ]
                },
                {
                    "name": "Sides",
                    "items": [
                        {"name": "French Fries", "description": "Crispy seasoned fries", "price_cents": 399},
                        {"name": "Coleslaw", "description": "Creamy homestyle coleslaw", "price_cents": 299},
                        {"name": "Mac and Cheese", "description": "Creamy three-cheese mac", "price_cents": 449},
                        {"name": "Cornbread", "description": "Sweet honey cornbread", "price_cents": 250},
                        {"name": "Biscuit", "description": "Buttery homemade biscuit", "price_cents": 200},
                    ]
                },
                {
                    "name": "Drinks",
                    "items": [
                        {"name": "Fountain Drink", "description": "Coke, Sprite, Dr Pepper, or Lemonade", "price_cents": 299},
                        {"name": "Sweet Tea", "description": "Southern-style sweet iced tea", "price_cents": 299},
                        {"name": "Bottled Water", "description": "16oz bottled water", "price_cents": 199},
                    ]
                },
            ]
        }
    },
    {
        "name": "Casa Taqueria",
        "cuisine": "mexican",
        "owner_name": "Maria Garcia",
        "owner_email": "maria@casataqueria.com",
        "owner_phone": "+15554445555",
        "opening_time": "10:00",
        "closing_time": "22:00",
        "operating_days": [0, 1, 2, 3, 4, 5, 6],
        "voice_id": "11labs-Myra",
        "boosted_keywords": ["Casa Taqueria", "tacos", "burrito", "quesadilla", "nachos", "guacamole"],
        "begin_message": "Hola, thanks for calling Casa Taqueria! What can I get for you today?",
        "menu": {
            "name": "Casa Taqueria Menu",
            "categories": [
                {
                    "name": "Tacos",
                    "items": [
                        {"name": "Carne Asada Taco", "description": "Grilled steak, onions, cilantro, salsa verde on corn tortilla", "price_cents": 425},
                        {"name": "Chicken Taco", "description": "Seasoned grilled chicken, lettuce, pico de gallo, sour cream", "price_cents": 375},
                        {"name": "Al Pastor Taco", "description": "Marinated pork, pineapple, onions, cilantro on corn tortilla", "price_cents": 425},
                        {"name": "Carnitas Taco", "description": "Slow-cooked pulled pork, onions, cilantro, salsa roja", "price_cents": 400},
                        {"name": "Fish Taco", "description": "Beer-battered cod, cabbage slaw, chipotle crema", "price_cents": 475},
                        {"name": "Veggie Taco", "description": "Grilled peppers, onions, mushrooms, black beans, queso fresco", "price_cents": 350},
                    ]
                },
                {
                    "name": "Burritos",
                    "items": [
                        {"name": "Chicken Burrito", "description": "Grilled chicken, rice, beans, cheese, lettuce, pico, sour cream", "price_cents": 1100},
                        {"name": "Steak Burrito", "description": "Carne asada, rice, beans, cheese, guacamole, salsa", "price_cents": 1250},
                        {"name": "Carnitas Burrito", "description": "Pulled pork, rice, beans, cheese, onions, cilantro", "price_cents": 1150},
                        {"name": "Veggie Burrito", "description": "Grilled veggies, rice, beans, cheese, guacamole, salsa", "price_cents": 1000},
                    ]
                },
                {
                    "name": "Quesadillas",
                    "items": [
                        {"name": "Cheese Quesadilla", "description": "Melted blend of Mexican cheeses in a flour tortilla", "price_cents": 750},
                        {"name": "Chicken Quesadilla", "description": "Grilled chicken with cheese, peppers, onions", "price_cents": 1050},
                        {"name": "Steak Quesadilla", "description": "Carne asada with cheese, peppers, onions", "price_cents": 1150},
                    ]
                },
                {
                    "name": "Bowls & Nachos",
                    "items": [
                        {"name": "Burrito Bowl", "description": "Choice of protein, rice, beans, lettuce, pico, cheese, sour cream - no tortilla", "price_cents": 1100},
                        {"name": "Nachos", "description": "Tortilla chips loaded with cheese, beans, jalapeños, pico, sour cream, guacamole", "price_cents": 1050},
                        {"name": "Chicken Nachos", "description": "Nachos topped with grilled chicken", "price_cents": 1250},
                    ]
                },
                {
                    "name": "Sides & Extras",
                    "items": [
                        {"name": "Chips and Salsa", "description": "Tortilla chips with house-made salsa roja and verde", "price_cents": 400},
                        {"name": "Chips and Guacamole", "description": "Tortilla chips with fresh-made guacamole", "price_cents": 650},
                        {"name": "Rice and Beans", "description": "Mexican rice with refried or black beans", "price_cents": 400},
                        {"name": "Elote", "description": "Grilled Mexican street corn with mayo, cotija, chili, lime", "price_cents": 500},
                    ]
                },
                {
                    "name": "Drinks",
                    "items": [
                        {"name": "Horchata", "description": "Traditional Mexican rice milk drink with cinnamon", "price_cents": 400},
                        {"name": "Jamaica", "description": "Hibiscus flower iced tea", "price_cents": 350},
                        {"name": "Mexican Coke", "description": "Glass bottle Coca-Cola with cane sugar", "price_cents": 350},
                        {"name": "Fountain Soda", "description": "Coke, Sprite, or Fanta", "price_cents": 250},
                    ]
                },
            ]
        }
    },
    {
        "name": "Tandoor Palace",
        "cuisine": "indian",
        "owner_name": "Raj Patel",
        "owner_email": "raj@tandoorpalace.com",
        "owner_phone": "+15555556666",
        "opening_time": "11:30",
        "closing_time": "22:00",
        "operating_days": [0, 1, 2, 3, 4, 5, 6],
        "voice_id": "11labs-Myra",
        "boosted_keywords": ["Tandoor Palace", "Indian", "tikka masala", "naan", "biryani", "samosa", "curry"],
        "begin_message": "Hello, thank you for calling Tandoor Palace! How can I help you today?",
        "menu": {
            "name": "Tandoor Palace Menu",
            "categories": [
                {
                    "name": "Appetizers",
                    "items": [
                        {"name": "Samosa", "description": "2 crispy pastries filled with spiced potatoes and peas, served with tamarind chutney", "price_cents": 600},
                        {"name": "Vegetable Pakora", "description": "Mixed vegetable fritters with mint chutney", "price_cents": 650},
                        {"name": "Chicken Tikka", "description": "4 pieces of tandoor-grilled marinated chicken", "price_cents": 900},
                        {"name": "Onion Bhaji", "description": "Crispy onion fritters with raita", "price_cents": 550},
                    ]
                },
                {
                    "name": "Curry Entrees",
                    "items": [
                        {"name": "Chicken Tikka Masala", "description": "Tender chicken in creamy tomato-spice sauce. Our most popular dish", "price_cents": 1550},
                        {"name": "Butter Chicken", "description": "Chicken in rich buttery tomato cream sauce", "price_cents": 1550},
                        {"name": "Lamb Rogan Josh", "description": "Slow-cooked lamb in aromatic Kashmiri spice sauce", "price_cents": 1750},
                        {"name": "Chicken Vindaloo", "description": "Spicy chicken curry with potatoes - hot!", "price_cents": 1500},
                        {"name": "Palak Paneer", "description": "Fresh spinach with homemade cheese cubes", "price_cents": 1350},
                        {"name": "Chana Masala", "description": "Chickpeas in tangy tomato and spice sauce", "price_cents": 1250},
                        {"name": "Dal Tadka", "description": "Yellow lentils tempered with cumin, garlic, and spices", "price_cents": 1150},
                        {"name": "Shrimp Curry", "description": "Jumbo shrimp in coconut curry sauce", "price_cents": 1750},
                    ]
                },
                {
                    "name": "Tandoor Specialties",
                    "items": [
                        {"name": "Tandoori Chicken", "description": "Half chicken marinated in yogurt and spices, cooked in tandoor oven", "price_cents": 1500},
                        {"name": "Chicken Seekh Kebab", "description": "Ground chicken kebabs with herbs and spices", "price_cents": 1400},
                        {"name": "Lamb Chops", "description": "4 marinated lamb chops grilled in tandoor", "price_cents": 1900},
                    ]
                },
                {
                    "name": "Biryani & Rice",
                    "items": [
                        {"name": "Chicken Biryani", "description": "Fragrant basmati rice layered with spiced chicken", "price_cents": 1500},
                        {"name": "Lamb Biryani", "description": "Fragrant basmati rice layered with spiced lamb", "price_cents": 1700},
                        {"name": "Vegetable Biryani", "description": "Fragrant basmati rice with mixed vegetables", "price_cents": 1300},
                        {"name": "Plain Basmati Rice", "description": "Steamed basmati rice", "price_cents": 350},
                    ]
                },
                {
                    "name": "Breads",
                    "items": [
                        {"name": "Plain Naan", "description": "Traditional tandoor-baked flatbread", "price_cents": 300},
                        {"name": "Garlic Naan", "description": "Naan with garlic and butter", "price_cents": 375},
                        {"name": "Cheese Naan", "description": "Naan stuffed with melted cheese", "price_cents": 400},
                        {"name": "Peshwari Naan", "description": "Naan stuffed with coconut, raisins, and almonds", "price_cents": 425},
                    ]
                },
                {
                    "name": "Drinks",
                    "items": [
                        {"name": "Mango Lassi", "description": "Sweet yogurt drink blended with mango", "price_cents": 450},
                        {"name": "Sweet Lassi", "description": "Traditional sweet yogurt drink", "price_cents": 400},
                        {"name": "Masala Chai", "description": "Spiced Indian tea with milk", "price_cents": 350},
                        {"name": "Fountain Soda", "description": "Coke, Sprite, or Fanta", "price_cents": 250},
                    ]
                },
            ]
        }
    },
    {
        "name": "Stack Burger Co.",
        "cuisine": "burgers",
        "owner_name": "Jake Miller",
        "owner_email": "jake@stackburger.com",
        "owner_phone": "+15556667777",
        "opening_time": "11:00",
        "closing_time": "23:00",
        "operating_days": [0, 1, 2, 3, 4, 5, 6],
        "voice_id": "11labs-Adrian",
        "boosted_keywords": ["Stack Burger", "burger", "cheeseburger", "fries", "milkshake"],
        "begin_message": "Hey, welcome to Stack Burger Co.! What can I get started for you?",
        "menu": {
            "name": "Stack Burger Co. Menu",
            "categories": [
                {
                    "name": "Burgers",
                    "items": [
                        {"name": "Classic Burger", "description": "Quarter-pound beef patty, lettuce, tomato, onion, pickles, Stack sauce", "price_cents": 999},
                        {"name": "Cheeseburger", "description": "Quarter-pound beef patty with American cheese, lettuce, tomato, pickles", "price_cents": 1099},
                        {"name": "Bacon Cheeseburger", "description": "Beef patty, crispy bacon, cheddar, lettuce, tomato, Stack sauce", "price_cents": 1299},
                        {"name": "Double Stack", "description": "Two beef patties, double cheese, pickles, onions, special sauce", "price_cents": 1499},
                        {"name": "Mushroom Swiss Burger", "description": "Beef patty, sautéed mushrooms, Swiss cheese, garlic aioli", "price_cents": 1299},
                        {"name": "BBQ Bacon Burger", "description": "Beef patty, crispy bacon, onion rings, cheddar, BBQ sauce", "price_cents": 1399},
                        {"name": "Veggie Burger", "description": "House-made black bean patty, avocado, lettuce, tomato, chipotle mayo", "price_cents": 1099},
                    ]
                },
                {
                    "name": "Chicken & More",
                    "items": [
                        {"name": "Crispy Chicken Sandwich", "description": "Fried chicken breast, pickles, coleslaw, on brioche bun", "price_cents": 1099},
                        {"name": "Grilled Chicken Wrap", "description": "Grilled chicken, lettuce, tomato, ranch in flour tortilla", "price_cents": 999},
                        {"name": "Hot Dog", "description": "All-beef frank with mustard, ketchup, relish, onions", "price_cents": 699},
                    ]
                },
                {
                    "name": "Sides",
                    "items": [
                        {"name": "French Fries", "description": "Crispy golden fries with seasoning salt", "price_cents": 399},
                        {"name": "Onion Rings", "description": "Beer-battered onion rings with ranch", "price_cents": 499},
                        {"name": "Sweet Potato Fries", "description": "Crispy sweet potato fries with chipotle mayo", "price_cents": 499},
                        {"name": "Loaded Fries", "description": "Fries topped with cheese, bacon, sour cream, and chives", "price_cents": 699},
                        {"name": "Side Salad", "description": "Mixed greens, tomato, cucumber, croutons", "price_cents": 449},
                    ]
                },
                {
                    "name": "Shakes & Drinks",
                    "items": [
                        {"name": "Vanilla Milkshake", "description": "Hand-spun vanilla ice cream shake", "price_cents": 599},
                        {"name": "Chocolate Milkshake", "description": "Hand-spun chocolate ice cream shake", "price_cents": 599},
                        {"name": "Strawberry Milkshake", "description": "Hand-spun strawberry ice cream shake", "price_cents": 599},
                        {"name": "Fountain Soda", "description": "Coke, Sprite, Dr Pepper, or Root Beer", "price_cents": 299},
                        {"name": "Iced Tea", "description": "Freshly brewed unsweetened iced tea", "price_cents": 299},
                    ]
                },
            ]
        }
    },
    {
        "name": "Sakura Sushi",
        "cuisine": "sushi",
        "owner_name": "Yuki Tanaka",
        "owner_email": "yuki@sakurasushi.com",
        "owner_phone": "+15557778888",
        "opening_time": "11:30",
        "closing_time": "21:30",
        "operating_days": [0, 1, 2, 3, 4, 5, 6],
        "voice_id": "11labs-Myra",
        "boosted_keywords": ["Sakura Sushi", "sushi", "sashimi", "roll", "maki", "tempura", "ramen"],
        "begin_message": "Hi, thank you for calling Sakura Sushi! What can I get for you today?",
        "menu": {
            "name": "Sakura Sushi Menu",
            "categories": [
                {
                    "name": "Appetizers",
                    "items": [
                        {"name": "Edamame", "description": "Steamed soybeans with sea salt", "price_cents": 500},
                        {"name": "Miso Soup", "description": "Traditional miso with tofu, seaweed, and scallions", "price_cents": 400},
                        {"name": "Gyoza", "description": "6 pan-fried pork dumplings with ponzu sauce", "price_cents": 750},
                        {"name": "Shrimp Tempura", "description": "5 pieces of lightly battered fried shrimp with tempura sauce", "price_cents": 1000},
                        {"name": "Seaweed Salad", "description": "Marinated wakame seaweed with sesame dressing", "price_cents": 600},
                    ]
                },
                {
                    "name": "Classic Rolls",
                    "items": [
                        {"name": "California Roll", "description": "Crab, avocado, cucumber, sesame seeds (8 pcs)", "price_cents": 900},
                        {"name": "Spicy Tuna Roll", "description": "Spicy tuna, cucumber, spicy mayo (8 pcs)", "price_cents": 1050},
                        {"name": "Salmon Avocado Roll", "description": "Fresh salmon and avocado (8 pcs)", "price_cents": 1050},
                        {"name": "Philadelphia Roll", "description": "Smoked salmon, cream cheese, cucumber (8 pcs)", "price_cents": 1000},
                        {"name": "Shrimp Tempura Roll", "description": "Shrimp tempura, avocado, eel sauce (8 pcs)", "price_cents": 1100},
                        {"name": "Veggie Roll", "description": "Avocado, cucumber, carrot, asparagus (8 pcs)", "price_cents": 800},
                    ]
                },
                {
                    "name": "Specialty Rolls",
                    "items": [
                        {"name": "Dragon Roll", "description": "Shrimp tempura inside, eel and avocado on top with eel sauce (8 pcs)", "price_cents": 1500},
                        {"name": "Rainbow Roll", "description": "California roll topped with assorted sashimi (8 pcs)", "price_cents": 1600},
                        {"name": "Spider Roll", "description": "Soft shell crab, avocado, cucumber, spicy mayo (8 pcs)", "price_cents": 1450},
                        {"name": "Volcano Roll", "description": "Spicy crab and shrimp baked on a California roll (8 pcs)", "price_cents": 1400},
                    ]
                },
                {
                    "name": "Sashimi & Nigiri",
                    "items": [
                        {"name": "Salmon Sashimi", "description": "5 pieces of fresh sliced salmon", "price_cents": 1200},
                        {"name": "Tuna Sashimi", "description": "5 pieces of fresh sliced tuna", "price_cents": 1300},
                        {"name": "Sashimi Combo", "description": "12 pieces assorted sashimi (salmon, tuna, yellowtail)", "price_cents": 2200},
                        {"name": "Nigiri Combo", "description": "8 pieces assorted nigiri sushi", "price_cents": 1800},
                    ]
                },
                {
                    "name": "Entrees",
                    "items": [
                        {"name": "Chicken Teriyaki", "description": "Grilled chicken with teriyaki sauce, served with rice and salad", "price_cents": 1400},
                        {"name": "Salmon Teriyaki", "description": "Grilled salmon with teriyaki sauce, served with rice and salad", "price_cents": 1600},
                        {"name": "Beef Teriyaki", "description": "Grilled beef with teriyaki sauce, served with rice and salad", "price_cents": 1500},
                    ]
                },
                {
                    "name": "Drinks",
                    "items": [
                        {"name": "Green Tea", "description": "Hot Japanese green tea", "price_cents": 250},
                        {"name": "Ramune", "description": "Japanese marble soda (original or strawberry)", "price_cents": 400},
                        {"name": "Fountain Soda", "description": "Coke, Sprite, or Ginger Ale", "price_cents": 250},
                    ]
                },
            ]
        }
    },
]


async def setup_restaurant(db, restaurant_config: dict, public_url: str) -> dict:
    """Set up a single restaurant with menu, agent, and phone number."""
    name = restaurant_config["name"]
    email = restaurant_config["owner_email"]

    # Step 1: Create or find restaurant account
    existing = db.query_one("restaurant_accounts", {"owner_email": email})
    if existing:
        logger.info(f"[{name}] Already exists (ID={existing['id']}). Skipping...")
        return {"name": name, "id": existing["id"], "status": "skipped"}

    logger.info(f"[{name}] Creating restaurant account...")
    account = db.insert("restaurant_accounts", {
        "business_name": name,
        "owner_name": restaurant_config["owner_name"],
        "owner_email": email,
        "owner_phone": restaurant_config["owner_phone"],
        "opening_time": restaurant_config["opening_time"],
        "closing_time": restaurant_config["closing_time"],
        "operating_days": restaurant_config["operating_days"],
        "subscription_tier": "starter",
        "subscription_status": "active",
        "platform_commission_rate": 0.0,
        "onboarding_completed": True,
        "is_active": True,
        "toast_enabled": False,
    })
    restaurant_id = account["id"]
    logger.info(f"[{name}] Created account: ID={restaurant_id}")

    # Step 2: Create menu
    menu_data = restaurant_config["menu"]
    logger.info(f"[{name}] Creating menu...")
    menu = db.insert("menus", {
        "account_id": restaurant_id,
        "name": menu_data["name"],
        "description": f"Full menu for {name}",
        "is_active": True,
        "available_days": restaurant_config["operating_days"],
        "available_start_time": restaurant_config["opening_time"],
        "available_end_time": restaurant_config["closing_time"],
    })
    menu_id = menu["id"]

    total_items = 0
    for cat_idx, cat_data in enumerate(menu_data["categories"]):
        category = db.insert("menu_categories", {
            "menu_id": menu_id,
            "name": cat_data["name"],
            "display_order": cat_idx,
        })
        cat_id = category["id"]

        for item_idx, item_data in enumerate(cat_data["items"]):
            db.insert("menu_items", {
                "category_id": cat_id,
                "name": item_data["name"],
                "description": item_data["description"],
                "price_cents": item_data["price_cents"],
                "is_available": True,
                "display_order": item_idx,
            })
            total_items += 1

    logger.info(f"[{name}] Created menu with {total_items} items")

    # Step 3: Create Retell LLM
    custom_prompt = get_prompt(name, restaurant_id)
    tools_config = retell_llm_service._get_tools_config(restaurant_id)

    import httpx
    llm_payload = {
        "model": "gpt-4o-mini",
        "general_prompt": custom_prompt,
        "begin_message": restaurant_config["begin_message"],
        "general_tools": tools_config,
    }

    llm_id = None
    agent_id = None
    phone_number = None

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.retellai.com/create-retell-llm",
                headers={
                    "Authorization": f"Bearer {os.getenv('RETELL_API_KEY')}",
                    "Content-Type": "application/json"
                },
                json=llm_payload,
                timeout=30.0
            )

            if response.status_code == 201:
                llm_id = response.json().get("llm_id")
                logger.info(f"[{name}] Created LLM: {llm_id}")
            else:
                logger.error(f"[{name}] Failed to create LLM: {response.status_code} - {response.text}")
                return {"name": name, "id": restaurant_id, "status": "llm_failed"}
    except Exception as e:
        logger.error(f"[{name}] Error creating LLM: {e}")
        return {"name": name, "id": restaurant_id, "status": "llm_error"}

    # Step 4: Create Retell Agent
    agent = await retell_service.create_agent(
        name=f"{name} Voice Agent",
        voice_id=restaurant_config["voice_id"],
        llm_id=llm_id,
        ambient_sound="coffee-shop",
        responsiveness=0.8,
        interruption_sensitivity=0.5,
        enable_backchannel=False,
        boosted_keywords=restaurant_config["boosted_keywords"],
        reminder_trigger_ms=10000,
        reminder_max_count=2,
        end_call_after_silence_ms=30000,
    )

    if agent:
        agent_id = agent.get("agent_id")
        logger.info(f"[{name}] Created agent: {agent_id}")
    else:
        logger.error(f"[{name}] Failed to create agent")
        return {"name": name, "id": restaurant_id, "llm_id": llm_id, "status": "agent_failed"}

    # Step 5: Purchase phone number and bind to agent
    phone = await retell_service.create_phone_number(
        area_code=332,  # NYC area code
        agent_id=agent_id,
        nickname=name,
    )

    if phone:
        phone_number = phone.get("phone_number")
        logger.info(f"[{name}] Purchased phone: {phone_number}")
    else:
        logger.warning(f"[{name}] Failed to purchase phone number - agent still works via web")

    # Step 6: Store everything with restaurant
    update_data = {
        "retell_agent_id": agent_id,
        "retell_llm_id": llm_id,
    }
    if phone_number:
        update_data["twilio_phone_number"] = phone_number

    db.update("restaurant_accounts", restaurant_id, update_data)
    logger.info(f"[{name}] Setup complete!")

    return {
        "name": name,
        "id": restaurant_id,
        "llm_id": llm_id,
        "agent_id": agent_id,
        "phone_number": phone_number,
        "menu_items": total_items,
        "status": "success",
    }


async def setup():
    """Main setup function - creates all demo restaurants."""
    db = get_db()

    public_url = os.getenv("PUBLIC_URL", "")
    if not public_url:
        ws_url = os.getenv("PUBLIC_WS_URL", "")
        if ws_url:
            public_url = ws_url.replace("wss://", "https://").replace("ws://", "http://")

    if not public_url:
        logger.error("PUBLIC_URL not set in .env - cannot create agent tools")
        return

    retell_key = os.getenv("RETELL_API_KEY")
    if not retell_key:
        logger.error("RETELL_API_KEY not set in .env - cannot create agents")
        return

    results = []
    for restaurant_config in RESTAURANTS:
        result = await setup_restaurant(db, restaurant_config, public_url)
        results.append(result)
        # Small delay between API calls to avoid rate limiting
        await asyncio.sleep(1)

    # Print summary
    print("\n" + "=" * 70)
    print("  DEMO RESTAURANTS SETUP COMPLETE")
    print("=" * 70)

    for r in results:
        status_icon = "OK" if r["status"] == "success" else "SKIP" if r["status"] == "skipped" else "FAIL"
        print(f"\n  [{status_icon}] {r['name']}")
        print(f"       Restaurant ID:  {r['id']}")
        if r.get("agent_id"):
            print(f"       Agent ID:       {r['agent_id']}")
            print(f"       Test URL:       https://app.retellai.com/agent/{r['agent_id']}")
        if r.get("phone_number"):
            print(f"       Phone:          {r['phone_number']}")
        if r.get("menu_items"):
            print(f"       Menu Items:     {r['menu_items']}")
        if r["status"] not in ("success", "skipped"):
            print(f"       Error:          {r['status']}")

    print("\n" + "=" * 70)
    success_count = sum(1 for r in results if r["status"] == "success")
    skip_count = sum(1 for r in results if r["status"] == "skipped")
    fail_count = len(results) - success_count - skip_count
    print(f"  Total: {len(results)} | Success: {success_count} | Skipped: {skip_count} | Failed: {fail_count}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(setup())
