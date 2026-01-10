# Architecture Plan

**Feature:** 
Build a complete Restaurant Reservation System backend API with the following requirements:

DETAILED SPECIFICATION:
# Phase 1: Core Reservation System - Detailed Specification

## Overview
Build a complete backend API for restaurant reservation management with SQLite database.

## Database Schema

### Table: restaurants
```sql
- id: INTEGER PRIMARY KEY
- name: VARCHAR(255) NOT NULL
- address: TEXT
- phone: VARCHAR(20)
- email: VARCHAR(255)
- opening_time: TIME (default: 11:00)
- closing_time: TIME (default: 22:00)
- booking_duration_minutes: INTEGER (default: 90)
- max_party_size: INTEGER (default: 8)
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

### Table: tables
```sql
- id: INTEGER PRIMARY KEY
- restaurant_id: INTEGER FOREIGN KEY -> restaurants.id
- table_number: VARCHAR(20) NOT NULL
- capacity: INTEGER NOT NULL (min: 1, max: 20)
- location: VARCHAR(100) (e.g., "window", "patio", "indoor")
- is_active: BOOLEAN (default: TRUE)
- created_at: TIMESTAMP
```

### Table: customers
```sql
- id: INTEGER PRIMARY KEY
- phone: VARCHAR(20) UNIQUE NOT NULL (primary identifier)
- name: VARCHAR(255)
- email: VARCHAR(255)
- notes: TEXT (allergies, preferences, etc.)
- total_bookings: INTEGER (default: 0)
- no_shows: INTEGER (default: 0)
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

### Table: bookings
```sql
- id: INTEGER PRIMARY KEY
- restaurant_id: INTEGER FOREIGN KEY -> restaurants.id
- table_id: INTEGER FOREIGN KEY -> tables.id (nullable initially)
- customer_id: INTEGER FOREIGN KEY -> customers.id
- booking_date: DATE NOT NULL
- booking_time: TIME NOT NULL
- party_size: INTEGER NOT NULL
- duration_minutes: INTEGER (default: 90)
- status: ENUM('pending', 'confirmed', 'seated', 'completed', 'cancelled', 'no_show')
- special_requests: TEXT
- created_at: TIMESTAMP
- updated_at: TIMESTAMP
```

## API Endpoints

### Restaurants
```
POST   /api/restaurants
  Body: {name, address, phone, email, opening_time?, closing_time?}
  Returns: Restaurant object with id

GET    /api/restaurants/{id}
  Returns: Restaurant details

PUT    /api/restaurants/{id}
  Body: {name?, address?, phone?, opening_time?, closing_time?}
  Returns: Updated restaurant

GET    /api/restaurants
  Returns: List of all restaurants
```

### Tables
```
POST   /api/tables
  Body: {restaurant_id, table_number, capacity, location?}
  Returns: Table object with id

GET    /api/restaurants/{restaurant_id}/tables
  Returns: List of tables for restaurant

PUT    /api/tables/{id}
  Body: {table_number?, capacity?, location?, is_active?}
  Returns: Updated table

DELETE /api/tables/{id}
  Returns: Success message
```

### Customers
```
POST   /api/customers
  Body: {phone, name?, email?, notes?}
  Returns: Customer object with id

GET    /api/customers/by-phone/{phone}
  Returns: Customer details or 404

PUT    /api/customers/{id}
  Body: {name?, email?, notes?}
  Returns: Updated customer
```

### Bookings
```
POST   /api/bookings
  Body: {
    restaurant_id,
    customer_phone,  # Will create customer if doesn't exist
    customer_name?,
    booking_date,    # Format: YYYY-MM-DD
    booking_time,    # Format: HH:MM
    party_size,
    special_requests?
  }
  Logic:
    1. Find or create customer by phone
    2. Check availability (no conflicts)
    3. Auto-assign suitable table (capacity >= party_size)
    4. Create booking with status='pending'
  Returns: Booking object with assigned table

GET    /api/bookings/{id}
  Returns: Booking details with restaurant, table, customer

PUT    /api/bookings/{id}
  Body: {booking_date?, booking_time?, party_size?, status?, special_requests?}
  Logic: Re-check availability if date/time/party_size changed
  Returns: Updated booking

DELETE /api/bookings/{id}
  Logic: Set status='cancelled', free up table
  Returns: Success message

GET    /api/restaurants/{restaurant_id}/bookings
  Query params: ?date=YYYY-MM-DD&status=pending
  Returns: List of bookings
```

### Availability
```
GET    /api/availability
  Query params:
    - restaurant_id (required)
    - date (required, format: YYYY-MM-DD)
    - time (required, format: HH:MM)
    - party_size (required)
    - duration_minutes? (optional, default: 90)

  Logic:
    1. Find tables with capacity >= party_size
    2. Check each table for conflicts:
       - Existing bookings that overlap with requested time slot
       - Overlap = (start_time < requested_end) AND (end_time > requested_start)
    3. Return list of available tables

  Returns: {
    available: boolean,
    available_tables: [
      {id, table_number, capacity, location}
    ],
    alternative_times: [  # If not available
      {time: "18:00", available_tables: 3},
      {time: "21:00", available_tables: 5}
    ]
  }
```

## Business Logic

### Availability Checking Algorithm
```python
def check_availability(restaurant_id, date, time, party_size, duration_minutes=90):
    # 1. Parse datetime
    requested_start = datetime.combine(date, time)
    requested_end = requested_start + timedelta(minutes=duration_minutes)

    # 2. Find suitable tables (capacity >= party_size, is_active=True)
    suitable_tables = get_tables(restaurant_id, min_capacity=party_size)

    # 3. For each table, check for conflicts
    available_tables = []
    for table in suitable_tables:
        # Get all bookings for this table on this date
        existing_bookings = get_bookings(
            table_id=table.id,
            date=date,
            status__not_in=['cancelled', 'no_show']
        )

        # Check for time conflicts
        has_conflict = False
        for booking in existing_bookings:
            booking_start = datetime.combine(booking.date, booking.time)
            booking_end = booking_start + timedelta(minutes=booking.duration_minutes)

            # Check overlap
            if (booking_start < requested_end) and (booking_end > requested_start):
                has_conflict = True
                break

        if not has_conflict:
            available_tables.append(table)

    return available_tables
```

### Auto Table Assignment
```python
def assign_table(restaurant_id, party_size, date, time):
    # Get available tables
    available = check_availability(restaurant_id, date, time, party_size)

    if not available:
        return None

    # Assign smallest suitable table (optimize capacity utilization)
    available.sort(key=lambda t: t.capacity)
    return available[0]
```

## Testing Requirements

### Unit Tests
- ✅ Create restaurant and retrieve it
- ✅ Create tables for restaurant
- ✅ Create customer with phone number
- ✅ Find customer by phone
- ✅ Create booking successfully
- ✅ Detect booking conflicts (same table, overlapping time)
- ✅ Auto-assign appropriate table based on party size
- ✅ Check availability correctly
- ✅ Handle invalid party size (0, negative, exceeds max)
- ✅ Validate date/time formats
- ✅ Update booking status
- ✅ Cancel booking

### Integration Tests
- ✅ Full booking flow: create customer → check availability → create booking
- ✅ Double booking prevention
- ✅ Multiple bookings for different tables at same time (should work)
- ✅ Edge case: booking exactly at boundary (12:00-13:30 and 13:30-15:00)

## File Structure
```
restaurant-assistant/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── database.py             # SQLAlchemy setup
│   ├── models.py               # SQLAlchemy models
│   ├── schemas.py              # Pydantic schemas
│   ├── crud.py                 # Database operations
│   ├── api/
│   │   ├── __init__.py
│   │   ├── restaurants.py      # Restaurant endpoints
│   │   ├── tables.py           # Table endpoints
│   │   ├── customers.py        # Customer endpoints
│   │   ├── bookings.py         # Booking endpoints
│   │   └── availability.py     # Availability checking
│   ├── services/
│   │   ├── __init__.py
│   │   └── booking_service.py  # Availability logic
│   └── tests/
│       ├── __init__.py
│       ├── test_restaurants.py
│       ├── test_tables.py
│       ├── test_customers.py
│       ├── test_bookings.py
│       └── test_availability.py
├── requirements.txt
├── .env.example
└── README.md
```

## Requirements.txt
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
pydantic==2.5.0
python-dotenv==1.0.0
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.1
```

## Success Criteria

Phase 1 is complete when:
1. ✅ All API endpoints work as specified
2. ✅ Database schema is created correctly
3. ✅ Availability checking prevents double bookings
4. ✅ Table auto-assignment works
5. ✅ All tests pass (90%+ coverage)
6. ✅ API can be tested via Swagger UI at /docs
7. ✅ Can run: `uvicorn backend.main:app --reload`
8. ✅ Can run: `pytest backend/tests/ -v`

## Notes
- Use SQLite for now (file: `restaurant.db`)
- Add proper error handling (404s, validation errors)
- Return helpful error messages
- Use HTTP status codes correctly (200, 201, 400, 404, 422)
- Add docstrings to all functions
- Type hints everywhere
- Follow REST conventions


CORE REQUIREMENTS:
1. FastAPI backend with SQLite database
2. Database models: Restaurant, Table, Customer, Booking
3. Full CRUD API endpoints for all models
4. Availability checking endpoint with conflict detection
5. Auto table assignment based on party size
6. Comprehensive test suite (pytest)
7. All tests must pass

IMPORTANT:
- Use SQLite (file: restaurant.db)
- Follow the exact database schema in the specification
- Implement the availability checking algorithm as specified
- Add proper error handling and validation
- Type hints and docstrings everywhere
- 90%+ test coverage

DELIVERABLES:
- backend/ directory with FastAPI application
- requirements.txt with all dependencies
- Passing test suite
- Working API accessible at http://localhost:8000/docs

**Date:** 2026-01-10 17:22:43
**Complexity:** high

## Summary

Build a complete Restaurant Reservation System backend API using FastAPI with SQLite database. The system will handle restaurants, tables, customers, and bookings with advanced availability checking and auto-table assignment. Architecture follows clean separation of concerns with models, schemas, CRUD operations, API routes, and business logic services.

## Database Changes

- **restaurants**: create - N/A
- **tables**: create - N/A
- **customers**: create - N/A
- **bookings**: create - N/A

## Backend Files

- **backend/main.py** (create): FastAPI application entry point with CORS, middleware, and route registration
- **backend/database.py** (create): SQLAlchemy database setup with SQLite configuration and session management
- **backend/models.py** (create): SQLAlchemy ORM models for Restaurant, Table, Customer, and Booking entities
- **backend/schemas.py** (create): Pydantic schemas for request/response validation and serialization
- **backend/crud.py** (create): Database CRUD operations with error handling and business logic
- **backend/api/__init__.py** (create): API module initialization
- **backend/api/restaurants.py** (create): Restaurant CRUD endpoints with validation
- **backend/api/tables.py** (create): Table management endpoints with restaurant association
- **backend/api/customers.py** (create): Customer endpoints with phone-based lookup
- **backend/api/bookings.py** (create): Booking CRUD endpoints with status management
- **backend/api/availability.py** (create): Availability checking endpoint with conflict detection
- **backend/services/__init__.py** (create): Services module initialization
- **backend/services/booking_service.py** (create): Core booking logic including availability checking and table assignment algorithms
- **backend/tests/__init__.py** (create): Test module initialization
- **backend/tests/conftest.py** (create): Pytest fixtures for test database and client setup
- **backend/tests/test_restaurants.py** (create): Restaurant API endpoint tests
- **backend/tests/test_tables.py** (create): Table management tests
- **backend/tests/test_customers.py** (create): Customer CRUD and lookup tests
- **backend/tests/test_bookings.py** (create): Booking creation, update, and cancellation tests
- **backend/tests/test_availability.py** (create): Availability checking and conflict detection tests
- **requirements.txt** (create): Python dependencies specification
- **.env.example** (create): Environment variables template
- **README.md** (create): Project documentation and setup instructions

## Frontend Files

No frontend files.

## API Endpoints

- **POST /api/restaurants**: Create new restaurant
- **GET /api/restaurants/{id}**: Get restaurant details
- **PUT /api/restaurants/{id}**: Update restaurant information
- **GET /api/restaurants**: List all restaurants
- **POST /api/tables**: Create new table
- **GET /api/restaurants/{restaurant_id}/tables**: List tables for a restaurant
- **PUT /api/tables/{id}**: Update table information
- **DELETE /api/tables/{id}**: Delete table
- **POST /api/customers**: Create new customer
- **GET /api/customers/by-phone/{phone}**: Find customer by phone number
- **PUT /api/customers/{id}**: Update customer information
- **POST /api/bookings**: Create booking with auto table assignment
- **GET /api/bookings/{id}**: Get booking details
- **PUT /api/bookings/{id}**: Update booking with re-validation
- **DELETE /api/bookings/{id}**: Cancel booking
- **GET /api/restaurants/{restaurant_id}/bookings**: List bookings with filters
- **GET /api/availability**: Check availability and suggest alternatives

## Dependencies

- fastapi==0.104.1
- uvicorn[standard]==0.24.0
- sqlalchemy==2.0.23
- pydantic==2.5.0
- python-dotenv==1.0.0
- pytest==7.4.3
- pytest-asyncio==0.21.1
- httpx==0.25.1

## Implementation Steps

1. Set up project structure and install dependencies
2. Create database.py with SQLAlchemy configuration for SQLite
3. Define all SQLAlchemy models in models.py with proper relationships
4. Create Pydantic schemas for request/response validation
5. Implement CRUD operations in crud.py with error handling
6. Build booking_service.py with availability checking and table assignment logic
7. Create API endpoints for restaurants and tables
8. Implement customer endpoints with phone-based lookup
9. Build booking endpoints with auto-assignment and validation
10. Create availability endpoint with conflict detection
11. Write comprehensive test suite with fixtures
12. Add integration tests for complete booking flow
13. Implement proper error handling and HTTP status codes
14. Add API documentation with docstrings
15. Test all endpoints via Swagger UI at /docs

## Risks

- Concurrent booking race conditions - mitigate with database transactions and row locking
- Time zone handling complexities - store all times in UTC
- Performance with large booking volumes - add database indexes on date/time columns
- Data validation edge cases - comprehensive input validation needed
- Booking status state transitions - ensure valid state machine logic
