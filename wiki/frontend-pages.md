# Frontend Pages

Overview of the main pages in the React application.

## Restaurant Owner Pages

### Dashboard (`/restaurant/dashboard`)

Main overview for restaurant owners.

**Features:**
- Quick stats: Pending orders, completed today, revenue, menu items
- Pending orders requiring attention
- Quick action buttons

**Data:**
- Orders API
- Analytics summary

### Orders (`/restaurant/orders`)

Order management interface.

**Features:**
- Order list with status filtering
- Status progression: Pending → Preparing → Ready → Completed
- Payment status tracking (Unpaid/Paid/Refunded)
- Order detail modal
- Quick status updates

**Filters:**
- All, Pending, Preparing, Ready, Completed, Cancelled

**Data:**
- `/api/restaurant/orders/*`

### Menu (`/restaurant/menu`)

Menu content management.

**Features:**
- Hierarchical view: Menus → Categories → Items
- Create/edit/delete menus
- Create/edit/delete categories
- Create/edit/delete items
- Toggle item availability
- Dietary tags display
- Price management (in cents)
- Import menu from file

**Data:**
- `/api/onboarding/accounts/{id}/menu-full`
- `/api/onboarding/menus/*`
- `/api/onboarding/items/*`

### Analytics (`/restaurant/analytics`)

Business analytics and insights.

**Features:**
- Revenue over time (area chart)
- Order count trends
- Peak hours heatmap
- Popular items ranking
- Time period selector (7/30/90 days)

**Data:**
- `/api/restaurant/orders/analytics/*`

### Transcripts (`/restaurant/transcripts`)

Call and SMS conversation history.

**Features:**
- Transcript list with search
- Filter by type (Voice/SMS)
- Message thread view
- Outcome tracking
- Phone number display

**Data:**
- `/api/onboarding/accounts/{id}/transcripts`

### Reservations (`/restaurant/reservations`)

Table booking management.

**Features:**
- Upcoming reservations list
- Booking status updates
- Party size and table assignment
- Special requests

**Data:**
- `/api/bookings/*`

### Settings (`/restaurant/settings`)

Restaurant configuration.

**Pages:**
- Index - Settings overview
- Phone Settings - Twilio phone number
- Operating Hours - Open/close times, days
- Google Maps Import - Import hours from Google Business

**Data:**
- `/api/onboarding/accounts/{id}/*`

## Platform Admin Pages

### Admin Dashboard (`/admin/dashboard`)

Platform-wide overview.

**Features:**
- Total restaurants count
- Total orders across platform
- Platform revenue
- Recent activity

**Data:**
- `/api/admin/stats`

### Restaurants (`/admin/restaurants`)

Restaurant management.

**Features:**
- All restaurants list
- Status indicators (Active, Trial, Suspended)
- Commission rate management
- Suspend/activate actions
- Subscription tier display

**Data:**
- `/api/admin/restaurants`
- `/api/admin/restaurants/{id}/*`

### Revenue (`/admin/revenue`)

Platform revenue tracking.

**Features:**
- Total revenue over time
- Commission breakdown by restaurant
- Payout status
- Revenue trends

**Data:**
- `/api/admin/revenue`

### Admin Analytics (`/admin/analytics`)

Platform-wide metrics.

**Features:**
- Growth metrics
- Daily active restaurants
- Total orders processed
- Revenue trends

**Data:**
- `/api/admin/analytics/*`

## Auth Pages

### Login (`/login`)

Restaurant owner authentication.

### Admin Login (`/admin/login`)

Platform admin authentication.

### Signup (`/signup`)

New restaurant registration.

## UI Patterns

### Loading States

All pages show `LoadingTRex` component while data loads.

### Error Handling

TanStack Query handles errors with retry logic.

### Real-time Updates

Orders pages auto-refresh every 30-60 seconds.

### Responsive Design

All pages work on tablet and desktop. Mobile support limited.

---

**Related:**
- [Frontend Architecture](./frontend.md)
- [API Reference](./api-reference.md)
