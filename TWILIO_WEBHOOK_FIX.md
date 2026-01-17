# 🔧 Fixing "Toll Free Number Unassigned" Error

## The Problem

When calling your Twilio number, you get: **"Sorry the toll free number you dialed is unassigned"**

This means Twilio doesn't know where to route the call because **no webhook is configured**.

---

## ✅ Solution: Configure Twilio Webhook

### Step 1: Get Your ngrok URL

Your ngrok URL is: `https://amparo-unsorry-unintricately.ngrok-free.dev`

### Step 2: Configure Twilio Console

1. **Go to Twilio Console**: https://console.twilio.com/
2. **Navigate**: Phone Numbers → Manage → Active Numbers
3. **Click** your phone number
4. **Scroll to "Voice Configuration"** section

### Step 3: Set Webhook URL

**In "A CALL COMES IN" section:**
- **Webhook URL**: `https://amparo-unsorry-unintricately.ngrok-free.dev/api/voice/welcome`
- **HTTP Method**: `POST`
- **Configure With**: `Webhooks`

**Click "Save"** at the bottom

### Step 4: Test

1. Call your Twilio number
2. You should hear: "Hey, thanks for calling [Restaurant Name]. How may I help you?"

---

## 🔍 Troubleshooting

### Still getting error?

**Check 1: ngrok is running**
```bash
# Verify ngrok is forwarding
# Should show: https://amparo-unsorry-unintricately.ngrok-free.dev -> http://localhost:8000
```

**Check 2: Backend is running**
```bash
# Test your backend directly
curl http://localhost:8000/health
# Or
curl https://amparo-unsorry-unintricately.ngrok-free.dev/health
```

**Check 3: Webhook endpoint is accessible**
```bash
# Test the webhook endpoint via ngrok
curl -X POST https://amparo-unsorry-unintricately.ngrok-free.dev/api/voice/welcome \
  -d "To=%2B15551234567&From=%2B15559876543"
```

**Check 4: Phone number is in database**
```bash
# Your Twilio phone number needs to be saved in the RestaurantAccount table
# Check via your admin dashboard or database
```

**Check 5: Webhook URL format**
- ✅ Correct: `https://amparo-unsorry-unintricately.ngrok-free.dev/api/voice/welcome`
- ❌ Wrong: `http://amparo-unsorry-unintricately.ngrok-free.dev/api/voice/welcome` (missing 's')
- ❌ Wrong: `https://localhost:8000/api/voice/welcome` (not accessible from internet)

---

## 📝 Important Notes

### ngrok Free Tier Limitation

Free ngrok URLs **change every time you restart ngrok**. 

**Before restarting ngrok:**
1. Note your new ngrok URL
2. Update the webhook in Twilio Console with the new URL
3. Save changes

**Or upgrade ngrok** for a stable URL that doesn't change.

### Phone Number in Database

Make sure your Twilio phone number is configured in your restaurant account:

```python
# Via API or admin dashboard
# Set twilio_phone_number field in RestaurantAccount
# Format: +15551234567 (E.164 format with + prefix)
```

---

## 🎯 Quick Checklist

- [ ] ngrok is running and shows "online" status
- [ ] Backend is running on port 8000
- [ ] Webhook URL is set in Twilio Console: `/api/voice/welcome`
- [ ] Webhook uses HTTPS (not HTTP)
- [ ] Webhook uses POST method
- [ ] Phone number is saved in database (RestaurantAccount.twilio_phone_number)
- [ ] Clicked "Save" in Twilio Console

---

## 🚀 Test Your Setup

After configuring, test by:

1. **Call your Twilio number** from another phone
2. **You should hear** the AI assistant greeting
3. **Speak your order** or question
4. **AI should respond** and take your order

If it still doesn't work, check the backend logs for error messages.
