# Architecture Plan

**Feature:** 
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

**Date:** 2026-01-10 21:16:41
**Complexity:** medium

## Summary

Build a complete React admin dashboard for restaurant management using Vite, React Router v6, and TailwindCSS. The frontend will integrate with the existing FastAPI backend API endpoints for restaurants, tables, bookings, and customers. The dashboard includes 5 main pages (Dashboard, Restaurants, Tables, Bookings, Customers), reusable UI components, and a custom API hook for data fetching with proper loading states and error handling.

## Database Changes

No database changes required.

## Backend Files

No backend files.

## Frontend Files

- **frontend/package.json** (create): NPM package configuration with React, Vite, TailwindCSS, React Router, and Axios dependencies
- **frontend/vite.config.js** (create): Vite build tool configuration with React plugin and proxy settings for API
- **frontend/tailwind.config.js** (create): TailwindCSS configuration with custom color scheme and content paths
- **frontend/postcss.config.js** (create): PostCSS configuration for TailwindCSS processing
- **frontend/index.html** (create): HTML entry point for the Vite React application
- **frontend/src/main.jsx** (create): React application entry point with BrowserRouter setup
- **frontend/src/App.jsx** (create): Main App component with React Router routes configuration
- **frontend/src/index.css** (create): Global CSS with TailwindCSS directives and custom styles
- **frontend/src/api/client.js** (create): Axios API client configured for backend communication with interceptors
- **frontend/src/components/Layout.jsx** (create): Main layout wrapper with sidebar and header
- **frontend/src/components/Sidebar.jsx** (create): Navigation sidebar with menu items and active state
- **frontend/src/components/Header.jsx** (create): Top header bar with title and user actions
- **frontend/src/components/shared/Button.jsx** (create): Reusable button with primary, secondary, danger variants and loading state
- **frontend/src/components/shared/Card.jsx** (create): Container card component with optional header and footer
- **frontend/src/components/shared/Table.jsx** (create): Data table component with sortable columns and actions
- **frontend/src/components/shared/Modal.jsx** (create): Reusable modal dialog with header, body, and footer sections
- **frontend/src/components/shared/Badge.jsx** (create): Status badge component with color variants for different states
- **frontend/src/components/shared/Input.jsx** (create): Form input component with label, validation, and error message display
- **frontend/src/components/shared/Select.jsx** (create): Dropdown select component with label and validation
- **frontend/src/components/shared/Toast.jsx** (create): Toast notification component for success/error messages
- **frontend/src/components/shared/Spinner.jsx** (create): Loading spinner component for async operations
- **frontend/src/components/shared/ConfirmDialog.jsx** (create): Confirmation dialog for destructive actions
- **frontend/src/components/shared/index.js** (create): Barrel export for all shared components
- **frontend/src/pages/Dashboard.jsx** (create): Dashboard page with stat cards, recent bookings, and overview metrics
- **frontend/src/pages/Restaurants.jsx** (create): Restaurant management page with CRUD operations and form modal
- **frontend/src/pages/Tables.jsx** (create): Table management page with restaurant selector and table CRUD
- **frontend/src/pages/Bookings.jsx** (create): Booking management page with filters, list view, and booking creation
- **frontend/src/pages/Customers.jsx** (create): Customer list page with search and booking history
- **frontend/src/hooks/useApi.js** (create): Custom hook for API calls with loading, error, and data state management
- **frontend/src/hooks/useToast.js** (create): Custom hook for toast notification management
- **frontend/src/context/ToastContext.jsx** (create): React context for global toast notifications
- **frontend/src/utils/helpers.js** (create): Utility functions for date formatting, validation, and data transformation
- **frontend/src/utils/constants.js** (create): Application constants including API endpoints and status values

## API Endpoints

- **GET /api/**: List all restaurants
- **POST /api/**: Create a new restaurant
- **PUT /api/{id}**: Update an existing restaurant
- **DELETE /api/{id}**: Delete a restaurant
- **GET /api/{restaurant_id}/tables**: List tables for a restaurant
- **POST /api/{restaurant_id}/tables**: Create a new table
- **GET /api/bookings/**: List all bookings with optional filters
- **POST /api/bookings/**: Create a new booking
- **DELETE /api/bookings/{id}**: Cancel a booking
- **GET /api/customers/**: List all customers
- **POST /api/availability/check**: Check table availability

## Dependencies

- react@^18.2.0
- react-dom@^18.2.0
- react-router-dom@^6.20.0
- axios@^1.6.0
- @vitejs/plugin-react@^4.2.0
- vite@^5.0.0
- tailwindcss@^3.4.0
- autoprefixer@^10.4.16
- postcss@^8.4.32
- @heroicons/react@^2.1.0
- date-fns@^3.0.0

## Implementation Steps

1. Initialize Vite project with React template and configure build settings
2. Install and configure TailwindCSS with custom color scheme
3. Set up React Router with route definitions for all pages
4. Create API client with Axios including base URL and interceptors
5. Build shared UI components (Button, Card, Table, Modal, Badge, Input, Select, Toast, Spinner)
6. Create Layout component with Sidebar and Header navigation
7. Implement useApi custom hook for data fetching with loading/error states
8. Implement Toast context and useToast hook for notifications
9. Build Dashboard page with stat cards and recent bookings table
10. Build Restaurants page with list view, add/edit modal, and delete confirmation
11. Build Tables page with restaurant selector and table management
12. Build Bookings page with filters, booking list, and create booking modal
13. Build Customers page with search and customer list
14. Add form validation to all forms
15. Implement error boundaries and loading states throughout
16. Test all CRUD operations against backend API
17. Polish UI/UX with responsive design adjustments

## Risks

- CORS configuration must be properly set on backend for frontend development server
- API endpoint response formats must match expected frontend data structures
- Date/time handling between frontend and backend timezone considerations
- Form validation must align with backend validation rules
- Error handling for network failures and API errors
- State management complexity for nested data (restaurants -> tables -> bookings)
