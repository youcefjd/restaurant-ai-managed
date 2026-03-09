"""
One-time fix: Create restaurants (location) rows for demo restaurant accounts
that are missing them. This fixes the foreign key constraint error on order creation.
"""
import os
import sys

from dotenv import load_dotenv
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(project_root, ".env"))

from backend.database import get_db

DEMO_ACCOUNTS = [
    {"id": 6, "name": "Golden Dragon Chinese", "address": "88 Mott St, New York, NY 10013", "phone": "+15552223333", "email": "wei@goldendragonct.com"},
    {"id": 7, "name": "Cluck & Grill", "address": "450 Flatbush Ave, Brooklyn, NY 11225", "phone": "+15553334444", "email": "marcus@cluckandgrill.com"},
    {"id": 8, "name": "Casa Taqueria", "address": "312 E 116th St, New York, NY 10029", "phone": "+15554445555", "email": "maria@casataqueria.com"},
    {"id": 9, "name": "Tandoor Palace", "address": "101 Lexington Ave, New York, NY 10016", "phone": "+15555556666", "email": "raj@tandoorpalace.com"},
    {"id": 10, "name": "Stack Burger Co.", "address": "200 W 44th St, New York, NY 10036", "phone": "+15556667777", "email": "jake@stackburger.com"},
    {"id": 11, "name": "Sakura Sushi", "address": "55 E 10th St, New York, NY 10003", "phone": "+15557778888", "email": "yuki@sakurasushi.com"},
]

def main():
    db = get_db()

    for acct in DEMO_ACCOUNTS:
        # Check if account exists
        account = db.query_one("restaurant_accounts", {"id": acct["id"]})
        if not account:
            print(f"  Account ID {acct['id']} ({acct['name']}) not found, skipping")
            continue

        # Check if location already exists
        existing = db.query_one("restaurants", {"account_id": acct["id"]})
        if existing:
            print(f"  {acct['name']} already has location row (ID={existing['id']}), skipping")
            continue

        # Get times from account
        opening_time = account.get("opening_time", "11:00")
        closing_time = account.get("closing_time", "22:00")

        location = db.insert("restaurants", {
            "account_id": acct["id"],
            "name": acct["name"],
            "address": acct["address"],
            "phone": acct["phone"],
            "email": acct["email"],
            "opening_time": opening_time,
            "closing_time": closing_time,
        })
        print(f"  Created location for {acct['name']}: restaurants.id = {location['id']}")

    print("\nDone! All demo restaurants now have location rows.")

if __name__ == "__main__":
    main()
