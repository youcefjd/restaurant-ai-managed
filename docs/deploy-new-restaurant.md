# Deploy a New Restaurant (One-Shot Guide)

Add a new restaurant with a working AI phone agent, menu, and dashboard login in one run.

## Prerequisites

- Python 3.12+ with venv activated: `source .venv/bin/activate`
- `.env` file with `RETELL_API_KEY`, `PUBLIC_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`
- Backend deployed to Railway (or wherever `PUBLIC_URL` points)

## Quick Start

### 1. Add the restaurant definition to `backend/setup_demo_restaurants.py`

Add a new entry to the `RESTAURANTS` list. Copy this template and fill in your values:

```python
{
    "name": "Restaurant Name",                    # Business name (shown in dashboard + voice greeting)
    "cuisine": "cuisine_type",                     # For reference only
    "owner_name": "Owner Full Name",
    "owner_email": "owner@restaurant.com",         # Used for login (must be unique)
    "owner_phone": "+15551234567",
    "address": "123 Main St, City, ST 10001",      # Physical address
    "opening_time": "11:00",                       # 24hr format
    "closing_time": "22:00",                       # 24hr format
    "operating_days": [0, 1, 2, 3, 4, 5, 6],      # 0=Mon, 6=Sun
    "voice_id": "11labs-Myra",                     # See Voice Options below
    "boosted_keywords": ["Restaurant Name", "key", "menu", "items"],
    "begin_message": "Hi, thanks for calling Restaurant Name! What can I get for you today?",
    "menu": {
        "name": "Restaurant Name Menu",
        "categories": [
            {
                "name": "Category Name",
                "items": [
                    {
                        "name": "Item Name",
                        "description": "Short description of the item",
                        "price_cents": 1299      # $12.99 = 1299
                    },
                ]
            },
            # Add more categories...
        ]
    }
}
```

### 2. Run the setup script

```bash
source .venv/bin/activate
python -m backend.setup_demo_restaurants
```

The script is **idempotent** -- it skips restaurants that already exist (matched by `owner_email`).

### 3. Set the login password

The setup script does not set a password. Run this after setup:

```bash
source .venv/bin/activate
python3 -c "
from backend.auth import get_password_hash
from backend.database import get_db

db = get_db()
EMAIL = 'owner@restaurant.com'      # <-- change this
PASSWORD = 'your-password-here'      # <-- change this

account = db.query_one('restaurant_accounts', {'owner_email': EMAIL})
if account:
    db.update('restaurant_accounts', account['id'], {
        'password_hash': get_password_hash(PASSWORD)
    })
    print(f'Password set for {account[\"business_name\"]} (ID={account[\"id\"]})')
else:
    print(f'No account found with email {EMAIL}')
"
```

### 4. Verify

```bash
source .venv/bin/activate
python3 -c "
from backend.database import get_db
db = get_db()

EMAIL = 'owner@restaurant.com'      # <-- change this
a = db.query_one('restaurant_accounts', {'owner_email': EMAIL})

print(f'Account:   {a[\"business_name\"]} (ID={a[\"id\"]})')
print(f'Agent:     {a.get(\"retell_agent_id\", \"MISSING\")}')
print(f'LLM:       {a.get(\"retell_llm_id\", \"MISSING\")}')
print(f'Phone:     {a.get(\"twilio_phone_number\", \"MISSING\")}')
print(f'Password:  {\"set\" if a.get(\"password_hash\") else \"NOT SET\"}')
print(f'Active:    {a.get(\"is_active\")}')

loc = db.query_one('restaurants', {'account_id': a['id']})
print(f'Location:  {\"restaurants.id=\" + str(loc[\"id\"]) if loc else \"MISSING - ORDERS WILL FAIL\"}')

menus = db._client.table('menus').select('id').eq('account_id', a['id']).execute()
if menus.data:
    cats = db._client.table('menu_categories').select('id').eq('menu_id', menus.data[0]['id']).execute()
    items = 0
    for c in cats.data:
        items += len(db._client.table('menu_items').select('id').eq('category_id', c['id']).execute().data)
    print(f'Menu:      {len(cats.data)} categories, {items} items')
else:
    print('Menu:      MISSING')

if a.get('retell_agent_id'):
    print(f'Test URL:  https://app.retellai.com/agent/{a[\"retell_agent_id\"]}')
"
```

All fields should show values (not MISSING). If Location shows MISSING, orders will fail with a foreign key error.

---

## What the Setup Script Creates

| Step | Table / Service | What |
|------|----------------|------|
| 1a | `restaurant_accounts` | Business account (name, email, hours, settings) |
| 1b | `restaurants` | Location row (required FK for orders table) |
| 2 | `menus` + `menu_categories` + `menu_items` | Full menu with categories and items |
| 3 | Retell API | LLM with system prompt + function tools pointing to `PUBLIC_URL` |
| 4 | Retell API | Voice agent bound to the LLM |
| 5 | Retell API | Phone number (332 area code) bound to the agent |
| 6 | `restaurant_accounts` | Stores `retell_agent_id`, `retell_llm_id`, `twilio_phone_number` |

**Not created by setup (must do manually):**
- `password_hash` -- see Step 3 above

---

## Voice Options

| Voice ID | Gender | Best For |
|----------|--------|----------|
| `11labs-Myra` | Female | General purpose, warm tone |
| `11labs-Adrian` | Male | Casual, energetic |

Full list: [Retell Voice Library](https://www.retellai.com/docs/build-agent/voice)

---

## Removing a Restaurant

```bash
source .venv/bin/activate
python3 -c "
from backend.database import get_db
db = get_db()
client = db._client

ACCOUNT_ID = 99  # <-- change this

# Delete in order: orders -> menu_items -> menu_categories -> menus -> restaurants -> account
client.table('orders').delete().eq('account_id', ACCOUNT_ID).execute()

menus = client.table('menus').select('id').eq('account_id', ACCOUNT_ID).execute()
for m in menus.data:
    cats = client.table('menu_categories').select('id').eq('menu_id', m['id']).execute()
    for c in cats.data:
        client.table('menu_items').delete().eq('category_id', c['id']).execute()
    client.table('menu_categories').delete().eq('menu_id', m['id']).execute()
client.table('menus').delete().eq('account_id', ACCOUNT_ID).execute()
client.table('restaurants').delete().eq('account_id', ACCOUNT_ID).execute()
client.table('restaurant_accounts').delete().eq('id', ACCOUNT_ID).execute()
print(f'Removed account {ACCOUNT_ID} and all linked data')
"
```

**Note:** This does NOT delete the Retell agent/LLM/phone number. To release those:

```bash
# Get the agent_id and llm_id before deleting the account, then:
curl -X DELETE https://api.retellai.com/delete-agent/AGENT_ID \
  -H "Authorization: Bearer $RETELL_API_KEY"

curl -X DELETE https://api.retellai.com/delete-retell-llm/LLM_ID \
  -H "Authorization: Bearer $RETELL_API_KEY"

# Phone number is released automatically when the agent is deleted
```

---

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `violates foreign key constraint "orders_restaurant_id_fkey"` | Missing `restaurants` (location) row | Insert a row into `restaurants` table with `account_id` matching the restaurant account |
| `Account password not set` | No `password_hash` on account | Run the password-setting script in Step 3 |
| `Restaurant configuration error` | No `restaurant_accounts` row for the given `restaurant_id` | Verify the restaurant_id passed to functions matches an existing account |
| Cart has items from another restaurant | Session ID collision (fixed in code, but stale carts may exist) | Delete stale carts: `client.table('voice_carts').delete().like('call_id', 'session_%').execute()` |
| Agent tools return errors / timeout | LLM tool URLs point to wrong backend | Update LLM tools to point to current `PUBLIC_URL` (see below) |
| Phone number not working | Number not bound to agent in Retell | Check `inbound_agent_id` via Retell API |

### Fix LLM Tool URLs (if backend URL changes)

```bash
source .venv/bin/activate
python3 -c "
import httpx, os
from dotenv import load_dotenv
load_dotenv()

NEW_URL = 'https://your-new-backend-url.com'  # <-- change this
API_KEY = os.getenv('RETELL_API_KEY')
headers = {'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'}

# List all LLMs
resp = httpx.get('https://api.retellai.com/list-retell-llms', headers=headers)
for llm in resp.json():
    llm_id = llm['llm_id']
    tools = llm.get('general_tools', [])
    updated = False
    for tool in tools:
        url = tool.get('url', '')
        if '/api/retell-functions/' in url and NEW_URL not in url:
            endpoint = url.split('/api/retell-functions/')[-1]
            tool['url'] = f'{NEW_URL}/api/retell-functions/{endpoint}'
            updated = True
    if updated:
        resp = httpx.patch(
            f'https://api.retellai.com/update-retell-llm/{llm_id}',
            headers=headers,
            json={'general_tools': tools}
        )
        print(f'Updated LLM {llm_id}: {resp.status_code}')
    else:
        print(f'LLM {llm_id}: already correct')
"
```

---

## Current Restaurants

| ID | Name | Phone | Login Email |
|----|------|-------|-------------|
| 5 | Sal's Pizza | (832) 925-4593 | sal@salspizza.com |
| 6 | Golden Dragon Chinese | (332) 264-7847 | wei@goldendragonct.com |
| 7 | Cluck & Grill | (332) 248-2911 | marcus@cluckandgrill.com |
| 8 | Casa Taqueria | (332) 249-4099 | maria@casataqueria.com |
| 9 | Tandoor Palace | (332) 529-2891 | raj@tandoorpalace.com |
| 10 | Stack Burger Co. | (332) 237-3037 | jake@stackburger.com |
| 11 | Sakura Sushi | (332) 248-2378 | yuki@sakurasushi.com |

All demo accounts use password: `demo123`
