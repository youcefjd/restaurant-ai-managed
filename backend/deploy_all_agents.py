"""
Deploy the latest prompt template + tools to all restaurant agents.

Usage:
    python -m backend.deploy_all_agents           # update all restaurants
    python -m backend.deploy_all_agents --id 5     # update only restaurant ID 5
    python -m backend.deploy_all_agents --dry-run  # show what would be updated

This runs the 3-step Retell deploy cycle for each restaurant:
  1. Update LLM (creates new draft version with latest prompt + tools)
  2. Publish agent (promotes draft to published)
  3. Update phone number to point to the new published version
"""

import os
import sys
import asyncio
import argparse
import logging

from dotenv import load_dotenv
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(project_root, ".env"))

import httpx
from backend.database import get_db
from backend.services.retell_llm_service import retell_llm_service

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

RETELL_API_KEY = os.getenv("RETELL_API_KEY", "")
RETELL_BASE = "https://api.retellai.com"


def retell_headers():
    return {
        "Authorization": f"Bearer {RETELL_API_KEY}",
        "Content-Type": "application/json",
    }


async def deploy_restaurant(restaurant: dict, phone_map: dict, dry_run: bool = False):
    """Run the 3-step deploy cycle for one restaurant."""
    rid = restaurant["id"]
    name = restaurant["business_name"]
    agent_id = restaurant.get("retell_agent_id")
    llm_id = restaurant.get("retell_llm_id")
    owner_phone = restaurant.get("owner_phone", "")

    if not agent_id or not llm_id:
        logger.warning(f"  [{name}] Skipping — no agent/LLM configured")
        return False

    phone_number = phone_map.get(agent_id)

    if dry_run:
        logger.info(f"  [{name}] Would update LLM {llm_id}, agent {agent_id}, phone {phone_number}")
        return True

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Update LLM with latest prompt + tools
        updated = await retell_llm_service.update_llm(
            llm_id=llm_id,
            restaurant_name=name,
            restaurant_id=rid,
            owner_phone=owner_phone,
        )
        if not updated:
            logger.error(f"  [{name}] FAILED to update LLM {llm_id}")
            return False
        llm_version = updated.get("version", "?")
        logger.info(f"  [{name}] LLM updated → v{llm_version}")

        # Step 2: Publish agent
        resp = await client.post(
            f"{RETELL_BASE}/publish-agent/{agent_id}",
            headers=retell_headers(),
            json={},
        )
        if resp.status_code != 200:
            logger.error(f"  [{name}] FAILED to publish agent: {resp.status_code}")
            return False
        logger.info(f"  [{name}] Agent published")

        # Step 3: Get new version and update phone
        resp = await client.get(
            f"{RETELL_BASE}/get-agent/{agent_id}",
            headers=retell_headers(),
        )
        agent_data = resp.json()
        published_version = agent_data["version"] - 1

        if phone_number:
            resp = await client.patch(
                f"{RETELL_BASE}/update-phone-number/{phone_number}",
                headers=retell_headers(),
                json={
                    "inbound_agent_id": agent_id,
                    "inbound_agent_version": published_version,
                },
            )
            if resp.status_code == 200:
                logger.info(f"  [{name}] Phone {phone_number} → v{published_version}")
            else:
                logger.error(f"  [{name}] FAILED to update phone: {resp.status_code}")
                return False
        else:
            logger.warning(f"  [{name}] No phone number found — skipping phone update")

    return True


async def main():
    parser = argparse.ArgumentParser(description="Deploy prompt template to all restaurant agents")
    parser.add_argument("--id", type=int, help="Only update this restaurant ID")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be updated")
    args = parser.parse_args()

    if not RETELL_API_KEY:
        logger.error("RETELL_API_KEY not set")
        sys.exit(1)

    if not retell_llm_service.enabled:
        logger.error("Retell LLM service not enabled")
        sys.exit(1)

    # Fetch all restaurants
    db = get_db()
    if args.id:
        account = db.query_one("restaurant_accounts", {"id": args.id})
        restaurants = [account] if account else []
    else:
        restaurants = db.query_all("restaurant_accounts", {"is_active": True})

    if not restaurants:
        logger.error("No restaurants found")
        sys.exit(1)

    # Build phone number map: agent_id -> phone_number
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{RETELL_BASE}/list-phone-numbers",
            headers=retell_headers(),
        )
        phones = resp.json()
    phone_map = {p["inbound_agent_id"]: p["phone_number"] for p in phones if p.get("inbound_agent_id")}

    logger.info(f"Deploying to {len(restaurants)} restaurant(s){'  [DRY RUN]' if args.dry_run else ''}:\n")

    success = 0
    failed = 0
    for r in restaurants:
        ok = await deploy_restaurant(r, phone_map, dry_run=args.dry_run)
        if ok:
            success += 1
        else:
            failed += 1

    logger.info(f"\nDone: {success} succeeded, {failed} failed")


if __name__ == "__main__":
    asyncio.run(main())
