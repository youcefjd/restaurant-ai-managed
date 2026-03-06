"""
Setup script for Sal's Pizza restaurant.
Creates the restaurant, menu, and Retell agent with hardcoded menu in the prompt.

Usage:
    python -m backend.setup_sals_pizza
"""

import os
import sys
import asyncio
import logging

# Load .env from project root
from dotenv import load_dotenv
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(project_root, ".env"))

from backend.database import get_db
from backend.services.retell_service import retell_service
from backend.services.retell_llm_service import retell_llm_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== Restaurant Config ====================

RESTAURANT_NAME = "Sal's Pizza"
OWNER_EMAIL = "sal@salspizza.com"
OWNER_PHONE = "+15551234567"
OPENING_TIME = "11:00"
CLOSING_TIME = "22:00"
OPERATING_DAYS = [0, 1, 2, 3, 4, 5, 6]  # Mon-Sun
TAX_RATE = 8.875  # NYC tax

# ==================== Menu Data ====================

MENU_DATA = {
    "name": "Sal's Pizza Menu",
    "categories": [
        {
            "name": "Pizzas",
            "items": [
                {"name": "Cheese Pizza", "description": "Classic New York style cheese pizza with mozzarella and tomato sauce", "price_cents": 1800},
                {"name": "Pepperoni Pizza", "description": "Loaded with pepperoni and mozzarella cheese", "price_cents": 2000},
                {"name": "Margherita Pizza", "description": "Fresh mozzarella, tomato, basil, and olive oil", "price_cents": 2100},
                {"name": "Meat Lovers Pizza", "description": "Pepperoni, sausage, bacon, and ham", "price_cents": 2400},
                {"name": "Veggie Pizza", "description": "Mushrooms, peppers, onions, olives, and tomatoes", "price_cents": 2100},
                {"name": "White Pizza", "description": "Ricotta, mozzarella, garlic, and olive oil - no red sauce", "price_cents": 2000},
                {"name": "BBQ Chicken Pizza", "description": "Grilled chicken, BBQ sauce, red onion, and cilantro", "price_cents": 2300},
                {"name": "Hawaiian Pizza", "description": "Ham and pineapple with mozzarella", "price_cents": 2100},
            ]
        },
        {
            "name": "Slices",
            "items": [
                {"name": "Cheese Slice", "description": "Single slice of classic cheese pizza", "price_cents": 350},
                {"name": "Pepperoni Slice", "description": "Single slice of pepperoni pizza", "price_cents": 400},
                {"name": "Sicilian Slice", "description": "Thick square slice with extra cheese", "price_cents": 450},
            ]
        },
        {
            "name": "Calzones & Rolls",
            "items": [
                {"name": "Calzone", "description": "Stuffed with ricotta and mozzarella, choice of fillings", "price_cents": 1200},
                {"name": "Stromboli", "description": "Rolled pizza dough with ham, salami, and mozzarella", "price_cents": 1200},
                {"name": "Garlic Knots", "description": "6 pieces, fresh from the oven with garlic butter", "price_cents": 500},
            ]
        },
        {
            "name": "Pasta",
            "items": [
                {"name": "Spaghetti Marinara", "description": "Spaghetti with house marinara sauce", "price_cents": 1200},
                {"name": "Penne Vodka", "description": "Penne pasta in creamy vodka sauce", "price_cents": 1400},
                {"name": "Baked Ziti", "description": "Ziti baked with ricotta, mozzarella, and meat sauce", "price_cents": 1400},
                {"name": "Chicken Parm", "description": "Breaded chicken cutlet with marinara and melted mozzarella over spaghetti", "price_cents": 1600},
            ]
        },
        {
            "name": "Sides & Salads",
            "items": [
                {"name": "Caesar Salad", "description": "Romaine lettuce, croutons, parmesan, Caesar dressing", "price_cents": 900},
                {"name": "Garden Salad", "description": "Mixed greens, tomato, cucumber, and red onion", "price_cents": 800},
                {"name": "Mozzarella Sticks", "description": "6 pieces with marinara dipping sauce", "price_cents": 800},
                {"name": "Chicken Wings", "description": "10 wings, choice of buffalo, BBQ, or plain", "price_cents": 1200},
                {"name": "French Fries", "description": "Crispy golden fries", "price_cents": 500},
            ]
        },
        {
            "name": "Drinks",
            "items": [
                {"name": "Fountain Soda", "description": "Coke, Sprite, or Fanta", "price_cents": 250},
                {"name": "Bottled Water", "description": "16oz bottled water", "price_cents": 200},
                {"name": "2-Liter Soda", "description": "Coke, Sprite, or Fanta", "price_cents": 400},
            ]
        },
    ]
}


def get_hardcoded_menu_prompt(restaurant_id: int) -> str:
    """Build the system prompt with the menu hardcoded directly in it."""

    # Build menu text from MENU_DATA
    menu_lines = []
    for cat in MENU_DATA["categories"]:
        menu_lines.append(f"\n### {cat['name']}")
        for item in cat["items"]:
            price = item["price_cents"] / 100
            menu_lines.append(f"- {item['name']}: ${price:.2f} - {item['description']}")

    menu_text = "\n".join(menu_lines)

    return f"""You are a friendly phone assistant for Sal's Pizza. You help customers place pickup orders.

## YOUR FULL MENU
{menu_text}

## SIZES - IMPORTANT
- Pizzas come in one size only (large). No need to ask about size.
- Slices are individual slices.
- All other items are single-serving portions.

## CRITICAL RULES - PRICES
- NEVER mention prices during ordering. Do NOT say the price when adding items.
- When a customer adds an item, just say "Got it" and "Anything else?" — NO dollar amounts.
- Prices are ONLY mentioned at the END when recapping the full order with tax.
- The ONLY time you say a dollar amount is during the order recap before payment.
- If customer specifically ASKS "how much is X?", then you may answer with the price from the menu above.

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
- You KNOW the full menu above - use it to answer questions WITHOUT calling get_menu
- ONLY call get_menu if you need to verify current availability

## START OF CONVERSATION - MANDATORY
1. Generate YOUR OWN unique 8-character session_id using random letters/numbers (NOT "a1b2c3d4"!)
2. Example formats: "x7k9m2p4", "q3r8t1w6", "h5j2m9v4" - make your OWN random one
3. Use the session_id YOU generated in ALL function calls for this conversation

## ANSWERING QUESTIONS - MANDATORY
When customer asks ANY question (menu, hours, prices, etc.):
1. ANSWER the question FIRST using the menu above or the appropriate function
2. THEN ask if they want to order
3. NEVER end the call without answering their question
4. If asked about menu items: use the menu listed above to answer
5. If asked about prices: refer to the prices listed above — this is the ONLY time you volunteer prices
6. If asked about hours: call get_hours() and tell them the hours

## TAKING ORDERS - FUNCTION CALLS
When customer says they want an item:
- Verify it's on the menu above first
- IMMEDIATELY call add_to_cart(restaurant_id={restaurant_id}, item_name="exact item name", quantity=N) BEFORE saying anything
- NEVER say "I've got that" or confirm an item until AFTER add_to_cart succeeds
- After add_to_cart succeeds, say ONLY "Got it. Anything else?" — do NOT mention the price or total
- Ignore any price/total info in the function response — do NOT read it back

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
- Read back ONLY the items and quantities (e.g., "So that's 1 Pepperoni Pizza and 2 Garlic Knots")
- Do NOT mention prices yet
- Ask "What name for the order and when would you like to pick up?"

## BEFORE CREATING ORDER - MANDATORY PAYMENT STEP
When you have both name AND pickup time:
1. FIRST call get_cart(restaurant_id={restaurant_id}) to verify cart contents and total
2. NOW read back the total WITH tax: "Your total with tax comes to $X.XX. Would you like to pay now by card, or pay when you pick up?"
3. This is the FIRST and ONLY time you mention the total dollar amount.
4. Wait for customer response about payment preference
5. If they want to pay by card: follow the PAYMENT COLLECTION steps below
6. If they want to pay at pickup: call create_order() with payment_method="pay_at_pickup"
7. Confirm the order, say goodbye, then call end_call()

IMPORTANT:
- NEVER call create_order without asking about payment first
- NEVER call create_order without calling get_cart first in the same conversation turn

## ITEM NOT ON MENU
If customer asks for something not on the menu:
- Do NOT call add_to_cart
- Say "We don't have [item]. We have [similar items]. Would you like one of those?"

## SPECIAL REQUESTS
For modifications ("extra spicy", "no garlic", "add cheese"):
- Include in special_requests parameter: add_to_cart(..., special_requests="extra spicy, no garlic")
- Do NOT add modifications as separate items

## PAYMENT COLLECTION (when customer chooses to pay by card)
1. Call initiate_payment_collection(restaurant_id={restaurant_id}, session_id=session_id)
2. Say exactly what the function response tells you to say (prompts for card number)
3. Customer will enter digits via phone keypad - you'll receive them as input
4. Call process_dtmf_input(restaurant_id={restaurant_id}, session_id=session_id, digits="the digits")
5. The response will tell you the next step (expiry, then CVV, then authorized)
6. Keep calling process_dtmf_input for each entry until you get "authorized" status
7. Once authorized, call create_order() with payment_method="card"

If payment fails:
- Call retry_payment() to try a different card
- Or call cancel_payment() and create_order() with payment_method="pay_at_pickup"

IMPORTANT for card payments:
- NEVER repeat card numbers, expiry, or CVV back to the customer
- Just say "Got it" after each successful entry
- Follow the exact prompts from each function response

## ENDING THE CALL
Call end_call() ONLY after:
1. Order is confirmed and you said goodbye
2. Customer explicitly says goodbye without wanting to order
3. Customer's question is answered AND they say goodbye

NEVER end call without:
- Answering any questions the customer asked
- Confirming if they want to order

## PREVENTING LOOPS - CRITICAL
- After saying "Anything else?" → STOP, do not say anything more, wait for response
- After asking for name/time → STOP, wait for response
- NEVER call the same function twice in a row with same parameters
- If function returns an error, tell customer and ask what they'd like instead
- Maximum 1 function call per turn unless adding multiple different items
- If you already called clear_cart this conversation, do NOT call it again
"""


async def setup():
    """Main setup function."""
    db = get_db()

    # Step 1: Check if restaurant already exists
    existing = db.query_one("restaurant_accounts", {"owner_email": OWNER_EMAIL})
    if existing:
        logger.info(f"Restaurant already exists with ID {existing['id']}. Updating...")
        restaurant_id = existing["id"]
    else:
        # Create restaurant account
        logger.info("Creating Sal's Pizza restaurant account...")
        account = db.insert("restaurant_accounts", {
            "business_name": RESTAURANT_NAME,
            "owner_name": "Sal",
            "owner_email": OWNER_EMAIL,
            "owner_phone": OWNER_PHONE,
            "opening_time": OPENING_TIME,
            "closing_time": CLOSING_TIME,
            "operating_days": OPERATING_DAYS,
            "subscription_tier": "free",
            "subscription_status": "trial",
            "platform_commission_rate": 15.0,
            "onboarding_completed": True,
            "is_active": True,
            "toast_enabled": True,
        })
        restaurant_id = account["id"]
        logger.info(f"Created restaurant account: ID={restaurant_id}")

    # Step 2: Create menu (only if no menu exists)
    existing_menus = db.query_all("menus", {"account_id": restaurant_id})
    if existing_menus:
        logger.info(f"Menu already exists for restaurant {restaurant_id}. Skipping menu creation.")
    else:
        logger.info("Creating menu...")
        menu = db.insert("menus", {
            "account_id": restaurant_id,
            "name": MENU_DATA["name"],
            "description": "Full menu for Sal's Pizza",
            "is_active": True,
            "available_days": OPERATING_DAYS,
            "available_start_time": OPENING_TIME,
            "available_end_time": CLOSING_TIME,
        })
        menu_id = menu["id"]
        logger.info(f"Created menu: ID={menu_id}")

        for cat_idx, cat_data in enumerate(MENU_DATA["categories"]):
            category = db.insert("menu_categories", {
                "menu_id": menu_id,
                "name": cat_data["name"],
                "display_order": cat_idx,
            })
            cat_id = category["id"]
            logger.info(f"  Created category: {cat_data['name']} (ID={cat_id})")

            for item_idx, item_data in enumerate(cat_data["items"]):
                item = db.insert("menu_items", {
                    "category_id": cat_id,
                    "name": item_data["name"],
                    "description": item_data["description"],
                    "price_cents": item_data["price_cents"],
                    "is_available": True,
                    "display_order": item_idx,
                })
                logger.info(f"    Created item: {item_data['name']} (${item_data['price_cents']/100:.2f})")

    # Step 3: Create Retell agent with hardcoded menu prompt
    logger.info("\nCreating Retell LLM and agent...")

    public_url = os.getenv("PUBLIC_URL", "")
    if not public_url:
        ws_url = os.getenv("PUBLIC_WS_URL", "")
        if ws_url:
            public_url = ws_url.replace("wss://", "https://").replace("ws://", "http://")

    if not public_url:
        logger.error("PUBLIC_URL not set in .env - cannot create agent tools")
        logger.info(f"\nRestaurant created with ID={restaurant_id}")
        logger.info("Set PUBLIC_URL in .env and re-run to create the agent.")
        return restaurant_id

    # Build the custom prompt with hardcoded menu
    custom_prompt = get_hardcoded_menu_prompt(restaurant_id)

    # Build tools config using the retell_llm_service helper
    tools_config = retell_llm_service._get_tools_config(restaurant_id)

    # Create the LLM directly via API
    import httpx
    llm_payload = {
        "model": "gpt-4o-mini",
        "general_prompt": custom_prompt,
        "begin_message": f"Hi, thanks for calling Sal's Pizza! What can I get for you today?",
        "general_tools": tools_config,
    }

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
                llm_config = response.json()
                llm_id = llm_config.get("llm_id")
                logger.info(f"Created Retell LLM: {llm_id}")
            else:
                logger.error(f"Failed to create LLM: {response.status_code} - {response.text}")
                return restaurant_id
    except Exception as e:
        logger.error(f"Error creating LLM: {e}")
        return restaurant_id

    # Create agent with the LLM
    agent = await retell_service.create_agent(
        name="Sal's Pizza Voice Agent (Native LLM)",
        voice_id="11labs-Myra",
        llm_id=llm_id,
        ambient_sound="coffee-shop",
        responsiveness=0.8,
        interruption_sensitivity=0.5,
        enable_backchannel=False,
        boosted_keywords=["Sal's Pizza", "pizza", "calzone", "slice"],
        reminder_trigger_ms=10000,
        reminder_max_count=2,
        end_call_after_silence_ms=30000,
    )

    if agent:
        agent_id = agent.get("agent_id")
        logger.info(f"Created Retell agent: {agent_id}")

        # Store agent and LLM IDs with restaurant
        db.update("restaurant_accounts", restaurant_id, {
            "retell_agent_id": agent_id,
            "retell_llm_id": llm_id,
        })
        logger.info(f"Linked agent {agent_id} to restaurant {restaurant_id}")
    else:
        logger.error("Failed to create agent")

    # Print summary
    print("\n" + "=" * 60)
    print(f"  SAL'S PIZZA SETUP COMPLETE")
    print("=" * 60)
    print(f"  Restaurant ID:  {restaurant_id}")
    print(f"  Restaurant:     {RESTAURANT_NAME}")
    print(f"  LLM ID:         {llm_id}")
    if agent:
        print(f"  Agent ID:       {agent_id}")
        print(f"  Test URL:       https://app.retellai.com/agent/{agent_id}")
    print(f"  Public URL:     {public_url}")
    print(f"  Menu Items:     {sum(len(c['items']) for c in MENU_DATA['categories'])} items")
    print("=" * 60)

    return restaurant_id


if __name__ == "__main__":
    result = asyncio.run(setup())
    if result:
        print(f"\nDone! Restaurant ID: {result}")
