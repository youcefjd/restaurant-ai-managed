# 💰 Commission System - Complete Guide

## How Commission Works (Simple Explanation)

### ❌ WRONG: Adding Commission to Customer Bill
```
Customer sees: Pizza $25
You add 5% commission: $1.25
Customer pays: $26.25  ← NO! Wrong!
```

### ✅ CORRECT: Deducting Commission from Restaurant Revenue
```
Customer sees: Pizza $25
Customer pays: $25  ← Menu price only
    ↓
Restaurant receives: $25.00
Platform takes: 5% = $1.25  ← Commission
Restaurant keeps: $23.75
```

**Key principle: Commission is invisible to customers. It's between platform and restaurant.**

---

## Customer Experience

**When AI answers the phone:**
- Customer: "How much is the pizza?"
- AI: "The Margherita Pizza is $25" ← Menu price only
- Customer: "I'll take two"
- AI: "That'll be $50 total" ← Menu price × quantity

**Customer never hears about commission. They only pay menu prices.**

---

## Restaurant Experience

**In their dashboard, they see:**
- Order received: $50.00
- Platform commission (5%): -$2.50
- **Net payout: $47.50**

**Or if commission is disabled:**
- Order received: $50.00
- Platform commission: $0.00
- **Net payout: $50.00**

---

## Platform Admin Controls

### API Endpoint: Update Commission Settings

**Endpoint:** `PUT /api/admin/restaurants/{account_id}/commission`

**Request body:**
```json
{
  "platform_commission_rate": 5.0,
  "commission_enabled": true
}
```

**Example: Set 5% commission for Restaurant #1:**
```bash
curl -X PUT http://localhost:8000/api/admin/restaurants/1/commission \
  -H "Content-Type: application/json" \
  -d '{
    "platform_commission_rate": 5.0,
    "commission_enabled": true
  }'
```

**Example: Disable commission for Restaurant #2:**
```bash
curl -X PUT http://localhost:8000/api/admin/restaurants/2/commission \
  -H "Content-Type: application/json" \
  -d '{
    "platform_commission_rate": 0,
    "commission_enabled": false
  }'
```

**Response:**
```json
{
  "id": 1,
  "business_name": "Mario's Pizza",
  "subscription_tier": "professional",
  "total_orders": 150,
  "total_revenue_cents": 500000,
  "commission_owed_cents": 25000,
  "...": "..."
}
```

---

## Database Fields

### RestaurantAccount Table

```python
platform_commission_rate = Column(Numeric(5, 2), default=10.0)  # 0-100%
commission_enabled = Column(Boolean, default=True)  # On/Off switch
```

**Examples:**
- `platform_commission_rate = 5.0` → 5% commission
- `platform_commission_rate = 10.0` → 10% commission (default)
- `commission_enabled = False` → No commission collected

---

## Commission Calculation

### For Each Order:

```python
# Get restaurant settings
restaurant = db.query(RestaurantAccount).filter_by(id=restaurant_id).first()

# Calculate commission
if restaurant.commission_enabled:
    commission = order.total_cents * (restaurant.platform_commission_rate / 100)
else:
    commission = 0

# Example:
# Order total: $50.00 (5000 cents)
# Commission rate: 5%
# Commission enabled: True
# Commission = 5000 * 0.05 = 250 cents = $2.50
```

### For All Orders (Total Owed):

```python
# Get all orders for a restaurant
orders = db.query(Order).filter(Order.restaurant_id == restaurant_id).all()
total_revenue = sum(order.total_cents for order in orders)

# Calculate total commission owed
if restaurant.commission_enabled:
    total_commission = total_revenue * (restaurant.platform_commission_rate / 100)
else:
    total_commission = 0

# Example:
# 100 orders totaling $10,000
# Commission rate: 5%
# Total commission = $10,000 * 0.05 = $500
```

---

## When Commission is Charged

### Option 1: Real-time (Stripe Connect - Automatic)

**How it works:**
1. Customer pays $25 via credit card
2. Money goes to Stripe
3. Stripe Connect automatically splits:
   - Platform: $1.25 (5% commission)
   - Stripe fees: $0.73 (2.9% + $0.30)
   - Restaurant: $23.02 (remaining)

**Implementation:** Already built in `backend/services/stripe_connect_service.py`

### Option 2: Manual Settlement (Track and Invoice)

**How it works:**
1. Track all orders with commission
2. Generate monthly invoice
3. Restaurant pays platform separately
4. Or deduct from Stripe payouts

**Implementation:** Calculate via API endpoint, invoice manually

---

## Commission Tracking

### Get Commission Report for Restaurant:

```bash
curl http://localhost:8000/api/admin/restaurants/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response includes:**
```json
{
  "total_orders": 150,
  "total_revenue_cents": 500000,
  "commission_owed_cents": 25000
}
```

**Means:**
- 150 orders processed
- $5,000 total revenue
- $250 commission owed

---

## Pricing Models

### Model 1: Commission Only
```
Subscription: $0/month
Commission: 10% on all orders
```

### Model 2: Subscription Only
```
Subscription: $99/month
Commission: 0%
```

### Model 3: Hybrid (Recommended)
```
Subscription: $99/month
Commission: 3-5% on AI phone orders only
```

**Set per restaurant using the API!**

---

## AI Pricing Behavior

**What AI says to customers:**

✅ **Correct:**
- "The Margherita Pizza is $25"
- "Two pizzas will be $50"
- "Your total is $50"

❌ **Wrong:**
- "The pizza is $25 plus commission" ← NO!
- "That's $26.25 including platform fee" ← NO!
- Never mention commission to customers

**The AI uses menu prices directly. Commission is calculated on the backend after the sale.**

---

## Frontend UI (To Be Built)

### Admin Dashboard - Restaurant Management

**Commission Settings Card:**
```
┌─────────────────────────────────────────┐
│ Restaurant: Mario's Pizza               │
├─────────────────────────────────────────┤
│ Commission Rate:  [5.0]%  [Update]     │
│                                         │
│ Commission Enabled: [✓ On] [ Off]      │
│                                         │
│ Total Revenue: $5,000.00                │
│ Commission Owed: $250.00                │
│                                         │
│ [View Detailed Report]                  │
└─────────────────────────────────────────┘
```

**Implementation:**
- Add to admin dashboard
- Call `PUT /api/admin/restaurants/{id}/commission`
- Show confirmation
- Display updated commission owed

---

## Common Questions

### Q: Does the customer see commission?
**A:** No. Customer only sees and pays menu prices.

### Q: When is commission collected?
**A:** With Stripe Connect: Automatically during payment. Otherwise: Track and invoice monthly.

### Q: Can I charge different rates per restaurant?
**A:** Yes! Each restaurant has its own `platform_commission_rate`.

### Q: Can I disable commission for specific restaurants?
**A:** Yes! Set `commission_enabled = false` via API.

### Q: Is commission charged on manual orders?
**A:** That's up to you. Currently calculates on ALL orders. You can filter by `order_source` field to only charge on AI phone orders.

### Q: How does the AI know not to mention commission?
**A:** The AI only knows about menu prices. Commission is calculated after the order is placed, on the backend.

---

## Testing Commission System

### Test 1: Create Order and Calculate Commission

```bash
# 1. Check current commission settings
curl http://localhost:8000/api/admin/restaurants/1

# 2. Set 5% commission
curl -X PUT http://localhost:8000/api/admin/restaurants/1/commission \
  -H "Content-Type: application/json" \
  -d '{"platform_commission_rate": 5.0, "commission_enabled": true}'

# 3. Create $50 order
curl -X POST http://localhost:8000/api/1/orders \
  -H "Authorization: Bearer TOKEN" \
  -d '{...order with $50 total...}'

# 4. Check commission owed
curl http://localhost:8000/api/admin/restaurants/1

# Expected: commission_owed_cents increased by 250 ($2.50 = 5% of $50)
```

### Test 2: Disable Commission

```bash
# Disable commission
curl -X PUT http://localhost:8000/api/admin/restaurants/1/commission \
  -H "Content-Type: application/json" \
  -d '{"platform_commission_rate": 0, "commission_enabled": false}'

# Create another order
# Expected: commission_owed_cents doesn't change
```

---

## Summary

✅ **Backend API:** Commission endpoints implemented
✅ **Database:** Commission fields exist
✅ **Calculation:** Automatic commission calculation
✅ **Stripe Connect:** Automatic split payments (already built)
⚠️ **Frontend UI:** Needs admin interface (not built yet)
⚠️ **Order Source Filtering:** Can add to only charge commission on AI orders

**The system is 80% complete. Just needs admin UI for managing commission settings!**
