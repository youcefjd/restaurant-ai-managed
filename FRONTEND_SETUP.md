# Restaurant AI Platform - Frontend Setup

## Overview

You now have a complete multi-tenant restaurant platform with:
- **Restaurant Dashboard** - For restaurant owners to manage orders, menu, and analytics
- **Platform Admin Dashboard** - For you to manage all restaurants, revenue, and growth
- **Landing Page** - Marketing page for restaurant signups

## Architecture

```
Frontend (React + TypeScript)
├── Restaurant Portal (/restaurant/*)
│   ├── Dashboard - Today's orders, revenue stats
│   ├── Orders - Real-time order management
│   ├── Menu - Menu item management
│   └── Analytics - Revenue & order charts
│
└── Platform Admin (/admin/*)
    ├── Dashboard - Platform-wide stats
    ├── Restaurants - Manage all restaurant accounts
    ├── Revenue - Commission tracking
    └── Analytics - Growth metrics
```

## Running the Platform

### 1. Start Backend (FastAPI)
```bash
cd /Users/youcef/restaurant-assistant
source venv/bin/activate
export ANTHROPIC_API_KEY='your-key-here'
export TWILIO_ACCOUNT_SID='your-sid-here'
export TWILIO_AUTH_TOKEN='your-token-here'
export STRIPE_API_KEY='your-stripe-key-here'
uvicorn main:app --reload --port 8000
```

### 2. Start Frontend (Vite)
```bash
cd /Users/youcef/restaurant-assistant/frontend-new
npm run dev
```

The frontend will run on `http://localhost:5173` and proxy API calls to `http://localhost:8000`

## Available Routes

### Public
- `/` - Landing page with features, pricing, and signup

### Restaurant Portal
- `/restaurant/dashboard` - Overview with today's stats
- `/restaurant/orders` - Order management with status updates
- `/restaurant/menu` - Menu management (items, modifiers, dietary tags)
- `/restaurant/analytics` - Revenue and order charts

### Platform Admin
- `/admin/dashboard` - Platform stats and recent signups
- `/admin/restaurants` - List all restaurants with revenue data
- `/admin/revenue` - Commission tracking and revenue breakdown
- `/admin/analytics` - Growth trends and metrics

## Features Implemented

### Restaurant Features
✅ Real-time order management
✅ Menu-aware AI conversations
✅ Menu management (items, categories, modifiers, dietary tags)
✅ Analytics dashboard with charts
✅ Stripe Connect integration for payments

### Platform Admin Features
✅ Multi-tenant restaurant management
✅ Revenue tracking with commission splits
✅ Suspend/activate restaurants
✅ Platform-wide analytics
✅ Growth metrics and trends

### Technical Features
✅ React Query for data fetching
✅ TailwindCSS for styling
✅ Recharts for visualizations
✅ TypeScript for type safety
✅ Vite for fast development

## Next Steps

1. **Add Authentication** - Implement user login/signup with sessions
2. **Real-time Updates** - Add WebSocket for live order updates
3. **Notifications** - Push notifications for new orders
4. **Mobile Responsive** - Optimize for mobile devices
5. **Testing** - Add unit and integration tests
6. **Production Build** - Deploy to Vercel/Netlify

## Development Commands

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type check
npm run type-check
```

## API Integration

The frontend uses Axios with a base URL of `/api` which is proxied to `http://localhost:8000/api` in development (configured in `vite.config.ts`).

All API calls are organized in `src/services/api.ts`:
- `adminAPI` - Platform admin endpoints
- `restaurantAPI` - Restaurant management endpoints
- `stripeAPI` - Stripe Connect endpoints
- `deliveryAPI` - Delivery management endpoints

## Environment Variables

Create a `.env` file in `frontend-new/`:

```env
VITE_API_URL=http://localhost:8000
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool & dev server
- **TailwindCSS** - Utility-first CSS
- **React Router v6** - Routing
- **React Query** - Data fetching & caching
- **Recharts** - Charts & visualizations
- **Axios** - HTTP client
- **Lucide React** - Icon library

## File Structure

```
frontend-new/
├── src/
│   ├── components/
│   │   └── layouts/
│   │       ├── RestaurantLayout.tsx
│   │       └── AdminLayout.tsx
│   ├── pages/
│   │   ├── restaurant/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Orders.tsx
│   │   │   ├── Menu.tsx
│   │   │   └── Analytics.tsx
│   │   ├── admin/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Restaurants.tsx
│   │   │   ├── Revenue.tsx
│   │   │   └── Analytics.tsx
│   │   └── LandingPage.tsx
│   ├── services/
│   │   └── api.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## Platform Business Model

### Revenue Model
- Restaurants pay monthly subscription ($49-$149/month)
- Platform takes 10% commission on all orders
- Automatic payment splits via Stripe Connect

### Example Revenue
If a restaurant processes $10,000 in orders:
- Restaurant receives: $9,000 (90%)
- Platform commission: $1,000 (10%)
- Plus subscription fee: $49-$149/month

## Support

For issues or questions, check:
- `/PLATFORM_OVERVIEW.md` - Complete platform documentation
- Backend API docs: `http://localhost:8000/docs`
- Frontend build logs: `npm run build`
