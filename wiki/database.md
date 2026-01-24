# Database

The platform uses **Supabase** (PostgreSQL) for all data storage.

## Connection

Database access is through the Supabase Python client:

```python
from backend.database import get_db, SupabaseDB

# In FastAPI route
def endpoint(db: SupabaseDB = Depends(get_db)):
    result = db.query_one("restaurant_accounts", {"id": 1})
```

## Configuration

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
```

The backend uses `SUPABASE_SERVICE_KEY` (service role) to bypass Row Level Security.

## Core Tables

### restaurant_accounts

Primary tenant table. Each restaurant is an account.

| Column | Type | Description |
|--------|------|-------------|
| id | int | Primary key |
| business_name | string | Restaurant name |
| owner_email | string | Owner's email (unique) |
| owner_phone | string | Owner's phone |
| password_hash | string | Bcrypt hashed password |
| twilio_phone_number | string | Assigned phone number |
| opening_time | time | Daily opening time |
| closing_time | time | Daily closing time |
| operating_days | int[] | Days open (0=Mon, 6=Sun) |
| subscription_tier | enum | FREE, STARTER, PROFESSIONAL, ENTERPRISE |
| subscription_status | enum | TRIAL, ACTIVE, PAST_DUE, CANCELLED, SUSPENDED |
| stripe_customer_id | string | Stripe customer ID |
| stripe_account_id | string | Stripe Connect account |
| platform_commission_rate | decimal | Commission percentage (0-100) |
| trial_ends_at | timestamp | Trial expiration |
| is_active | boolean | Account status |
| onboarding_completed | boolean | Setup complete flag |
| created_at | timestamp | Creation date |

### menus

Menu containers for restaurants.

| Column | Type | Description |
|--------|------|-------------|
| id | int | Primary key |
| account_id | int | FK to restaurant_accounts |
| name | string | Menu name (e.g., "Lunch Menu") |
| description | string | Menu description |
| is_active | boolean | Currently active |
| available_days | int[] | Days available |
| available_start_time | time | Start availability |
| available_end_time | time | End availability |

### menu_categories

Categories within menus.

| Column | Type | Description |
|--------|------|-------------|
| id | int | Primary key |
| menu_id | int | FK to menus |
| name | string | Category name |
| description | string | Category description |
| display_order | int | Sort order |

### menu_items

Individual menu items.

| Column | Type | Description |
|--------|------|-------------|
| id | int | Primary key |
| category_id | int | FK to menu_categories |
| name | string | Item name |
| description | string | Item description |
| price_cents | int | Price in cents |
| dietary_tags | string[] | Tags: vegetarian, vegan, gluten_free, etc. |
| is_available | boolean | Currently available |
| preparation_time_minutes | int | Prep time estimate |
| display_order | int | Sort order |

### menu_modifiers

Modifiers/customizations for items.

| Column | Type | Description |
|--------|------|-------------|
| id | int | Primary key |
| item_id | int | FK to menu_items |
| name | string | Modifier name |
| price_cents | int | Additional price (can be 0) |

### orders

Customer orders.

| Column | Type | Description |
|--------|------|-------------|
| id | int | Primary key |
| account_id | int | FK to restaurant_accounts |
| order_type | enum | TAKEOUT, DELIVERY |
| status | enum | PENDING, CONFIRMED, PREPARING, READY, COMPLETED, CANCELLED |
| customer_name | string | Customer name |
| customer_phone | string | Customer phone |
| customer_email | string | Customer email |
| order_items | json | Array of order items |
| special_instructions | string | Special requests |
| payment_status | enum | UNPAID, PENDING, PAID, REFUNDED |
| payment_method | string | Payment method used |
| delivery_address | string | Delivery address (if applicable) |
| subtotal | int | Subtotal in cents |
| tax | int | Tax in cents |
| delivery_fee | int | Delivery fee in cents |
| total | int | Total in cents |
| conversation_id | string | Link to call/SMS transcript |
| created_at | timestamp | Order creation time |
| pickup_time | timestamp | Requested pickup time |

### deliveries

Delivery tracking for orders.

| Column | Type | Description |
|--------|------|-------------|
| id | int | Primary key |
| order_id | int | FK to orders |
| status | enum | ASSIGNED, PICKED_UP, IN_TRANSIT, DELIVERED, FAILED |
| driver_name | string | Driver name |
| driver_phone | string | Driver phone |
| delivery_address | string | Delivery destination |
| estimated_arrival | timestamp | ETA |
| actual_arrival | timestamp | Actual delivery time |

### tables

Restaurant tables for reservations.

| Column | Type | Description |
|--------|------|-------------|
| id | int | Primary key |
| account_id | int | FK to restaurant_accounts |
| table_number | string | Table identifier |
| capacity | int | Maximum party size |
| location | enum | INDOOR, OUTDOOR, WINDOW, PRIVATE, BAR |
| is_active | boolean | Available for booking |

### bookings

Table reservations.

| Column | Type | Description |
|--------|------|-------------|
| id | int | Primary key |
| account_id | int | FK to restaurant_accounts |
| table_id | int | FK to tables |
| customer_id | int | FK to customers |
| booking_date | date | Reservation date |
| booking_time | time | Reservation time |
| party_size | int | Number of guests |
| status | enum | PENDING, CONFIRMED, CANCELLED, COMPLETED, NO_SHOW |
| special_requests | string | Special requests |
| created_at | timestamp | Creation time |

### customers

Customer records.

| Column | Type | Description |
|--------|------|-------------|
| id | int | Primary key |
| account_id | int | FK to restaurant_accounts |
| phone | string | Customer phone (unique per account) |
| name | string | Customer name |
| email | string | Customer email |
| total_orders | int | Order count |
| total_spent_cents | int | Lifetime spend |
| last_order_date | timestamp | Last order date |

### transcripts

Call and SMS conversation records.

| Column | Type | Description |
|--------|------|-------------|
| id | int | Primary key |
| account_id | int | FK to restaurant_accounts |
| transcript_type | enum | VOICE, SMS |
| customer_phone | string | Customer phone |
| conversation_id | string | Unique conversation ID |
| messages | json | Message array |
| outcome | enum | ORDER_PLACED, BOOKING_CREATED, etc. |
| order_id | int | FK to orders (if order placed) |
| summary | string | AI-generated summary |
| duration_seconds | int | Call duration |
| created_at | timestamp | Start time |

## Database Wrapper

The `SupabaseDB` class provides SQLAlchemy-like methods:

```python
# Query single record
db.query_one("table", {"id": 1})

# Query multiple records
db.query_all("orders", {"account_id": 1}, order_by="created_at", order_desc=True)

# Insert
db.insert("orders", {"customer_name": "John", ...})

# Update
db.update("orders", id=1, {"status": "CONFIRMED"})

# Delete
db.delete("orders", id=1)

# Count
db.count("orders", {"account_id": 1})
```

## Migrations

Database migrations are stored in `backend/migrations/`:
- `001_add_performance_indexes.sql`
- `002_add_analytics_rpc_functions.sql`
- `003_add_audit_logs.sql`

Apply migrations via Supabase SQL editor or CLI.

---

**Related:**
- [Architecture](./architecture.md)
- [API Reference](./api-reference.md)
