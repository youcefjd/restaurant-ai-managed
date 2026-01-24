# API Reference

Detailed endpoint documentation for the Restaurant AI Platform.

## Authentication

### POST /auth/login

Restaurant owner login.

**Request:**
```
Content-Type: application/x-www-form-urlencoded

username=email@example.com&password=secret
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "email@example.com",
    "business_name": "Restaurant Name"
  }
}
```

### POST /auth/signup

Create new restaurant account.

**Request:**
```json
{
  "business_name": "New Restaurant",
  "owner_email": "owner@example.com",
  "owner_phone": "4155551234",
  "password": "securepassword"
}
```

### GET /auth/me

Get current authenticated user.

**Headers:** `Authorization: Bearer {token}`

---

## Orders

### GET /api/restaurant/orders/today

Get today's orders for the authenticated restaurant.

**Response:**
```json
[
  {
    "id": 1,
    "order_type": "TAKEOUT",
    "status": "PENDING",
    "customer_name": "John Doe",
    "customer_phone": "+14155551234",
    "order_items": [...],
    "total": 2500,
    "created_at": "2026-01-24T12:00:00Z"
  }
]
```

### GET /api/restaurant/orders/active

Get orders with status PENDING, CONFIRMED, or PREPARING.

### GET /api/restaurant/orders/{id}

Get single order by ID.

### PATCH /api/restaurant/orders/{id}/status

Update order status.

**Request:**
```json
{
  "status": "PREPARING"
}
```

Valid statuses: `PENDING`, `CONFIRMED`, `PREPARING`, `READY`, `COMPLETED`, `CANCELLED`

### PATCH /api/restaurant/orders/{id}/payment

Update payment status.

**Request:**
```json
{
  "payment_status": "PAID",
  "payment_method": "CARD"
}
```

### GET /api/restaurant/orders/stats

Order statistics summary.

**Response:**
```json
{
  "pending_count": 5,
  "completed_today": 23,
  "revenue_today": 125000,
  "average_order_value": 5434
}
```

### GET /api/restaurant/orders/analytics/summary

Analytics summary with customizable date range.

**Query params:** `days=30`

### GET /api/restaurant/orders/analytics/trends

Revenue trends over time.

**Query params:** `days=30`

### GET /api/restaurant/orders/analytics/popular-items

Most ordered items.

**Query params:** `days=30`, `limit=10`

---

## Menu Management

### GET /api/onboarding/accounts/{id}/menu-full

Get complete menu structure with categories and items.

**Response:**
```json
{
  "menus": [
    {
      "id": 1,
      "name": "Main Menu",
      "categories": [
        {
          "id": 1,
          "name": "Appetizers",
          "items": [
            {
              "id": 1,
              "name": "Spring Roll",
              "price_cents": 599,
              "is_available": true,
              "dietary_tags": ["vegetarian"]
            }
          ]
        }
      ]
    }
  ]
}
```

### POST /api/onboarding/accounts/{id}/menus

Create new menu.

**Request:**
```json
{
  "name": "Lunch Menu",
  "description": "Available 11am-3pm"
}
```

### POST /api/onboarding/menus/{id}/categories

Add category to menu.

**Request:**
```json
{
  "name": "Main Courses",
  "description": "Entrees and mains"
}
```

### POST /api/onboarding/items

Create menu item.

**Request:**
```json
{
  "category_id": 1,
  "name": "Kung Pao Chicken",
  "description": "Spicy chicken with peanuts",
  "price_cents": 1499,
  "dietary_tags": ["spicy"],
  "is_available": true
}
```

### PUT /api/onboarding/items/{id}

Update menu item.

### DELETE /api/onboarding/items/{id}

Delete menu item.

### POST /api/onboarding/modifiers

Add modifier to item.

**Request:**
```json
{
  "item_id": 1,
  "name": "Extra Spicy",
  "price_cents": 0
}
```

---

## Settings

### PATCH /api/onboarding/accounts/{id}/operating-hours

Update operating hours.

**Request:**
```json
{
  "opening_time": "09:00",
  "closing_time": "22:00",
  "operating_days": [0, 1, 2, 3, 4, 5, 6]
}
```

### PATCH /api/onboarding/accounts/{id}/twilio-phone

Set restaurant phone number.

**Request:**
```json
{
  "phone_number": "+14155551234"
}
```

---

## Transcripts

### GET /api/onboarding/accounts/{id}/transcripts

Get call and SMS transcripts.

**Query params:**
- `type`: `VOICE` or `SMS`
- `limit`: Number of records
- `offset`: Pagination offset

---

## Platform Admin

### GET /api/admin/stats

Platform-wide statistics.

**Response:**
```json
{
  "total_restaurants": 25,
  "active_restaurants": 22,
  "total_orders": 1500,
  "total_revenue_cents": 7500000,
  "platform_commission_cents": 750000
}
```

### GET /api/admin/restaurants

List all restaurants with filtering.

**Query params:**
- `status_filter`: `active`, `trial`, `suspended`
- `limit`, `offset`

### PUT /api/admin/restaurants/{id}/commission

Update restaurant commission rate.

**Request:**
```json
{
  "commission_rate": 12.5
}
```

### POST /api/admin/restaurants/{id}/suspend

Suspend a restaurant account.

### POST /api/admin/restaurants/{id}/activate

Activate a suspended account.

---

## Stripe Connect

### GET /api/stripe-connect/status/{account_id}

Get Stripe Connect status.

### POST /api/stripe-connect/onboard

Start Stripe onboarding.

**Request:**
```json
{
  "account_id": 1,
  "refresh_url": "https://...",
  "return_url": "https://..."
}
```

### GET /api/stripe-connect/balance/{account_id}

Get Stripe account balance.

### GET /api/stripe-connect/dashboard-link/{account_id}

Get link to Stripe Express dashboard.

---

## Retell Voice

### POST /api/retell/webhook

Receives Retell call lifecycle events.

### WebSocket /api/retell/chat

Real-time conversation with Retell AI.

---

## Health

### GET /health

System health check.

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "llm": "gemini",
  "services": {
    "retell": true,
    "stripe": true
  }
}
```

---

**Related:**
- [API Overview](./api-overview.md)
- [Authentication](./authentication.md)
