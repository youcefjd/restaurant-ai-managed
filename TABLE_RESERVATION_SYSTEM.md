# Table Reservation System Documentation
## 90-Minute Time Slots with Automatic & Manual Availability Management

---

## 🎯 System Overview

**How It Works**: Tables are reserved for **90-minute slots**. The AI automatically checks availability and prevents double-booking. Restaurants can manually control table availability.

---

## 📊 Core Concepts

### 1. Time-Based Availability (90-Minute Slots)

Each reservation blocks a table for **90 minutes** from the booking time:

```
Example: Booking at 7:00 PM

Timeline:
├─ 7:00 PM: Reservation starts
├─ 8:30 PM: Reservation ends (90 minutes later)
└─ Table becomes available again

During 7:00-8:30 PM:
- This table CANNOT be booked
- AI will suggest alternative tables or times
```

### 2. Automatic Table Assignment

When a customer requests a booking, the system:

1. **Finds tables with sufficient capacity**
   - Party of 4 → Tables with capacity >= 4

2. **Checks time slot availability**
   - Requested time: 7:00 PM
   - Checks: 7:00 PM - 8:30 PM (90 minutes)
   - Looks for conflicts with existing bookings

3. **Assigns smallest suitable table**
   - Priority: Optimize table usage
   - Party of 4 → Assign 4-seat table (not 8-seat)

4. **Creates booking or suggests alternatives**
   - If available → Book it!
   - If not → "Try 6:30 PM or 8:00 PM instead"

---

## 🤖 AI Booking Flow

### Scenario 1: Available Table

```
Customer: "I want a table for 4 people tonight at 7pm"

AI Process:
1. Parse: party_size=4, date=today, time=7:00pm
2. Check availability: find_available_table(4, today, 7pm)
3. Found: Table #2 (capacity 4) is free
4. Book: Reserve Table #2 from 7:00-8:30pm
5. Confirm: "Great! Table #2 is reserved for 4 guests at 7pm"

Database:
- table_id: 2
- booking_time: 19:00:00
- duration_minutes: 90
- status: confirmed

Result: Table #2 is BLOCKED from 7:00-8:30pm
```

### Scenario 2: No Tables Available (Conflict)

```
Customer: "Table for 6 at 7pm"

AI Process:
1. Check: find_available_table(6, today, 7pm)
2. Result: No tables available (all large tables booked)
3. Find alternatives: suggest_alternative_times()
4. Suggest: "No tables for 6 at 7pm. Try 6:00pm, 8:00pm, or 9:00pm?"

Customer: "8pm works"

AI: Checks again, books at 8:00pm if available
```

### Scenario 3: Overlapping Bookings (Conflict Detection)

```
Existing Bookings:
- Table #1: 6:30 PM - 8:00 PM (party of 4)
- Table #2: 7:00 PM - 8:30 PM (party of 2)

Customer: "Table for 4 at 7:30pm"

AI Check:
- Table #1: CONFLICT
  → 7:30pm falls within 6:30-8:00pm ❌
- Table #2: CONFLICT
  → 7:30pm falls within 7:00-8:30pm ❌
- Table #3: AVAILABLE ✅
  → No bookings from 7:30-9:00pm

Result: Books Table #3
```

---

## 🛠️ Manual Control (Restaurant Dashboard)

### Feature 1: Take Table Out of Service

**Use Case**: Maintenance, VIP reservation, broken chair, etc.

```http
PATCH /api/table-management/tables/3
{
  "is_active": false
}

Response:
{
  "message": "Table 3 is now out of service",
  "is_active": false
}
```

**Effect**:
- Table #3 will NOT appear in availability checks
- AI won't assign this table to any bookings
- Existing bookings remain valid

**To Reactivate**:
```http
PATCH /api/table-management/tables/3
{
  "is_active": true
}
```

### Feature 2: Add New Table

```http
POST /api/table-management/tables/
{
  "restaurant_id": 1,
  "table_number": "6",
  "capacity": 4,
  "location": "Patio"
}

Response:
{
  "id": 6,
  "table_number": "6",
  "capacity": 4,
  "location": "Patio",
  "is_active": true,
  "message": "Table 6 created successfully"
}
```

### Feature 3: Update Table Capacity

```http
PATCH /api/table-management/tables/2
{
  "capacity": 6
}

Response:
{
  "message": "Table 2 capacity updated to 6",
  "capacity": 6
}
```

**Effect**: Table #2 can now accommodate parties up to 6 people

### Feature 4: Check Availability (Dashboard Tool)

```http
POST /api/table-management/availability/check
{
  "restaurant_id": 1,
  "party_size": 4,
  "booking_date": "2026-01-20",
  "booking_time": "19:00"
}

Response:
{
  "available": true,
  "available_tables_count": 2,
  "message": "Table available for 4 people at 19:00"
}

OR if not available:

{
  "available": false,
  "available_tables_count": 0,
  "suggested_times": ["18:00", "18:30", "20:00"],
  "message": "No tables available for 4 at 19:00. Try: 06:00 PM, 06:30 PM, 08:00 PM"
}
```

### Feature 5: View Table Schedule

```http
GET /api/table-management/tables/1/schedule?date=2026-01-20

Response:
{
  "table_id": 1,
  "date": "2026-01-20",
  "bookings": [
    {
      "booking_id": 5,
      "start_time": "18:00:00",
      "end_time": "19:30:00",
      "duration_minutes": 90,
      "party_size": 4,
      "status": "confirmed"
    },
    {
      "booking_id": 8,
      "start_time": "20:00:00",
      "end_time": "21:30:00",
      "duration_minutes": 90,
      "party_size": 2,
      "status": "confirmed"
    }
  ],
  "message": "Found 2 bookings for this table"
}
```

**Visual Representation**:
```
Table #1 Schedule for Jan 20, 2026:
├─ 5:00 PM - 6:00 PM: AVAILABLE
├─ 6:00 PM - 7:30 PM: BOOKED (Booking #5, party of 4)
├─ 7:30 PM - 8:00 PM: AVAILABLE
├─ 8:00 PM - 9:30 PM: BOOKED (Booking #8, party of 2)
└─ 9:30 PM - 10:00 PM: AVAILABLE
```

### Feature 6: Get All Available Slots

```http
GET /api/table-management/availability/slots/1?party_size=4&date=2026-01-20

Response:
[
  {
    "time": "17:00",
    "time_formatted": "05:00 PM",
    "available_tables": 3
  },
  {
    "time": "17:30",
    "time_formatted": "05:30 PM",
    "available_tables": 3
  },
  {
    "time": "18:00",
    "time_formatted": "06:00 PM",
    "available_tables": 2
  },
  {
    "time": "19:00",
    "time_formatted": "07:00 PM",
    "available_tables": 0  // FULLY BOOKED
  }
]
```

**Use Case**: Display availability calendar in dashboard

---

## 📱 Customer Experience

### Voice Call Example

```
Customer: "I want to book a table"

AI: "I'd be happy to help! How many people?"

Customer: "Four people"

AI: "Great! What date and time work for you?"

Customer: "Tonight at 7pm"

AI: [Checks availability]
    ✅ Table #2 available from 7:00-8:30pm

AI: "Perfect! I have Table #2 available for 4 guests tonight at 7pm.
     May I have your name?"

Customer: "John Smith"

AI: "Excellent! Your table is reserved, John. Table #2 for 4 guests
     tonight at 7pm. See you then!"

[SMS sent: "Reservation confirmed! Table #2, 7:00 PM, 4 guests"]
```

### If Table Not Available

```
Customer: "Table for 8 tonight at 7pm"

AI: [Checks availability]
    ❌ No tables for 8 available at 7:00-8:30pm

AI: "I don't have a table for 8 available at 7pm tonight.
     However, I have availability at 6pm, 8pm, or 9pm.
     Would any of those work?"

Customer: "8pm is fine"

AI: [Checks 8:00pm]
    ✅ Table #5 (capacity 8) available 8:00-9:30pm

AI: "Perfect! Table #5 is reserved for 8 guests at 8pm tonight."
```

---

## 🔒 Conflict Prevention Logic

### SQL Conflict Check

```sql
-- Check if table is available at requested time
SELECT * FROM bookings
WHERE table_id = ?              -- Specific table
  AND booking_date = ?          -- Same date
  AND status IN ('pending', 'confirmed')  -- Active bookings only
  AND (
    -- New booking (7:00-8:30) overlaps existing booking
    -- Case 1: New booking starts during existing booking
    (
      ? >= booking_time AND
      ? < (booking_time + INTERVAL duration_minutes MINUTE)
    )
    OR
    -- Case 2: New booking ends during existing booking
    (
      (? + INTERVAL 90 MINUTE) > booking_time AND
      (? + INTERVAL 90 MINUTE) <= (booking_time + INTERVAL duration_minutes MINUTE)
    )
    OR
    -- Case 3: New booking completely covers existing booking
    (
      ? <= booking_time AND
      (? + INTERVAL 90 MINUTE) >= (booking_time + INTERVAL duration_minutes MINUTE)
    )
  )

-- If this returns ANY rows → CONFLICT (table not available)
-- If this returns ZERO rows → AVAILABLE (safe to book)
```

### Visual Conflict Examples

```
Scenario A: Start Time Conflict
Existing: |====6:00---7:30====|
New:           |====7:00---8:30====|
                ↑ CONFLICT!
Result: Cannot book (starts during existing)

Scenario B: End Time Conflict
Existing:      |====7:00---8:30====|
New:      |====6:30---8:00====|
                           ↑ CONFLICT!
Result: Cannot book (ends during existing)

Scenario C: Complete Overlap
Existing:   |====7:00---8:30====|
New:      |======6:00---9:00======|
          ↑                      ↑
Result: Cannot book (covers existing)

Scenario D: No Conflict
Existing: |====6:00---7:30====|
New:                          |====8:00---9:30====|
Result: ✅ CAN BOOK (no overlap)
```

---

## 📊 Dashboard Features for Restaurants

### Real-Time Availability View

```
┌─────────────────────────────────────────────────────────┐
│ Table Availability - Tonight                            │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ 5:00 PM  [Table 1] [Table 2] [Table 3] [Table 4]  ✅   │
│ 5:30 PM  [Table 1] [Table 2] [Table 3] [Table 4]  ✅   │
│ 6:00 PM  [Booked ] [Table 2] [Table 3] [Table 4]  ✅   │
│ 6:30 PM  [Booked ] [Booked ] [Table 3] [Table 4]  ✅   │
│ 7:00 PM  [Booked ] [Booked ] [Booked ] [Table 4]  ✅   │
│ 7:30 PM  [Booked ] [Booked ] [Booked ] [Booked ]  ❌   │
│ 8:00 PM  [Table 1] [Table 2] [Table 3] [Booked ]  ✅   │
│ 8:30 PM  [Table 1] [Table 2] [Table 3] [Table 4]  ✅   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Table Management Actions

```
┌─────────────────────────────────────────────────────────┐
│ Table #3 - Capacity: 4                                  │
├─────────────────────────────────────────────────────────┤
│ Status: ⚪ Active                                       │
│ Location: Main Dining                                   │
│                                                          │
│ Actions:                                                │
│ [Take Out of Service] [Edit Capacity] [View Schedule]  │
│                                                          │
│ Today's Bookings:                                       │
│ • 6:00 PM - 7:30 PM: John Smith (party of 4)           │
│ • 8:00 PM - 9:30 PM: Sarah Jones (party of 2)          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 🧪 Testing the System

### Test 1: Simple Booking (Available)

```bash
curl -X POST http://localhost:8000/api/test/test-conversation \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "+15551112222",
    "message": "I want to book a table for 4 people tomorrow at 7pm, my name is Alex",
    "account_id": 3,
    "context": {}
  }'

Expected: Booking created, table assigned
```

### Test 2: Conflict Detection

```bash
# First booking
curl -X POST http://localhost:8000/api/bookings/ \
  -H "Content-Type: application/json" \
  -d '{
    "restaurant_id": 1,
    "customer_phone": "+15551111111",
    "customer_name": "Alice",
    "party_size": 4,
    "booking_date": "2026-01-25",
    "booking_time": "19:00:00"
  }'

# Second booking (conflict)
curl -X POST http://localhost:8000/api/bookings/ \
  -H "Content-Type: application/json" \
  -d '{
    "restaurant_id": 1,
    "customer_phone": "+15552222222",
    "customer_name": "Bob",
    "party_size": 4,
    "booking_date": "2026-01-25",
    "booking_time": "19:30:00"  # Conflicts with first booking
  }'

Expected: 409 Conflict with alternative times suggested
```

### Test 3: Manual Table Control

```bash
# Take table out of service
curl -X PATCH http://localhost:8000/api/table-management/tables/1 \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'

# Try to book (should skip table #1)
curl -X POST http://localhost:8000/api/bookings/ ...

Expected: Table #1 not considered, assigns different table
```

---

## 📈 Capacity Management

### Optimal Table Usage

The system assigns tables efficiently:

```
Restaurant has:
- 2x Tables (capacity 2)
- 2x Tables (capacity 4)
- 1x Table (capacity 8)

Booking for 2 people:
✅ Assigns 2-seat table (optimal)
❌ Doesn't waste 4-seat or 8-seat table

Booking for 5 people:
✅ Assigns 8-seat table (only option)

Booking for 4 people:
✅ Assigns 4-seat table (exact match)
```

### Manual Capacity Adjustments

```
Scenario: Party larger than expected

Table #2 normally seats 4, but you can accommodate 5 temporarily:

PATCH /api/table-management/tables/2
{
  "capacity": 5
}

Now bookings for 5 people can be assigned to Table #2.

After the event:
PATCH /api/table-management/tables/2
{
  "capacity": 4
}

Restore normal capacity.
```

---

## 🎯 Summary

### ✅ What's Implemented

1. **90-minute reservation slots** (DEFAULT_RESERVATION_DURATION = 90)
2. **Automatic availability checking** (prevents double-booking)
3. **Smart table assignment** (smallest suitable table)
4. **Conflict detection** (time slot overlaps)
5. **Alternative time suggestions** (if requested time unavailable)
6. **Manual table control** (take out of service, adjust capacity)
7. **Table schedule views** (see all bookings for a table)
8. **Availability calendar** (show all available slots)

### 🔄 How It Works

**When AI Books a Table**:
1. Customer requests: "Table for 4 at 7pm"
2. System finds tables: capacity >= 4, is_active = true
3. Checks availability: 7:00-8:30pm slot free?
4. Assigns table: Smallest suitable available table
5. Creates booking: Blocks table for 90 minutes
6. Confirms: "Table #2 reserved for 4 at 7pm"

**When Restaurant Manages**:
1. Dashboard: View all tables and their status
2. Actions: Take out of service, change capacity, view schedule
3. Effect: AI respects manual changes immediately
4. Bookings: Existing reservations remain valid

---

**Status**: ✅ FULLY IMPLEMENTED
**Duration**: 90 minutes per reservation
**Conflict Prevention**: Automatic
**Manual Control**: Available via API & Dashboard

🎉 **Ready to use!**
