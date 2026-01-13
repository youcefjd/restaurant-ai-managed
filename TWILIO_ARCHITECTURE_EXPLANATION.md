# Twilio Architecture Explanation

## Why Twilio Credentials in .env?

### Required in .env:
- ✅ **`TWILIO_ACCOUNT_SID`** - Required
- ✅ **`TWILIO_AUTH_TOKEN`** - Required

**Why?** These are needed for the platform to make API calls to Twilio:
- Send SMS confirmations to customers
- Handle incoming webhooks from Twilio
- Process voice calls

### NOT in .env:
- ❌ **`TWILIO_PHONE_NUMBER`** - **Removed!**

**Why removed?** Each restaurant has their own phone number stored in the database. There is no fallback phone number. If a restaurant hasn't set their phone number, SMS/voice simply won't work for that restaurant.

## How It Works Now

### Architecture:
```
Platform Twilio Account (credentials in .env - for API access only)
    ↓
    ├─ Restaurant 1: Phone number stored in database (required for SMS/voice)
    ├─ Restaurant 2: Phone number stored in database (required for SMS/voice)
    └─ Restaurant 3: Phone number stored in database (required for SMS/voice)
```

### Flow:

1. **Restaurant sets phone number** in Settings → Stored in `restaurant_accounts.twilio_phone_number`

2. **Customer calls** → Twilio webhook identifies restaurant by phone number

3. **SMS confirmations** → Sent from restaurant's phone number (REQUIRED - no fallback)

4. **If no phone number set** → SMS/voice features are disabled for that restaurant

### Important Constraint:

**All phone numbers must be in the same Twilio account** to send SMS from them. This means:
- If you're using one Twilio account for all restaurants → Works perfectly
- If each restaurant has their own Twilio account → Would need to store credentials per restaurant

## Current Setup (Recommended)

**One Twilio account for the platform:**
- Platform buys phone numbers through one account
- Assigns numbers to restaurants
- All SMS/voice goes through platform account
- Restaurants just configure their phone number in Settings

**Benefits:**
- Simpler setup (one set of credentials)
- Easier management
- Lower cost (bulk pricing)

## Alternative Setup (If Needed)

If you want restaurants to use their own Twilio accounts, you'd need to:
1. Store `twilio_account_sid` and `twilio_auth_token` per restaurant in database
2. Create Twilio client per restaurant when sending SMS
3. More complex, but gives restaurants full control

## Summary

**What you need in .env:**
- ✅ `TWILIO_ACCOUNT_SID` - Required (for API calls only)
- ✅ `TWILIO_AUTH_TOKEN` - Required (for API calls only)
- ❌ `TWILIO_PHONE_NUMBER` - **NOT NEEDED** (removed)

**What restaurants set in Settings:**
- ✅ `twilio_phone_number` - Their phone number (REQUIRED for SMS/voice to work)

**Important:**
- Platform credentials in .env are **only for making Twilio API calls**
- Each restaurant **must** set their own phone number in Settings
- If no phone number is set → SMS/voice features are disabled
- Dashboard shows warnings if phone number or menu is missing
