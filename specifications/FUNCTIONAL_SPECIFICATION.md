# Restaurant AI Platform - Functional Specification

**Version:** 1.0  
**Date:** January 2026  
**Purpose:** Complete functional specification for recreating the Restaurant AI Platform

---

## Executive Summary

The Restaurant AI Platform is a **multi-tenant SaaS platform** that enables restaurants to manage their operations with AI-powered phone ordering, menu management, table reservations, order processing, and payment handling. The platform provides restaurants with an AI assistant that answers phone calls and text messages, takes orders, makes reservations, and handles customer inquiries automatically.

### Key Differentiators

1. **AI Phone Assistant**: Automated phone and SMS answering using natural language AI
2. **Multi-Tenant Architecture**: Single platform serving multiple independent restaurants
3. **Complete Order Management**: From voice/text ordering through delivery completion
4. **Automatic Commission Handling**: Platform earns revenue through commission on orders
5. **Real-Time Menu Management**: Dynamic availability updates without menu edits

---

## Business Model

### Revenue Streams

1. **Platform Commission**: Percentage of each order (default 10%, configurable per restaurant)
   - Calculated from order total (invisible to customers)
   - Applied automatically during payment processing
   - Tracked per restaurant for reporting

2. **Subscription Tiers**: Monthly recurring revenue (MRR)
   - **Free**: $0/month - 30-day trial period
   - **Starter**: $49/month - Basic features
   - **Professional**: $99/month - Full features
   - **Enterprise**: $299/month - Premium features

### Commission Flow

```
Customer pays: $50.00 (menu prices only)
    ↓
Platform commission (10%): $5.00
    ↓
Restaurant receives: $45.00 (automatically)
```

**Important**: Customers only see and pay menu prices. Commission is invisible to customers and handled between platform and restaurant.

### Customer Experience

- Customers call restaurant's phone number → AI answers
- Customers text restaurant's phone number → AI responds
- Customers interact naturally: "I want a pizza", "Table for 4 tonight"
- AI understands menu, takes orders, makes reservations
- Orders appear in restaurant dashboard immediately

---

## User Roles and Capabilities

### 1. Platform Administrator

**Purpose**: Manage the entire platform and all restaurants

**Capabilities**:
- View all restaurants in the system
- Create, suspend, and activate restaurant accounts
- Set subscription tiers and commission rates per restaurant
- View platform-wide analytics (total revenue, commission, growth)
- Monitor restaurant performance and activity
- Generate revenue reports (daily, weekly, monthly)
- Manage subscription status (trial, active, past_due, cancelled, suspended)

**Dashboard Features**:
- Total restaurants count
- Total revenue across all restaurants
- Total platform commission earned
- Growth metrics (new restaurants, orders, revenue)
- Restaurant list with status indicators
- Revenue breakdown by restaurant
- Commission tracking per restaurant

### 2. Restaurant Owner

**Purpose**: Manage individual restaurant operations

**Capabilities**:
- Create and manage restaurant account
- Build and manage menus (items, categories, modifiers)
- Toggle menu item availability in real-time
- Configure tables for reservations
- View and manage orders (takeout, delivery, dine-in)
- Track reservations and table assignments
- Monitor revenue and earnings
- Configure restaurant settings (hours, contact info, phone number)
- View analytics (orders, revenue, popular items)

**Dashboard Features**:
- Order management (pending, preparing, ready, delivered)
- Reservation calendar
- Menu editor with availability toggles
- Table management
- Revenue analytics
- Order history
- Settings configuration

### 3. Customer

**Purpose**: Place orders and make reservations via phone/SMS

**Interaction Methods**:
- **Voice Calls**: Call restaurant phone number, speak to AI
- **SMS/Text**: Text restaurant phone number, AI responds via text

**Capabilities**:
- Ask menu questions ("What vegetarian options do you have?")
- Check prices ("How much is the pizza?")
- Place takeout orders
- Place delivery orders (provide address)
- Make table reservations
- Check operating hours
- Receive order confirmations via SMS

**Limitations**: Customers do NOT have web dashboard access. All interaction is through phone/SMS.

---

## Core Functional Areas

### 1. Restaurant Onboarding

**Purpose**: Allow new restaurants to sign up and configure their account

**Flow**:
1. Restaurant owner provides basic information:
   - Business name
   - Owner name, email, phone
2. System creates account with:
   - Default subscription: FREE (30-day trial)
   - Commission rate: 10% (configurable)
   - Trial period: 30 days from signup
   - Account status: Active
3. Restaurant completes onboarding:
   - Add menu items
   - Configure tables (optional)
   - Set operating hours
   - Connect payment account (optional)
   - Assign phone number for AI (optional)

**Functional Requirements**:
- Support multiple locations per restaurant account (future)
- Support multiple menus per restaurant (e.g., Lunch, Dinner)
- Track onboarding completion status
- Allow restaurants to return and complete setup later

### 2. Menu Management

**Purpose**: Enable restaurants to create and manage their menu items

**Menu Structure**:
- **Menu**: Top-level container (restaurant can have multiple menus)
  - Example: "Lunch Menu", "Dinner Menu", "Brunch Menu"
- **Category**: Grouping within a menu
  - Example: "Appetizers", "Main Courses", "Desserts", "Beverages"
- **Item**: Individual menu item
  - Name, description, price
  - Dietary tags (vegetarian, vegan, gluten-free, etc.)
  - Availability status (available/unavailable)
  - Preparation time
  - Optional image URL
- **Modifier**: Customization options for items
  - Example: "Extra cheese", "No onions", "Spicy level"
  - Price adjustments (positive or negative)

**Functional Requirements**:
- **Real-Time Availability Toggle**: Mark items available/unavailable without editing menu
  - Use case: Out of ingredients, time-based availability (breakfast items only in morning)
  - Toggle affects AI responses immediately
  - Unavailable items are not suggested or offered
- **Menu Parsing**: Support importing menus via text or image (AI-powered)
- **Dietary Tags**: Support filtering by dietary restrictions
- **Price Management**: All prices stored in cents (integer) to avoid floating-point errors
- **Menu Display Order**: Control order of categories and items

### 3. Order Management

**Purpose**: Handle orders from creation to completion

**Order Types**:
- **Takeout**: Customer picks up at restaurant
- **Delivery**: Delivered to customer address
- **Dine-In**: Eaten at restaurant (no delivery)

**Order Lifecycle**:
1. **Created**: Order placed by customer (via phone/SMS)
2. **Confirmed**: Restaurant acknowledges order
3. **Preparing**: Kitchen is preparing order
4. **Ready**: Order is ready for pickup/delivery
5. **Out for Delivery**: Order assigned to driver, in transit (delivery only)
6. **Delivered**: Order completed and delivered (delivery only)
7. **Cancelled**: Order cancelled (any stage)

**Order Components**:
- Customer information (name, phone, optional email)
- Order items (menu items with quantities and modifiers)
- Order type (takeout/delivery/dine-in)
- Delivery address (if delivery order)
- Total price (calculated from items + modifiers)
- Special instructions
- Status and timestamps

**Functional Requirements**:
- Orders appear in restaurant dashboard immediately after creation
- Support order modification before confirmation
- Track order status changes with timestamps
- Calculate totals automatically including modifiers
- Support special instructions per item
- Kitchen display view (simplified order list for chefs)
- SMS notifications to customers on status updates (optional)

### 4. Table Reservations

**Purpose**: Allow customers to book tables via AI

**Reservation System**:
- **Tables**: Defined by restaurant with capacity (seats)
  - Table number (identifier)
  - Capacity (maximum party size)
  - Optional location description
  - Active/inactive status
- **Reservations**: Bookings for specific tables at specific times
  - Date and time
  - Party size
  - Customer information
  - Status (pending, confirmed, seated, completed, cancelled, no_show)
  - Duration: 90 minutes (default, configurable)

**Availability Logic**:
- Tables must have capacity >= party size
- Tables must be available for the full 90-minute slot
- No overlapping reservations on same table
- System suggests alternative times if requested time unavailable
- Automatic table assignment (smallest suitable table)

**Functional Requirements**:
- **Conflict Prevention**: Prevent double-booking automatically
- **Availability Checking**: Real-time availability queries
- **Alternative Time Suggestions**: If requested time unavailable, suggest nearby times
- **Table Assignment**: Automatic assignment based on party size
- **Manual Override**: Restaurants can manually assign tables if needed
- **Status Tracking**: Track reservation status through lifecycle
- **No-Show Tracking**: Mark reservations as no-show

### 5. Voice AI Assistant (Phone Calls)

**Purpose**: Automated phone answering and order taking

**How It Works**:
1. Customer calls restaurant's phone number
2. System identifies restaurant by phone number
3. AI greets customer with restaurant name
4. Customer speaks naturally
5. Speech-to-text converts speech to text
6. AI processes request with restaurant's menu context
7. AI responds via text-to-speech
8. Conversation continues until order/booking complete
9. System creates order or reservation in database

**AI Capabilities**:
- **Menu Questions**: Answer questions about menu items, prices, dietary options
- **Order Taking**: Process complex orders with modifiers ("2 pizzas, extra cheese, no onions")
- **Reservations**: Check availability and book tables
- **Hours**: Provide operating hours
- **Natural Language**: Understand variations like "tomorrow", "7pm", "tonight"

**Functional Requirements**:
- Multi-tenant support (each restaurant has own phone number)
- Menu-aware responses (only mentions available items)
- Context preservation during conversation
- Order/reservation confirmation before finalizing
- SMS confirmation sent to customer after order/booking

**Technical Note**: Implementation requires:
- Voice service provider (Twilio, etc.) for phone calls
- Speech-to-text service (Twilio Whisper, etc.)
- Text-to-speech service (Twilio, etc.)
- AI/LLM service (Google Gemini, OpenAI, etc.) for conversation

### 6. SMS/Text Message Support

**Purpose**: Allow customers to interact via text messages

**How It Works**:
1. Customer texts restaurant's phone number
2. System identifies restaurant by phone number
3. AI processes text message with menu context
4. AI responds via text message
5. Conversation continues asynchronously (no time limit)
6. System creates order or reservation when confirmed

**Functional Requirements**:
- Same AI capabilities as voice (menu questions, orders, reservations)
- Asynchronous conversations (can span hours/days)
- Conversation state management (remember context)
- Multi-tenant support (same as voice)

**Advantages Over Voice**:
- More accurate (no speech recognition errors)
- Written record of conversation
- Customer can multitask
- Lower cost per interaction

### 7. Payment Processing

**Purpose**: Handle payments for orders with commission splitting

**Payment Flow**:
1. Customer confirms order
2. Payment information collected (via Stripe Connect)
3. Payment processed for full order amount
4. Platform commission automatically deducted
5. Remaining amount transferred to restaurant
6. Transaction recorded in system

**Functional Requirements**:
- Support credit/debit card payments
- Automatic commission calculation
- Automatic payment splitting (platform + restaurant)
- Payment status tracking
- Refund support (if needed)
- Payment history per restaurant

**Technical Note**: Requires Stripe Connect integration for marketplace payments.

### 8. Commission Management

**Purpose**: Track and manage platform commission per restaurant

**Commission Settings**:
- **Rate**: Percentage (0-100%), default 10%
- **Enabled/Disabled**: Toggle commission on/off per restaurant
- **Calculation**: Based on order total (menu prices only)

**Functional Requirements**:
- Configurable per restaurant
- Commission calculated automatically on each order
- Commission tracking (total owed per restaurant)
- Commission reporting in admin dashboard
- Commission invisible to customers

**Examples**:
- Restaurant A: 5% commission
- Restaurant B: 10% commission (default)
- Restaurant C: 0% commission (disabled for special partnership)

### 9. Analytics and Reporting

**Purpose**: Provide insights to restaurants and platform admin

**Restaurant Analytics**:
- Order count and revenue (daily, weekly, monthly)
- Popular menu items
- Peak ordering times
- Average order value
- Reservation statistics
- Commission owed

**Platform Admin Analytics**:
- Total restaurants
- Total revenue across all restaurants
- Total platform commission
- Growth metrics (new restaurants, orders, revenue)
- Restaurant performance comparison
- Subscription revenue

**Functional Requirements**:
- Real-time or near-real-time data updates
- Date range filtering
- Export capabilities (future)
- Visual charts and graphs

---

## Data Models (Conceptual)

### RestaurantAccount
- Business identification (name, owner info)
- Subscription information (tier, status, trial dates)
- Commission settings (rate, enabled/disabled)
- Contact information (phone, email, address)
- Operating hours (opening/closing time, days of week)
- Phone number for AI (Twilio number)
- Payment account (Stripe Connect ID)

### Restaurant (Location)
- Physical location details (address)
- Can have multiple locations per account (future)

### Menu
- Menu name and description
- Active status
- Time-based availability (days, hours)
- Belongs to one RestaurantAccount

### MenuCategory
- Category name and description
- Display order
- Belongs to one Menu

### MenuItem
- Name, description, price
- Dietary tags (array)
- Availability status
- Preparation time
- Display order
- Image URL (optional)
- Belongs to one MenuCategory

### MenuModifier
- Modifier name
- Price adjustment
- Modifier group (e.g., "Size", "Toppings")
- Belongs to one MenuItem

### Table
- Table number (identifier)
- Capacity (maximum seats)
- Location description (optional)
- Active status
- Belongs to one Restaurant

### Order
- Order type (takeout/delivery/dine-in)
- Customer information
- Order items (with quantities and modifiers)
- Total price
- Status and timestamps
- Delivery address (if applicable)
- Belongs to one RestaurantAccount

### Booking (Reservation)
- Date and time
- Party size
- Duration (default 90 minutes)
- Customer information
- Assigned table
- Status and timestamps
- Special requests
- Belongs to one Restaurant and one Table

### Customer
- Phone number (primary identifier)
- Name, email (optional)
- Booking/order history
- Notes (allergies, preferences)

---

## Integration Requirements

### Required Third-Party Services

1. **Voice/SMS Service** (Twilio recommended)
   - Phone number management
   - Voice call handling
   - SMS message handling
   - Speech-to-text
   - Text-to-speech

2. **AI/LLM Service** (Google Gemini, OpenAI, or similar)
   - Natural language understanding
   - Conversation handling
   - Menu-aware responses

3. **Payment Processing** (Stripe Connect required for commission splitting)
   - Payment collection
   - Automatic payment splitting
   - Payout management

4. **Optional: Google Maps API**
   - Operating hours import from Google Maps
   - Address validation

---

## User Workflows

### Workflow 1: New Restaurant Signup

1. Restaurant owner visits platform
2. Fills out signup form (business name, owner info)
3. System creates account (FREE tier, 30-day trial)
4. Restaurant owner receives login credentials
5. Restaurant logs in and completes onboarding:
   - Creates menu with categories
   - Adds menu items
   - Configures tables (optional)
   - Sets operating hours
   - Assigns phone number for AI (optional)
6. Restaurant starts receiving orders/reservations

### Workflow 2: Customer Places Order via Phone

1. Customer calls restaurant phone number
2. AI answers: "Thanks for calling [Restaurant Name]. How may I help you?"
3. Customer: "I want to order a pizza"
4. AI: "Great! We have Margherita ($15), Pepperoni ($17), Veggie ($16). Which would you like?"
5. Customer: "Pepperoni, large"
6. AI: "Large pepperoni pizza, $17. Delivery or pickup?"
7. Customer: "Delivery to 123 Main St"
8. AI: "Perfect! Total is $17. Confirm order?"
9. Customer: "Yes"
10. AI: "Order confirmed! We'll have it ready in 30 minutes. Confirmation #1234"
11. System creates order in database
12. Customer receives SMS confirmation
13. Order appears in restaurant dashboard

### Workflow 3: Customer Makes Reservation via SMS

1. Customer texts restaurant: "Table for 4 tonight at 7pm"
2. AI: "Let me check availability... Yes! I have a table for 4 at 7pm. What name?"
3. Customer: "Sarah Johnson"
4. AI: "Perfect! Table reserved for 4 guests tonight at 7pm. Name: Sarah Johnson. Confirmation #5678"
5. System creates booking in database
6. Customer receives SMS confirmation
7. Reservation appears in restaurant dashboard

### Workflow 4: Restaurant Manages Order

1. Order appears in restaurant dashboard (status: Pending)
2. Restaurant confirms order (status: Confirmed)
3. Kitchen starts preparing (status: Preparing)
4. Order ready (status: Ready)
5. If delivery: Assign driver (status: Out for Delivery)
6. Order delivered (status: Delivered)
7. Payment processed automatically (commission deducted, restaurant receives payout)

### Workflow 5: Restaurant Updates Menu Availability

1. Restaurant notices out of salmon
2. Opens dashboard → Menu section
3. Finds "Grilled Salmon" item
4. Toggles "Available" to "Unavailable"
5. System immediately updates
6. Next customer asks: "Do you have salmon?"
7. AI responds: "Sorry, we're currently out of salmon. Would you like to try [alternative]?"

---

## Platform Administration Workflows

### Workflow 6: Admin Manages Restaurant

1. Admin logs into admin dashboard
2. Views all restaurants list
3. Clicks on specific restaurant
4. Views restaurant details (orders, revenue, commission)
5. Updates subscription tier (e.g., FREE → Professional)
6. Adjusts commission rate (e.g., 10% → 5%)
7. Views revenue breakdown

### Workflow 7: Commission Calculation and Tracking

1. Restaurant receives order: $50
2. System calculates commission: $50 × 10% = $5
3. Commission tracked in RestaurantAccount.commission_owed
4. Payment processed: Customer pays $50
5. Platform receives: $5 (automatically via Stripe Connect)
6. Restaurant receives: $45 (automatically via Stripe Connect)
7. Admin views commission report: Total commission earned per restaurant

---

## Success Criteria

A successful implementation must:

1. ✅ Support multiple restaurants independently (multi-tenant)
2. ✅ Enable restaurants to create and manage menus
3. ✅ Handle AI phone and SMS conversations
4. ✅ Process orders from creation to completion
5. ✅ Manage table reservations with conflict prevention
6. ✅ Process payments with automatic commission splitting
7. ✅ Provide dashboards for restaurants and admin
8. ✅ Track commission automatically
9. ✅ Support real-time menu availability updates
10. ✅ Maintain conversation context during AI interactions

---

## Technical Constraints (Non-Functional)

### Performance Requirements
- Order creation: < 2 seconds
- AI response time: < 5 seconds (depends on LLM provider)
- Dashboard page load: < 2 seconds
- Real-time updates: Near-instantaneous

### Scalability Requirements
- Support 100+ restaurants
- Handle 1000+ orders per day
- Concurrent AI conversations: 50+
- Database queries optimized for multi-tenant access

### Availability Requirements
- 99% uptime (except planned maintenance)
- Graceful degradation if AI service unavailable
- Data backup and recovery

### Security Requirements
- Secure payment processing (PCI compliance)
- API authentication (JWT tokens)
- Database isolation between restaurants
- HTTPS for all communications

---

## Out of Scope (Future Enhancements)

These features are NOT in the current specification but may be added later:

- Customer-facing web ordering interface
- Mobile apps (iOS/Android)
- Inventory management
- Staff scheduling
- Loyalty programs
- Marketing campaigns
- Advanced analytics (predictive, ML-based)
- Multi-language support
- QR code ordering
- In-store kiosk ordering
- Delivery driver tracking app
- Advanced reporting with exports

---

## Document Purpose

This functional specification provides a complete description of **what** the system does, **who** uses it, and **how** it works from a functional perspective. It does NOT specify technical implementation details (which database, which framework, which deployment method).

Another development team can use this specification to:
- Understand all features and requirements
- Design their own technical architecture
- Choose their own technology stack
- Implement the functionality described herein

The specification focuses on **functionality** and **business logic**, leaving technical decisions to the implementation team.

---

**End of Functional Specification**
