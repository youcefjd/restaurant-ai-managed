# Voice AI Agent Flow - Complete Explanation

## Summary

**YES, the app DOES have voice AI capability** for:
- ✅ Taking to-go orders
- ✅ Checking the menu
- ✅ Checking hours of operation
- ✅ Making table reservations

**HOWEVER, there's a critical missing feature:** There's **no way for restaurant owners to configure their Twilio phone number** in the UI or via API. This is why you can't test it after creating a restaurant account.

---

## How the Voice AI Flow Works

### 1. **Call Flow Architecture**

```
Customer calls Twilio number
        ↓
Twilio receives call
        ↓
Twilio sends webhook to: /api/voice/welcome
        ↓
Backend identifies restaurant by matching:
   - Twilio "To" phone number (the number called)
   - RestaurantAccount.twilio_phone_number (in database)
        ↓
Backend responds with TwiML greeting
        ↓
Customer speaks: "I want to order a pizza"
        ↓
Twilio Whisper converts speech → text
        ↓
Twilio sends webhook to: /api/voice/process
   with: SpeechResult="I want to order a pizza"
        ↓
Backend sends to Gemini AI:
   - Customer message
   - Restaurant's full menu
   - Conversation context
        ↓
Gemini AI understands intent and responds
        ↓
Backend creates order/reservation in database
        ↓
Backend sends TwiML response back to Twilio
        ↓
Twilio speaks response to customer
        ↓
Conversation continues until order complete
```

### 2. **Restaurant Identification**

The system identifies which restaurant a call is for by matching the **Twilio phone number**:

**In `backend/api/voice.py` (lines 46-49):**
```python
# Look up which restaurant owns this Twilio number
restaurant = db.query(RestaurantAccount).filter(
    RestaurantAccount.twilio_phone_number == To
).first()
```

**The `To` parameter** is the Twilio phone number that was called. This must match the `twilio_phone_number` field in the `RestaurantAccount` table.

### 3. **AI Capabilities**

The AI (via Gemini) can handle:

**Menu Questions:**
- "What vegetarian options do you have?"
- "How much is the shawarma?"
- "What's on your menu?"

**Order Taking:**
- "I want 2 pizzas for delivery"
- "I'll take a large pepperoni, no tomato, extra cheese"
- Processes modifiers, quantities, delivery addresses

**Reservations:**
- "Table for 4 tomorrow at 7pm"
- Checks table availability
- Creates booking in database

**Hours of Operation:**
- "What are your hours?"
- Can be answered if stored in restaurant data

### 4. **Database Schema**

**RestaurantAccount model** (`backend/models_platform.py`):
```python
class RestaurantAccount(Base):
    # ... other fields ...
    twilio_phone_number = Column(String(20), nullable=True, unique=True)
```

This field stores the Twilio phone number that customers will call.

---

## The Missing Feature: Phone Number Configuration

### Current State

❌ **No API endpoint** to update `twilio_phone_number`
- Searched entire backend: No PATCH/PUT endpoint exists
- Only GET endpoint: `/api/onboarding/accounts/{id}` (read-only)

❌ **No frontend UI** to configure phone number
- Checked restaurant dashboard: No settings page
- No form to enter Twilio phone number
- Restaurant owners have no way to set this

### What Happens Now

1. Restaurant owner creates account via `/api/onboarding/signup`
2. Account is created with `twilio_phone_number = NULL`
3. Owner has no way to set the phone number
4. When customer calls, system can't find restaurant:
   ```python
   if not restaurant:
       logger.warning(f"No restaurant found for Twilio number {To}")
       # Returns error message to caller
   ```

### What's Needed

To make this work, you need:

1. **Backend API endpoint** to update phone number:
   ```
   PATCH /api/onboarding/accounts/{id}/twilio-phone
   Body: { "twilio_phone_number": "+15551234567" }
   ```

2. **Frontend Settings page** where restaurant owners can:
   - View current Twilio phone number (if set)
   - Enter/update Twilio phone number
   - See instructions on how to get a Twilio number
   - Test the connection

---

## How to Test (Manual Workaround)

Until the feature is added, you can manually set the phone number:

### Option 1: Direct Database Update

```bash
# Connect to SQLite database
sqlite3 restaurant_reservations.db

# Update the restaurant account
UPDATE restaurant_accounts 
SET twilio_phone_number = '+15551234567' 
WHERE id = 1;  -- Replace 1 with your restaurant account ID

# Verify
SELECT id, business_name, twilio_phone_number 
FROM restaurant_accounts;
```

### Option 2: Python Script

```python
from backend.database import SessionLocal
from backend.models_platform import RestaurantAccount

db = SessionLocal()
account = db.query(RestaurantAccount).filter(
    RestaurantAccount.id == YOUR_ACCOUNT_ID
).first()

account.twilio_phone_number = "+15551234567"  # Your Twilio number
db.commit()
```

---

## Complete Setup Requirements

For the voice AI to work, you need:

1. ✅ **Twilio Account** - Sign up at twilio.com
2. ✅ **Twilio Phone Number** - Buy a number ($1/month)
3. ✅ **Twilio Credentials** - Add to `.env`:
   ```
   TWILIO_ACCOUNT_SID=ACxxxxx
   TWILIO_AUTH_TOKEN=xxxxx
   TWILIO_PHONE_NUMBER=+15551234567
   PUBLIC_URL=https://your-domain.com
   ```
4. ✅ **Twilio Webhooks** - Configure in Twilio console:
   - Voice: `https://your-domain.com/api/voice/welcome`
   - SMS: `https://your-domain.com/api/voice/sms/incoming`
5. ❌ **Database Phone Number** - **MISSING**: No way to set `twilio_phone_number` in database
6. ✅ **Gemini API Key** - GOOGLE_AI_API_KEY configured in .env
7. ✅ **Menu Created** - Restaurant must have menu items

---

## Recommended Solution

I can add:

1. **Backend API endpoint** to update Twilio phone number
2. **Frontend Settings page** in restaurant dashboard
3. **Validation** to ensure phone number format is correct
4. **Instructions** on how to get a Twilio number

This would allow restaurant owners to:
- Configure their phone number after signup
- Update it if they change Twilio numbers
- See their current phone number in the dashboard
- Test the voice AI system

Would you like me to implement this feature?
