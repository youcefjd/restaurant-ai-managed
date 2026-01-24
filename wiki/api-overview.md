# API Overview

The backend provides a REST API built with FastAPI.

## Base URL

- Development: `http://localhost:8000`
- API Documentation: `http://localhost:8000/api/docs` (Swagger UI)

## API Structure

```
/api
├── /auth           # Authentication
├── /restaurant     # Restaurant order management
├── /onboarding     # Menu and settings management
├── /admin          # Platform admin operations
├── /retell         # Voice AI webhooks
├── /stripe-connect # Payment integration
├── /tables         # Table management
├── /bookings       # Reservations
├── /deliveries     # Delivery tracking
└── /customers      # Customer data
```

## Route Modules

| Module | File | Purpose |
|--------|------|---------|
| Auth | `backend/api/auth.py` | Login, signup, token verification |
| Restaurant | `backend/api/orders.py` | Order CRUD and analytics |
| Onboarding | `backend/api/onboarding.py` | Menu, settings, accounts |
| Admin | `backend/api/platform_admin.py` | Platform management |
| Retell | `backend/api/retell_voice.py` | Voice webhooks |
| Stripe | `backend/api/stripe_connect.py` | Payment integration |
| Tables | `backend/api/tables.py` | Table management |
| Bookings | `backend/api/bookings.py` | Reservations |
| Deliveries | `backend/api/deliveries.py` | Delivery tracking |
| Transcripts | `backend/api/transcripts.py` | Call records |

## Authentication

Most endpoints require a JWT token:

```
Authorization: Bearer {token}
```

Obtain tokens via:
- `POST /auth/login` - Restaurant login
- `POST /auth/admin/login` - Admin login

## Common Patterns

### Pagination

```
GET /api/orders?offset=0&limit=20
```

### Filtering

```
GET /api/orders?status=PENDING&account_id=1
```

### Date Ranges

```
GET /api/orders?start_date=2026-01-01&end_date=2026-01-31
```

## Response Format

Success responses return the resource directly:

```json
{
  "id": 1,
  "name": "Order #1",
  ...
}
```

Error responses follow:

```json
{
  "detail": "Error message"
}
```

## Key Endpoints by Feature

### Orders
- `GET /api/restaurant/orders/today` - Today's orders
- `GET /api/restaurant/orders/active` - Active orders
- `PATCH /api/restaurant/orders/{id}/status` - Update status
- `GET /api/restaurant/orders/analytics/summary` - Analytics

### Menu
- `GET /api/onboarding/accounts/{id}/menu-full` - Full menu
- `POST /api/onboarding/accounts/{id}/menus` - Create menu
- `POST /api/onboarding/items` - Add menu item
- `PUT /api/onboarding/items/{id}` - Update item

### Settings
- `PATCH /api/onboarding/accounts/{id}/operating-hours` - Update hours
- `PATCH /api/onboarding/accounts/{id}/twilio-phone` - Set phone

### Admin
- `GET /api/admin/stats` - Platform statistics
- `GET /api/admin/restaurants` - All restaurants
- `PUT /api/admin/restaurants/{id}/commission` - Set commission

## Health Check

```
GET /health
```

Returns service status and availability of external services.

---

**Related:**
- [API Reference](./api-reference.md)
- [Authentication](./authentication.md)
