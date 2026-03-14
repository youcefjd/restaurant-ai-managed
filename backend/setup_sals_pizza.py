"""
Setup script for Sal's Pizza restaurant.
Creates the restaurant, menu, and Retell agent using the shared system prompt.

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



# Sal's Pizza now uses the shared system prompt from retell_llm_service
# (no more hardcoded prompt that drifts out of sync)


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

    # Step 3: Create Retell agent using the shared system prompt
    logger.info("\nCreating Retell LLM and agent...")

    if not retell_llm_service.enabled:
        logger.error("Retell LLM service not enabled - check RETELL_API_KEY")
        return restaurant_id

    llm_config = await retell_llm_service.create_llm(
        restaurant_name=RESTAURANT_NAME,
        restaurant_id=restaurant_id,
        model="gpt-4o-mini",
        owner_phone=OWNER_PHONE,
    )

    if not llm_config:
        logger.error("Failed to create LLM")
        return restaurant_id

    llm_id = llm_config.get("llm_id")
    logger.info(f"Created Retell LLM: {llm_id}")

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
    print(f"  Public URL:     {retell_llm_service.public_url}")
    print(f"  Menu Items:     {sum(len(c['items']) for c in MENU_DATA['categories'])} items")
    print("=" * 60)

    return restaurant_id


if __name__ == "__main__":
    result = asyncio.run(setup())
    if result:
        print(f"\nDone! Restaurant ID: {result}")
