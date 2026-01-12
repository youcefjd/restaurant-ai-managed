#!/usr/bin/env python3
"""
Phase 2: Admin Dashboard Frontend
Build a React admin dashboard for restaurant owners to manage their reservation system.
"""

import os
import sys

# Add autonomous_engineer to path
sys.path.insert(0, '/tmp/autonomous_engineer')

# Set environment variable to disable emergency stop signals for this script
os.environ["DISABLE_EMERGENCY_STOP_SIGNALS"] = "1"

from autonomous_engineer.orchestrator_agent import OrchestratorAgent
from llm_provider import create_llm_provider

# Phase 2 Requirements
PHASE_2_REQUIREMENTS = """
# Phase 2: Restaurant Admin Dashboard

Build a modern React admin dashboard for restaurant owners using Vite, React Router, and TailwindCSS.

## Project Structure
```
frontend/
├── package.json
├── vite.config.js
├── tailwind.config.js
├── index.html
├── src/
│   ├── main.jsx
│   ├── App.jsx
│   ├── api/
│   │   └── client.js          # API client for backend
│   ├── components/
│   │   ├── Layout.jsx         # Main layout with sidebar
│   │   ├── Sidebar.jsx        # Navigation sidebar
│   │   ├── Header.jsx         # Top header bar
│   │   └── shared/            # Reusable components
│   │       ├── Button.jsx
│   │       ├── Card.jsx
│   │       ├── Table.jsx
│   │       ├── Modal.jsx
│   │       ├── Badge.jsx
│   │       └── Input.jsx
│   ├── pages/
│   │   ├── Dashboard.jsx      # Dashboard with stats
│   │   ├── Restaurants.jsx    # Restaurant CRUD
│   │   ├── Tables.jsx         # Table management
│   │   ├── Bookings.jsx       # Booking management
│   │   └── Customers.jsx      # Customer list
│   ├── hooks/
│   │   └── useApi.js          # Custom hook for API calls
│   └── utils/
│       └── helpers.js         # Utility functions
```

## Technical Requirements

### 1. Setup & Configuration
- Use Vite as the build tool
- React 18+ with hooks
- React Router v6 for routing
- TailwindCSS for styling
- Axios for API requests

### 2. API Integration
Backend API is running at http://localhost:8000

Endpoints to integrate:
- GET /api/ - List restaurants
- POST /api/ - Create restaurant
- PUT /api/{id} - Update restaurant
- DELETE /api/{id} - Delete restaurant
- GET /api/{restaurant_id}/tables - List tables
- POST /api/{restaurant_id}/tables - Create table
- GET /api/bookings/ - List bookings
- POST /api/bookings/ - Create booking
- DELETE /api/bookings/{id} - Cancel booking
- GET /api/customers/ - List customers
- POST /api/availability/check - Check availability

### 3. Pages & Features

#### Dashboard Page
- Show 4 stat cards: Total Restaurants, Total Bookings, Total Customers, Active Tables
- Recent bookings table (last 10)
- Today's bookings count
- Weekly booking trend chart (bonus)

#### Restaurants Page
- Table view of all restaurants
- "Add Restaurant" button with modal form
- Edit/Delete actions for each restaurant
- Form fields: name, address, phone, email, opening_time, closing_time, booking_duration_minutes, max_party_size
- Client-side validation

#### Tables Page
- Restaurant selector dropdown
- Table list for selected restaurant
- Add/Edit/Delete table functionality
- Fields: table_number, capacity, location, is_active
- Visual table layout view (bonus)

#### Bookings Page
- Filterable booking list (by date, status, restaurant)
- Create booking button with modal
- Cancel booking action
- Status badges (pending, confirmed, cancelled, completed, no_show)
- Calendar view (bonus)

#### Customers Page
- Customer list table
- Show: name, phone, email, total_bookings, no_shows
- Search by phone number

### 4. UI/UX Requirements
- Clean, modern design
- Responsive layout (desktop-first)
- Loading states for API calls
- Error handling with toast notifications
- Form validation
- Confirmation dialogs for destructive actions
- Color scheme: Blue primary (#2563eb), success green, warning yellow, danger red

### 5. Component Requirements

All components should be modular and reusable.

**Button.jsx** - Primary, secondary, danger variants with loading state
**Card.jsx** - Container with optional header and footer
**Table.jsx** - Data table with sortable columns
**Modal.jsx** - Reusable modal with header, body, footer
**Badge.jsx** - Status badges with color variants
**Input.jsx** - Form inputs with label and error message

### 6. Dependencies (package.json)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32"
  }
}
```

### 7. Implementation Notes
- Use React hooks (useState, useEffect, useContext)
- Create custom useApi hook for data fetching
- Handle CORS properly (backend already configured)
- Use TailwindCSS utility classes for styling
- Implement proper error boundaries
- Add loading spinners for async operations

## Success Criteria
1. All pages load without errors
2. Can create, read, update, delete restaurants
3. Can view and manage bookings
4. Clean, professional UI
5. Proper error handling
6. Responsive design

Build this as a production-ready admin dashboard that restaurant owners would actually want to use.
"""

def main():
    print("=" * 80)
    print("🚀 PHASE 2: ADMIN DASHBOARD FRONTEND")
    print("=" * 80)
    print()
    print("Building React admin dashboard with Vite and TailwindCSS...")
    print()

    # Initialize LLM provider
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    llm_provider = create_llm_provider(
        "anthropic",
        model="claude-opus-4-5-20251101",
        api_key=api_key
    )

    # Initialize orchestrator
    repo_path = os.path.abspath(".")
    orchestrator = OrchestratorAgent(
        repo_path=repo_path,
        github_token=None,
        llm_provider=llm_provider
    )

    # Run Phase 2
    print("📋 Requirements:")
    print(PHASE_2_REQUIREMENTS[:500] + "...\n")

    result = orchestrator.execute(PHASE_2_REQUIREMENTS)

    print()
    print("=" * 80)
    if result.get("success"):
        print("✅ PHASE 2 COMPLETE!")
        print("=" * 80)
        print()
        print("Next steps:")
        print("1. cd frontend")
        print("2. npm install")
        print("3. npm run dev")
        print("4. Open http://localhost:5173")
    else:
        print("❌ PHASE 2 FAILED")
        print("=" * 80)
        print(f"Error: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()
