# Data Models and Workflows - Functional Specification

**Purpose**: Detailed data model definitions and complete workflow descriptions

---

## Data Models (Entity Definitions)

### RestaurantAccount

**Purpose**: Represents a restaurant business account (multi-tenant root entity)

**Properties**:
- `id` (unique identifier)
- `business_name` (string) - Legal business name
- `owner_name` (string) - Owner/primary contact name
- `owner_email` (string, unique) - Owner email (used for login)
- `owner_phone` (string, optional) - Owner phone number
- `phone` (string, optional) - Restaurant public contact phone
- `twilio_phone_number` (string, unique, optional) - Phone number for AI calls/SMS
- `opening_time` (string, format "HH:MM") - Daily opening time (e.g., "09:00")
- `closing_time` (string, format "HH:MM") - Daily closing time (e.g., "22:00")
- `operating_days` (array of integers) - Days of week [0-6] where 0=Monday, 6=Sunday
- `subscription_tier` (enum) - FREE, STARTER, PROFESSIONAL, ENTERPRISE
- `subscription_status` (enum) - TRIAL, ACTIVE, PAST_DUE, CANCELLED, SUSPENDED
- `stripe_customer_id` (string, optional) - Stripe customer ID for subscriptions
- `stripe_account_id` (string, optional) - Stripe Connect account ID for payouts
- `platform_commission_rate` (decimal, 0-100) - Commission percentage (default 10.0)
- `commission_enabled` (boolean) - Whether commission is active (default true)
- `onboarding_completed` (boolean) - Whether setup is complete (default false)
- `is_active` (boolean) - Whether account is active (default true)
- `trial_ends_at` (datetime, optional) - When trial period ends
- `created_at` (datetime)
- `updated_at` (datetime)

**Relationships**:
- Has many `Menu` records
- Has many `Restaurant` (location) records
- Has many `Order` records

**Business Rules**:
- Email must be unique across all accounts
- `twilio_phone_number` must be unique if set
- `platform_commission_rate` must be between 0 and 100
- Trial period is 30 days from account creation (default)

---

### Restaurant (Location)

**Purpose**: Represents a physical restaurant location (future: multiple locations per account)

**Properties**:
- `id` (unique identifier)
- `account_id` (foreign key to RestaurantAccount)
- `name` (string) - Location name (e.g., "Downtown Location")
- `address` (text) - Full street address
- `phone` (string, optional) - Location-specific phone
- `email` (string, optional) - Location-specific email
- `opening_time` (time) - Location-specific opening time
- `closing_time` (time) - Location-specific closing time
- `booking_duration_minutes` (integer) - Default reservation duration (default 90)
- `max_party_size` (integer) - Maximum party size allowed (default 10)
- `created_at` (datetime)
- `updated_at` (datetime)

**Relationships**:
- Belongs to one `RestaurantAccount`
- Has many `Table` records
- Has many `Booking` records

**Business Rules**:
- Each account can have one or more locations (currently supports one, extensible to many)
- `opening_time` must be before `closing_time`
- `booking_duration_minutes` must be positive

---

### Menu

**Purpose**: Top-level menu container (restaurant can have multiple menus)

**Properties**:
- `id` (unique identifier)
- `account_id` (foreign key to RestaurantAccount)
- `name` (string) - Menu name (e.g., "Dinner Menu", "Lunch Specials")
- `description` (text, optional) - Menu description
- `is_active` (boolean) - Whether menu is currently active (default true)
- `available_days` (array of integers, optional) - Days menu is available [0-6]
- `available_start_time` (string, optional, format "HH:MM") - When menu becomes available
- `available_end_time` (string, optional, format "HH:MM") - When menu stops being available
- `created_at` (datetime)
- `updated_at` (datetime)

**Relationships**:
- Belongs to one `RestaurantAccount`
- Has many `MenuCategory` records

**Business Rules**:
- Restaurant can have multiple menus (e.g., Lunch Menu, Dinner Menu, Brunch Menu)
- Only active menus appear in AI context

---

### MenuCategory

**Purpose**: Groups menu items (e.g., Appetizers, Main Courses, Desserts)

**Properties**:
- `id` (unique identifier)
- `menu_id` (foreign key to Menu)
- `name` (string) - Category name
- `description` (text, optional) - Category description
- `display_order` (integer) - Sort order within menu (default 0)
- `created_at` (datetime)

**Relationships**:
- Belongs to one `Menu`
- Has many `MenuItem` records

**Business Rules**:
- `display_order` determines sorting (lower numbers first)

---

### MenuItem

**Purpose**: Individual menu item

**Properties**:
- `id` (unique identifier)
- `category_id` (foreign key to MenuCategory)
- `name` (string) - Item name
- `description` (text, optional) - Item description
- `price_cents` (integer) - Price in cents (e.g., 1200 = $12.00)
- `dietary_tags` (array of strings, optional) - Tags like ["vegetarian", "gluten_free", "halal"]
- `is_available` (boolean) - Current availability status (default true)
- `image_url` (string, optional) - Item image URL
- `preparation_time_minutes` (integer, optional) - Estimated prep time
- `display_order` (integer) - Sort order within category (default 0)
- `created_at` (datetime)
- `updated_at` (datetime)

**Relationships**:
- Belongs to one `MenuCategory`
- Has many `MenuModifier` records

**Business Rules**:
- `price_cents` must be non-negative (can be 0 for free items)
- `is_available` can be toggled in real-time without editing menu
- Only available items appear in AI responses
- `dietary_tags` used for filtering (vegetarian, vegan, gluten_free, etc.)

**Key Feature**: Real-time availability toggle - restaurant can mark items unavailable instantly without menu edits.

---

### MenuModifier

**Purpose**: Customization options for menu items (e.g., "Extra cheese", "No onions", "Spicy level")

**Properties**:
- `id` (unique identifier)
- `item_id` (foreign key to MenuItem)
- `name` (string) - Modifier name (e.g., "Extra cheese", "No onions")
- `price_adjustment_cents` (integer) - Price change in cents (positive or negative, default 0)
- `is_default` (boolean) - Whether modifier is selected by default (default false)
- `modifier_group` (string, optional) - Group for mutually exclusive modifiers (e.g., "Size", "Toppings")
- `created_at` (datetime)

**Relationships**:
- Belongs to one `MenuItem`

**Business Rules**:
- `price_adjustment_cents` can be negative (discount) or positive (add-on)
- Multiple modifiers can be applied to same item
- Modifiers in same `modifier_group` are mutually exclusive (future)

**Examples**:
- "Extra cheese": `price_adjustment_cents = 50` ($0.50)
- "No onions": `price_adjustment_cents = 0` (free modification)
- "Large size": `price_adjustment_cents = 300` ($3.00)

---

### Table

**Purpose**: Represents a dining table for reservations

**Properties**:
- `id` (unique identifier)
- `restaurant_id` (foreign key to Restaurant)
- `table_number` (string) - Table identifier (e.g., "T1", "Table 5")
- `capacity` (integer) - Maximum number of seats
- `location` (string, optional) - Location description (e.g., "Window", "Patio")
- `is_active` (boolean) - Whether table is available for bookings (default true)
- `created_at` (datetime)

**Relationships**:
- Belongs to one `Restaurant`
- Has many `Booking` records

**Business Rules**:
- `capacity` must be positive
- `table_number` must be unique within restaurant
- `is_active = false` means table is out of service (maintenance, reserved, etc.)
- Only active tables are considered for availability checking

**Key Feature**: Table status can be toggled (take out of service) without deleting table.

---

### Order

**Purpose**: Customer order (takeout, delivery, or dine-in)

**Properties**:
- `id` (unique identifier)
- `restaurant_id` (foreign key to Restaurant, optional for legacy)
- `account_id` (foreign key to RestaurantAccount)
- `order_type` (enum) - TAKEOUT, DELIVERY, DINE_IN
- `customer_name` (string)
- `customer_phone` (string)
- `customer_email` (string, optional)
- `delivery_address` (text, optional) - Required if `order_type = DELIVERY`
- `order_items` (JSON) - Array of items with quantities and modifiers
- `total_cents` (integer) - Total order price in cents
- `status` (enum) - PENDING, CONFIRMED, PREPARING, READY, OUT_FOR_DELIVERY, DELIVERED, CANCELLED
- `special_instructions` (text, optional)
- `order_source` (string, optional) - Where order came from (e.g., "voice", "sms", "manual")
- `created_at` (datetime)
- `updated_at` (datetime)

**Relationships**:
- Belongs to one `RestaurantAccount` (and optionally `Restaurant`)
- Has one `Delivery` record (if `order_type = DELIVERY`)

**Business Rules**:
- `order_items` JSON structure:
  ```json
  [
    {
      "item_id": 1,
      "item_name": "Chicken Shawarma Wrap",
      "quantity": 2,
      "price_cents": 1200,
      "modifiers": ["Extra cheese", "No onions"],
      "subtotal_cents": 2500
    }
  ]
  ```
- `total_cents` must equal sum of item subtotals
- `delivery_address` required if `order_type = DELIVERY`
- Status transitions: PENDING → CONFIRMED → PREPARING → READY → (OUT_FOR_DELIVERY) → DELIVERED
- Orders can be CANCELLED at any stage

---

### Delivery

**Purpose**: Delivery tracking for delivery orders

**Properties**:
- `id` (unique identifier)
- `order_id` (foreign key to Order)
- `driver_name` (string, optional)
- `driver_phone` (string, optional)
- `status` (enum) - ASSIGNED, PICKED_UP, IN_TRANSIT, DELIVERED, FAILED
- `estimated_delivery_time` (datetime, optional)
- `actual_delivery_time` (datetime, optional)
- `created_at` (datetime)
- `updated_at` (datetime)

**Relationships**:
- Belongs to one `Order` (one-to-one)

**Business Rules**:
- Only exists if `Order.order_type = DELIVERY`
- Status transitions: ASSIGNED → PICKED_UP → IN_TRANSIT → DELIVERED

---

### Booking (Reservation)

**Purpose**: Table reservation

**Properties**:
- `id` (unique identifier)
- `restaurant_id` (foreign key to Restaurant)
- `table_id` (foreign key to Table, optional initially)
- `customer_id` (foreign key to Customer)
- `booking_date` (date) - Date of reservation
- `booking_time` (time) - Time of reservation
- `party_size` (integer) - Number of guests
- `duration_minutes` (integer) - Reservation duration (default 90)
- `status` (enum) - PENDING, CONFIRMED, SEATED, COMPLETED, CANCELLED, NO_SHOW
- `special_requests` (text, optional)
- `created_at` (datetime)
- `updated_at` (datetime)

**Relationships**:
- Belongs to one `Restaurant`
- Belongs to one `Table` (assigned automatically or manually)
- Belongs to one `Customer`

**Business Rules**:
- `party_size` must be positive
- `duration_minutes` defaults to 90
- `table_id` assigned automatically based on capacity and availability
- No overlapping reservations on same table (enforced by availability checking)
- Status transitions: PENDING → CONFIRMED → SEATED → COMPLETED
- Can be CANCELLED or marked NO_SHOW at any stage

---

### Customer

**Purpose**: Customer information (identified by phone number)

**Properties**:
- `id` (unique identifier)
- `phone` (string, unique) - Primary identifier (phone number)
- `name` (string)
- `email` (string, optional)
- `notes` (text, optional) - Internal notes (allergies, preferences, etc.)
- `total_bookings` (integer) - Total bookings made (default 0)
- `no_shows` (integer) - Number of no-show incidents (default 0)
- `created_at` (datetime)
- `updated_at` (datetime)

**Relationships**:
- Has many `Booking` records

**Business Rules**:
- `phone` is unique and primary identifier
- Customer created automatically on first order/booking if not exists
- `total_bookings` and `no_shows` tracked for analytics

---

## Complete Workflows

### Workflow 1: Restaurant Onboarding

**Actor**: Restaurant Owner

**Steps**:
1. Restaurant owner visits signup page
2. Fills form: business_name, owner_name, owner_email, owner_phone
3. System creates `RestaurantAccount`:
   - `subscription_tier = FREE`
   - `subscription_status = TRIAL`
   - `trial_ends_at = created_at + 30 days`
   - `platform_commission_rate = 10.0`
   - `commission_enabled = true`
   - `onboarding_completed = false`
4. System creates `Restaurant` (location):
   - Links to `RestaurantAccount`
   - Sets default `booking_duration_minutes = 90`
   - Sets default `max_party_size = 10`
5. Restaurant owner receives login credentials
6. Restaurant owner logs in
7. Restaurant creates `Menu`:
   - Sets menu name (e.g., "Main Menu")
   - `is_active = true`
8. Restaurant creates `MenuCategory` records:
   - Adds categories (e.g., "Appetizers", "Main Courses")
   - Sets `display_order`
9. Restaurant creates `MenuItem` records:
   - Adds items to categories
   - Sets name, description, `price_cents`
   - Sets `dietary_tags` (optional)
   - Sets `is_available = true`
10. Restaurant creates `MenuModifier` records (optional):
    - Adds modifiers to items
    - Sets `price_adjustment_cents`
11. Restaurant creates `Table` records (optional):
    - Adds tables with `table_number`, `capacity`
    - Sets `is_active = true`
12. Restaurant sets operating hours:
    - Sets `opening_time`, `closing_time`
    - Sets `operating_days`
13. Restaurant assigns phone number for AI (optional):
    - Sets `twilio_phone_number`
14. System sets `onboarding_completed = true`

**Outcome**: Restaurant account fully configured and ready to receive orders/reservations.

---

### Workflow 2: Customer Places Order via Phone

**Actors**: Customer (via phone), AI System, Restaurant

**Steps**:
1. Customer calls `RestaurantAccount.twilio_phone_number`
2. Voice service receives call, sends webhook to `/api/voice/welcome`
3. System identifies `RestaurantAccount` by phone number
4. System loads restaurant context:
   - Menu (with only available items)
   - Operating hours
   - Settings
5. AI generates greeting: "Thanks for calling [Business Name]"
6. Voice service plays greeting to customer
7. Customer speaks: "I want to order a pizza"
8. Speech-to-text converts to text: "I want to order a pizza"
9. Voice service sends webhook to `/api/voice/process` with text
10. AI processes request with menu context
11. AI responds: "We have Margherita ($15), Pepperoni ($17)..."
12. Customer: "Pepperoni, large, extra cheese"
13. AI processes: Extracts item, size, modifier
14. AI calculates price: $17.00 (base) + $0.50 (extra cheese) = $17.50
15. AI: "Large pepperoni with extra cheese, $17.50. Delivery or pickup?"
16. Customer: "Delivery to 123 Main St"
17. AI: "Total: $17.50. Confirm order?"
18. Customer: "Yes"
19. System creates `Order`:
    - `order_type = DELIVERY`
    - `customer_name = null` (if not collected)
    - `customer_phone = caller_phone`
    - `delivery_address = "123 Main St"`
    - `order_items = [{"item_id": 2, "name": "Pepperoni Pizza", "quantity": 1, "modifiers": ["large", "extra cheese"], "subtotal_cents": 1750}]`
    - `total_cents = 1750`
    - `status = PENDING`
    - `order_source = "voice"`
20. System creates `Delivery` record:
    - `order_id = order.id`
    - `status = ASSIGNED`
21. System calculates commission (if enabled):
    - `commission = 1750 * (10 / 100) = 175 cents = $1.75`
    - Tracked in `RestaurantAccount` (not stored per order, calculated on demand)
22. AI: "✅ Order #1234 confirmed! Total: $17.50. We'll have it ready in 30 minutes."
23. System sends SMS confirmation to `customer_phone`
24. Order appears in restaurant dashboard (status: PENDING)
25. Customer hangs up

**Outcome**: Order created in database, restaurant notified, customer receives confirmation.

---

### Workflow 3: Restaurant Fulfills Order

**Actor**: Restaurant Owner/Staff

**Steps**:
1. Restaurant owner opens dashboard → Orders section
2. Sees new order: Order #1234 (status: PENDING)
3. Restaurant confirms order:
   - Updates `Order.status = CONFIRMED`
4. Kitchen starts preparing:
   - Updates `Order.status = PREPARING`
5. Order ready:
   - Updates `Order.status = READY`
   - If delivery: Updates `Delivery.status = PICKED_UP`
   - Assigns driver (if applicable):
     - Updates `Delivery.driver_name`, `Delivery.driver_phone`
6. If delivery:
   - Updates `Delivery.status = IN_TRANSIT`
   - Updates `Order.status = OUT_FOR_DELIVERY`
7. Order delivered:
   - Updates `Delivery.status = DELIVERED`
   - Updates `Delivery.actual_delivery_time = now()`
   - Updates `Order.status = DELIVERED`
8. Payment processed (if not already):
   - Customer pays $17.50
   - Platform commission ($1.75) automatically deducted
   - Restaurant receives $15.75 (via Stripe Connect)

**Outcome**: Order fulfilled, payment processed, commission collected.

---

### Workflow 4: Customer Makes Reservation via SMS

**Actors**: Customer (via SMS), AI System, Restaurant

**Steps**:
1. Customer texts `RestaurantAccount.twilio_phone_number`: "Table for 4 tonight at 7pm"
2. SMS service receives message, sends webhook to `/api/voice/sms/incoming`
3. System identifies `RestaurantAccount` by phone number
4. System loads conversation state (if exists):
   - Conversation history
   - Current context
5. System loads restaurant context:
   - Available tables
   - Existing bookings
6. AI processes request:
   - Parses: `party_size = 4`, `date = today`, `time = 19:00`
   - Checks availability: Queries `Table` records with `capacity >= 4` and `is_active = true`
   - Checks conflicts: Queries `Booking` records for overlapping times
   - Finds available table: `Table` with `id = 3`, `capacity = 4`
7. AI responds: "Great! I have a table for 4 available at 7pm tonight. What name?"
8. Customer texts: "Sarah Johnson"
9. System creates or finds `Customer`:
   - If `Customer.phone` exists: Use existing
   - If not: Create new `Customer` with `phone = sender_phone`, `name = "Sarah Johnson"`
10. System creates `Booking`:
    - `restaurant_id = restaurant.id`
    - `table_id = 3` (automatically assigned)
    - `customer_id = customer.id`
    - `booking_date = today`
    - `booking_time = 19:00`
    - `party_size = 4`
    - `duration_minutes = 90`
    - `status = CONFIRMED`
11. AI responds: "✅ Table reserved! 4 guests, tonight 7pm. Table #3. Confirmation #5678"
12. System sends SMS confirmation to customer
13. Reservation appears in restaurant dashboard

**Outcome**: Reservation created, table assigned, customer receives confirmation.

---

### Workflow 5: Restaurant Toggles Menu Item Availability

**Actor**: Restaurant Owner

**Steps**:
1. Restaurant owner notices: Out of salmon
2. Opens dashboard → Menu section
3. Finds "Grilled Salmon" menu item
4. Clicks "Availability" toggle → Sets `MenuItem.is_available = false`
5. System updates `MenuItem` record immediately
6. Next customer calls: "Do you have salmon?"
7. AI loads menu context:
   - Filters out items where `is_available = false`
   - "Grilled Salmon" not in context
8. AI responds: "Sorry, we're currently out of salmon. Would you like to try [alternative] instead?"
9. Later, restaurant receives salmon delivery
10. Restaurant owner toggles availability: `MenuItem.is_available = true`
11. Next customer: "Do you have salmon?"
12. AI responds: "Yes! We have Grilled Salmon ($18.99). Would you like to order it?"

**Outcome**: Menu availability updated in real-time without menu edits.

---

### Workflow 6: Admin Manages Restaurant Commission

**Actor**: Platform Administrator

**Steps**:
1. Admin logs into admin dashboard
2. Views restaurants list
3. Clicks on Restaurant #5 (e.g., "Pizza Palace")
4. Views restaurant details:
   - Total orders: 150
   - Total revenue: $5,000 (500000 cents)
   - Current commission rate: 10%
   - Commission owed: $500 (calculated: $5,000 × 10%)
5. Admin decides to reduce commission for this restaurant:
   - Updates `RestaurantAccount.platform_commission_rate = 5.0`
   - `commission_enabled = true` (unchanged)
6. System updates `RestaurantAccount` record
7. Next order from Restaurant #5:
   - Order total: $50 (5000 cents)
   - Commission: $50 × 5% = $2.50 (instead of $5.00)
   - Restaurant receives: $47.50 (instead of $45.00)
8. Admin views updated commission report:
   - New commission rate: 5%
   - Commission on new orders calculated at 5%

**Outcome**: Commission rate updated, affects future orders (not retroactive).

---

### Workflow 7: Reservation Conflict Prevention

**Actors**: System (automatic), Customer, AI System

**Scenario**: Table already booked at requested time

**Steps**:
1. Existing booking:
   - `Table.id = 2`
   - `booking_date = 2026-01-20`
   - `booking_time = 19:00`
   - `duration_minutes = 90`
   - Time slot: 19:00 - 20:30
2. Customer requests: "Table for 4 tonight at 7pm"
3. System checks availability:
   - Finds `Table` records: `capacity >= 4` and `is_active = true`
   - Table #2: `capacity = 4` ✓
   - Checks conflicts:
     - Query `Booking` for `table_id = 2`, `booking_date = 2026-01-20`
     - Finds existing booking: 19:00 - 20:30
     - Requested time: 19:00 - 20:30
     - Conflict detected! ❌
   - Table #2 is NOT available
   - Checks other tables: Table #5 available ✓
4. System assigns Table #5 (if available)
5. If NO tables available:
   - System finds alternative times:
     - Checks 18:00 (available ✓)
     - Checks 18:30 (available ✓)
     - Checks 20:00 (available ✓)
   - AI responds: "I don't have a table for 4 available at 7pm. However, I have availability at 6pm, 6:30pm, or 8pm. Would any of those work?"

**Outcome**: Double-booking prevented, alternative times suggested.

---

## Business Rules Summary

### Commission Rules
- Commission calculated on order total (menu prices only)
- Commission invisible to customers
- Commission rate configurable per restaurant (0-100%)
- Commission can be enabled/disabled per restaurant
- Commission tracked but calculated on-demand (not stored per order)

### Availability Rules
- Only `is_available = true` menu items appear in AI responses
- Only `is_active = true` tables considered for reservations
- Reservation conflicts prevented (no overlapping bookings)
- Reservation duration: 90 minutes (configurable per restaurant)

### Order Rules
- Order must have at least one item
- `total_cents` must equal sum of item subtotals
- `delivery_address` required if `order_type = DELIVERY`
- Order status progresses sequentially (cannot skip stages)

### Reservation Rules
- Party size must be <= table capacity
- No overlapping reservations on same table
- Table automatically assigned (smallest suitable table)
- Reservation duration: 90 minutes default

### Multi-Tenant Rules
- Each restaurant has unique phone number
- Menu data isolated per restaurant
- Orders/reservations linked to specific restaurant
- No data sharing between restaurants

---

**End of Data Models and Workflows**
