"""
Onboard a new restaurant with AI voice ordering.

Creates the restaurant account, menu, Retell voice agent, and phone number.
Uses the production prompt template from retell_llm_service (shared across all restaurants).

Usage:
    # Interactive mode — prompts for all details
    python -m backend.onboard_restaurant

    # From a config file
    python -m backend.onboard_restaurant --config restaurant.json

    # Skip phone number purchase (test only, use Retell dashboard to call)
    python -m backend.onboard_restaurant --no-phone

Config JSON format:
    {
        "business_name": "Joe's Tacos",
        "owner_name": "Joe",
        "owner_email": "joe@joestacos.com",
        "owner_phone": "+15551234567",
        "opening_time": "11:00",
        "closing_time": "22:00",
        "operating_days": [0, 1, 2, 3, 4, 5, 6],
        "timezone": "America/Chicago",
        "tax_rate": 8.25,
        "area_code": 332,
        "voice_id": "11labs-Myra",
        "menu": {
            "categories": [
                {
                    "name": "Tacos",
                    "items": [
                        {"name": "Carne Asada Taco", "description": "Grilled steak taco", "price_cents": 450},
                        {"name": "Chicken Taco", "description": "Seasoned chicken taco", "price_cents": 400}
                    ]
                }
            ]
        }
    }

After onboarding:
    - Test voice agent: https://app.retellai.com/agent/<agent_id>
    - Deploy prompt updates: python -m backend.deploy_all_agents --id <restaurant_id>
    - View in dashboard: your frontend URL → login with owner_email
"""

import os
import sys
import json
import asyncio
import argparse
import logging

from dotenv import load_dotenv
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(project_root, ".env"))

from backend.database import get_db
from backend.services.retell_service import retell_service
from backend.services.retell_llm_service import retell_llm_service

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


# ==================== Voice Options ====================
# Popular Retell voices — see https://docs.retellai.com for full list
VOICES = {
    "myra":    "11labs-Myra",     # Female, warm, friendly
    "adrian":  "11labs-Adrian",   # Male, professional
}
DEFAULT_VOICE = "11labs-Myra"


def prompt_input(label: str, default: str = None, required: bool = True) -> str:
    """Prompt user for input with optional default."""
    suffix = f" [{default}]" if default else ""
    while True:
        value = input(f"  {label}{suffix}: ").strip()
        if not value and default:
            return default
        if value or not required:
            return value
        print(f"    ⚠ {label} is required")


def prompt_menu_interactive() -> dict:
    """Interactively build a menu."""
    print("\n  Menu Setup")
    print("  (Enter categories and items. Empty category name to finish.)\n")

    categories = []
    while True:
        cat_name = input(f"  Category name (or Enter to finish): ").strip()
        if not cat_name:
            if not categories:
                print("    ⚠ Need at least one category")
                continue
            break

        items = []
        while True:
            item_name = input(f"    Item name (or Enter to finish category): ").strip()
            if not item_name:
                if not items:
                    print("      ⚠ Need at least one item per category")
                    continue
                break
            description = input(f"    Description: ").strip() or item_name
            while True:
                price_str = input(f"    Price (e.g. 12.99): $").strip()
                try:
                    price_cents = int(float(price_str) * 100)
                    break
                except ValueError:
                    print("      ⚠ Enter a valid price")
            items.append({
                "name": item_name,
                "description": description,
                "price_cents": price_cents,
            })
            print(f"      ✓ Added {item_name} (${price_cents/100:.2f})")

        categories.append({"name": cat_name, "items": items})
        print(f"    ✓ Category '{cat_name}' — {len(items)} items\n")

    return {"categories": categories}


def load_config(config_path: str) -> dict:
    """Load restaurant config from JSON file."""
    with open(config_path) as f:
        config = json.load(f)

    required = ["business_name", "owner_name", "owner_email", "owner_phone", "menu"]
    missing = [k for k in required if k not in config]
    if missing:
        raise ValueError(f"Missing required fields in config: {', '.join(missing)}")

    if not config["menu"].get("categories"):
        raise ValueError("Menu must have at least one category with items")

    return config


def interactive_config() -> dict:
    """Build config interactively."""
    print("\n" + "=" * 60)
    print("  NEW RESTAURANT ONBOARDING")
    print("=" * 60 + "\n")

    config = {
        "business_name": prompt_input("Business name"),
        "owner_name": prompt_input("Owner name"),
        "owner_email": prompt_input("Owner email"),
        "owner_phone": prompt_input("Owner phone (E.164, e.g. +15551234567)"),
        "opening_time": prompt_input("Opening time (HH:MM, 24h)", "11:00"),
        "closing_time": prompt_input("Closing time (HH:MM, 24h)", "22:00"),
        "timezone": prompt_input("Timezone", "America/Chicago"),
        "tax_rate": float(prompt_input("Tax rate %", "8.25")),
        "area_code": int(prompt_input("Phone area code (3 digits)", "332")),
        "voice_id": VOICES.get(
            prompt_input("Voice (myra/adrian)", "myra").lower(),
            DEFAULT_VOICE
        ),
    }

    # Operating days
    days_str = prompt_input("Operating days (0=Mon..6=Sun, comma-separated)", "0,1,2,3,4,5,6")
    config["operating_days"] = [int(d.strip()) for d in days_str.split(",")]

    # Menu
    config["menu"] = prompt_menu_interactive()

    return config


async def onboard(config: dict, purchase_phone: bool = True):
    """Run the full onboarding flow."""
    db = get_db()
    name = config["business_name"]

    # ── Step 1: Create restaurant account ──────────────────────
    logger.info(f"\n[1/5] Creating restaurant account: {name}")

    existing = db.query_one("restaurant_accounts", {"owner_email": config["owner_email"]})
    if existing:
        restaurant_id = existing["id"]
        logger.info(f"  Already exists (ID={restaurant_id}), updating...")
        db.update("restaurant_accounts", restaurant_id, {
            "business_name": name,
            "owner_name": config["owner_name"],
            "owner_phone": config["owner_phone"],
            "opening_time": config.get("opening_time", "11:00"),
            "closing_time": config.get("closing_time", "22:00"),
            "operating_days": config.get("operating_days", [0,1,2,3,4,5,6]),
            "timezone": config.get("timezone", "America/Chicago"),
            "tax_rate": config.get("tax_rate", 8.25) / 100,
            "max_advance_order_days": config.get("max_advance_order_days", 0),
            "is_active": True,
        })
    else:
        account = db.insert("restaurant_accounts", {
            "business_name": name,
            "owner_name": config["owner_name"],
            "owner_email": config["owner_email"],
            "owner_phone": config["owner_phone"],
            "opening_time": config.get("opening_time", "11:00"),
            "closing_time": config.get("closing_time", "22:00"),
            "operating_days": config.get("operating_days", [0,1,2,3,4,5,6]),
            "timezone": config.get("timezone", "America/Chicago"),
            "tax_rate": config.get("tax_rate", 8.25) / 100,
            "max_advance_order_days": config.get("max_advance_order_days", 0),
            "subscription_tier": "starter",
            "subscription_status": "trial",
            "platform_commission_rate": 15.0,
            "onboarding_completed": True,
            "is_active": True,
        })
        restaurant_id = account["id"]
        logger.info(f"  Created (ID={restaurant_id})")

    # Create location row (needed for orders FK)
    existing_loc = db.query_one("restaurants", {"account_id": restaurant_id})
    if not existing_loc:
        db.insert("restaurants", {
            "account_id": restaurant_id,
            "name": name,
            "address": config.get("address", ""),
            "phone": config["owner_phone"],
            "email": config["owner_email"],
            "opening_time": config.get("opening_time", "11:00"),
            "closing_time": config.get("closing_time", "22:00"),
        })

    # ── Step 2: Create menu ────────────────────────────────────
    logger.info(f"\n[2/5] Setting up menu")

    existing_menus = db.query_all("menus", {"account_id": restaurant_id})
    if existing_menus:
        logger.info(f"  Menu already exists, skipping (delete existing menu to re-create)")
    else:
        menu_config = config["menu"]
        menu = db.insert("menus", {
            "account_id": restaurant_id,
            "name": f"{name} Menu",
            "description": f"Full menu for {name}",
            "is_active": True,
            "available_days": config.get("operating_days", [0,1,2,3,4,5,6]),
            "available_start_time": config.get("opening_time", "11:00"),
            "available_end_time": config.get("closing_time", "22:00"),
        })
        menu_id = menu["id"]

        total_items = 0
        for cat_idx, cat_data in enumerate(menu_config["categories"]):
            category = db.insert("menu_categories", {
                "menu_id": menu_id,
                "name": cat_data["name"],
                "display_order": cat_idx,
            })

            for item_idx, item_data in enumerate(cat_data["items"]):
                db.insert("menu_items", {
                    "category_id": category["id"],
                    "name": item_data["name"],
                    "description": item_data.get("description", ""),
                    "price_cents": item_data["price_cents"],
                    "is_available": True,
                    "display_order": item_idx,
                })
                total_items += 1

            logger.info(f"  {cat_data['name']}: {len(cat_data['items'])} items")

        logger.info(f"  Total: {total_items} menu items")

    # ── Step 3: Create Retell LLM ──────────────────────────────
    logger.info(f"\n[3/5] Creating Retell LLM (voice AI brain)")

    if not retell_llm_service.enabled:
        logger.error("  RETELL_API_KEY not set — cannot create voice agent")
        _print_summary(restaurant_id, name, None, None, None)
        return restaurant_id

    # Check if LLM already exists
    account_data = db.query_one("restaurant_accounts", {"id": restaurant_id})
    existing_llm = account_data.get("retell_llm_id") if account_data else None
    existing_agent = account_data.get("retell_agent_id") if account_data else None

    if existing_llm:
        # Update existing LLM with latest prompt
        logger.info(f"  Updating existing LLM {existing_llm}")
        await retell_llm_service.update_llm(
            llm_id=existing_llm,
            restaurant_name=name,
            restaurant_id=restaurant_id,
            owner_phone=config["owner_phone"],
        )
        llm_id = existing_llm
    else:
        llm_config = await retell_llm_service.create_llm(
            restaurant_name=name,
            restaurant_id=restaurant_id,
            model="gpt-4o-mini",
            owner_phone=config["owner_phone"],
        )
        if not llm_config:
            logger.error("  Failed to create LLM")
            return restaurant_id
        llm_id = llm_config["llm_id"]
        logger.info(f"  Created LLM: {llm_id}")

    # ── Step 4: Create Retell Agent ────────────────────────────
    logger.info(f"\n[4/5] Creating Retell voice agent")

    voice_id = config.get("voice_id", DEFAULT_VOICE)
    # Extract keywords from menu item names for STT boosting
    boosted_keywords = [name]
    for cat in config["menu"]["categories"]:
        for item in cat["items"]:
            # Add each item name as a boosted keyword
            boosted_keywords.append(item["name"])

    if existing_agent:
        logger.info(f"  Agent already exists: {existing_agent}")
        agent_id = existing_agent
        # Update webhook URL
        public_url = retell_llm_service.public_url
        if public_url:
            await retell_service.update_agent(
                agent_id,
                webhook_url=f"https://{public_url}/api/retell/webhook"
            )
    else:
        agent = await retell_service.create_agent(
            name=f"{name} Voice Agent",
            voice_id=voice_id,
            llm_id=llm_id,
            ambient_sound="coffee-shop",
            responsiveness=0.8,
            interruption_sensitivity=0.5,
            enable_backchannel=False,
            boosted_keywords=boosted_keywords[:50],  # Retell has a limit
            reminder_trigger_ms=10000,
            reminder_max_count=2,
            end_call_after_silence_ms=30000,
        )

        if not agent:
            logger.error("  Failed to create agent")
            _print_summary(restaurant_id, name, llm_id, None, None)
            return restaurant_id

        agent_id = agent["agent_id"]
        logger.info(f"  Created agent: {agent_id}")

        # Set webhook URL for call events (call_started, call_ended, call_analyzed)
        public_url = retell_llm_service.public_url
        if public_url:
            await retell_service.update_agent(
                agent_id,
                webhook_url=f"https://{public_url}/api/retell/webhook"
            )
            logger.info(f"  Webhook: https://{public_url}/api/retell/webhook")

    # Store IDs
    db.update("restaurant_accounts", restaurant_id, {
        "retell_agent_id": agent_id,
        "retell_llm_id": llm_id,
    })

    # ── Step 5: Purchase phone number ──────────────────────────
    phone_number = account_data.get("twilio_phone_number") if account_data else None

    if phone_number:
        logger.info(f"\n[5/5] Phone number already assigned: {phone_number}")
    elif purchase_phone:
        logger.info(f"\n[5/5] Purchasing phone number (area code {config.get('area_code', 332)})")
        phone = await retell_service.create_phone_number(
            area_code=config.get("area_code", 332),
            agent_id=agent_id,
            nickname=name,
        )
        if phone:
            phone_number = phone.get("phone_number")
            db.update("restaurant_accounts", restaurant_id, {
                "twilio_phone_number": phone_number,
            })
            logger.info(f"  Assigned: {phone_number}")
        else:
            logger.error("  Failed to purchase phone number")
    else:
        logger.info(f"\n[5/5] Skipping phone number (--no-phone)")

    # ── Deploy (publish agent + update phone) ──────────────────
    logger.info(f"\n  Publishing agent...")
    import httpx
    api_key = os.getenv("RETELL_API_KEY", "")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Publish
        resp = await client.post(
            f"https://api.retellai.com/publish-agent/{agent_id}",
            headers=headers, json={}
        )
        if resp.status_code == 200:
            logger.info(f"  Agent published")

            # Update phone to point to published version
            if phone_number:
                resp2 = await client.get(
                    f"https://api.retellai.com/get-agent/{agent_id}",
                    headers=headers
                )
                version = resp2.json().get("version", 2) - 1
                await client.patch(
                    f"https://api.retellai.com/update-phone-number/{phone_number}",
                    headers=headers,
                    json={"inbound_agent_id": agent_id, "inbound_agent_version": version}
                )
                logger.info(f"  Phone → agent v{version}")
        else:
            logger.warning(f"  Publish failed: {resp.status_code}")

    _print_summary(restaurant_id, name, llm_id, agent_id, phone_number)
    return restaurant_id


def _print_summary(rid, name, llm_id, agent_id, phone_number):
    """Print onboarding summary."""
    print("\n" + "=" * 60)
    print(f"  ONBOARDING COMPLETE: {name}")
    print("=" * 60)
    print(f"  Restaurant ID:   {rid}")
    if llm_id:
        print(f"  LLM ID:          {llm_id}")
    if agent_id:
        print(f"  Agent ID:        {agent_id}")
        print(f"  Test in browser: https://app.retellai.com/agent/{agent_id}")
    if phone_number:
        print(f"  Phone number:    {phone_number}")
        print(f"  Call to test:    {phone_number}")
    print()
    print("  Next steps:")
    print(f"    1. Test the agent: call {phone_number or 'via Retell dashboard'}")
    print(f"    2. Update prompt:  python -m backend.deploy_all_agents --id {rid}")
    print(f"    3. View orders:    Login to dashboard with {name}'s email")
    print("=" * 60)


async def main():
    parser = argparse.ArgumentParser(
        description="Onboard a new restaurant with AI voice ordering"
    )
    parser.add_argument("--config", type=str, help="Path to restaurant config JSON file")
    parser.add_argument("--no-phone", action="store_true", help="Skip phone number purchase")
    args = parser.parse_args()

    # Validate environment
    if not os.getenv("SUPABASE_URL"):
        logger.error("SUPABASE_URL not set. Copy .env.example to .env and fill in values.")
        sys.exit(1)

    if args.config:
        config = load_config(args.config)
    else:
        config = interactive_config()

    await onboard(config, purchase_phone=not args.no_phone)


if __name__ == "__main__":
    asyncio.run(main())
