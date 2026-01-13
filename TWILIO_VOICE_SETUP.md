# 📞💬 Twilio Voice + SMS Integration - AI Assistant Setup

**Complete guide to enable AI-powered phone calls AND text messages for your restaurant**

---

## 🎯 What This Enables

### Voice Calls
When a customer **calls** your restaurant:
1. **Twilio answers** the call
2. **Customer speaks**: "I'd like to order 2 pizzas for delivery"
3. **Twilio Whisper** converts speech → text
4. **Ollama AI** understands the request
5. **AI responds** with order confirmation
6. **Twilio speaks** response back to customer
7. **Order created** in your dashboard

### Text Messages (SMS)
When a customer **texts** your restaurant:
1. **Twilio receives** the text
2. **Customer texts**: "1 large pepperoni pizza, delivery"
3. **Ollama AI** understands the request
4. **AI texts back**: "Great! Delivery address?"
5. **Customer replies**: "456 Oak Ave"
6. **AI texts**: "✅ Order #1234 confirmed! $17.99, 30 min delivery"
7. **Order created** in your dashboard

**All automatic!** No human needed to answer phone or texts.

---

## 🏗️ System Architecture

### Voice Call Flow
```
Customer Phone Call
        ↓
[Twilio Phone Number]
        ↓
[Twilio Voice API] ← Speech-to-Text (Whisper)
        ↓
[Your Server - Backend API]
   /api/voice/welcome
   /api/voice/process
        ↓
[Ollama AI - Local LLM]
   - Understands intent
   - Generates response
        ↓
[Your Restaurant Menu Database]
        ↓
[Response back to Twilio]
        ↓
[Text-to-Speech] → Customer hears response
```

### SMS Text Flow
```
Customer Text Message
        ↓
[Twilio Phone Number]
        ↓
[Twilio Messaging API]
        ↓
[Your Server - Backend API]
   /api/voice/sms/incoming
        ↓
[Ollama AI - Local LLM]
   - Understands intent
   - Generates response
        ↓
[Your Restaurant Menu Database]
        ↓
[Response back to Twilio]
        ↓
[SMS Message] → Customer receives text
```

**Same AI brain handles both voice AND text!**

---

## 📋 Prerequisites

✅ Server running (see SERVER_SETUP_GUIDE.md)
✅ Ollama AI working
✅ Backend API running on port 8000
✅ Public domain or ngrok tunnel

---

## 🔧 Step 1: Create Twilio Account

### Sign Up

1. Go to: https://www.twilio.com/try-twilio
2. Sign up with email
3. Verify phone number
4. You get **$15 free credit!**

### Get Your Credentials

1. Go to Twilio Console: https://console.twilio.com/
2. Find your:
   - **Account SID** - Looks like: `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - **Auth Token** - Click "Show" to reveal
   - Copy both - you'll need them!

---

## 📱 Step 2: Get a Phone Number

### Buy Twilio Number

1. In Twilio Console → Phone Numbers → Buy a Number
2. Select country (United States recommended)
3. Check **Voice** AND **SMS** capabilities ✅
4. Search for available numbers
5. Choose a number you like
6. Buy it (**$1/month**, uses your free credit)

**Your restaurant phone number!** Customers can call **AND** text this number.

**Copy the number:** Format like `+15551234567`

---

## 🌐 Step 3: Make Your Server Public

Twilio needs to reach your server over the internet. Two options:

### Option A: Ngrok (Quick Testing)

```bash
# Install ngrok
brew install ngrok  # Mac
# Or download from: https://ngrok.com/download

# Start ngrok tunnel to your backend
ngrok http 8000

# You'll see:
# Forwarding: https://abc123.ngrok.io → http://localhost:8000
```

**Copy the ngrok URL:** `https://abc123.ngrok.io`

**Note:** Free ngrok URLs change every restart. Upgrade for stable URL.

### Option B: Domain + HTTPS (Production)

If you have a domain (like `myrestaurant.com`):

```bash
# Setup covered in SERVER_SETUP_GUIDE.md
# Your URL: https://myrestaurant.com
```

---

## 🔐 Step 4: Configure Environment Variables

On your server:

```bash
cd ~/restaurant-ai-managed
nano .env
```

**Add Twilio credentials:**
```bash
# Twilio Voice Configuration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+15551234567

# Your public server URL
PUBLIC_URL=https://abc123.ngrok.io
# Or: PUBLIC_URL=https://myrestaurant.com
```

**Save the file** (Ctrl+O, Enter, Ctrl+X in nano)

**Restart backend:**
```bash
# If using systemd
sudo systemctl restart restaurant-backend

# If running manually
# Kill the uvicorn process and start again
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🎛️ Step 5: Configure Twilio Webhooks

### Set Voice Webhooks

1. Go to: Twilio Console → Phone Numbers → Manage Numbers
2. Click your phone number
3. Scroll to **Voice Configuration**

**Configure as follows:**

**A CALL COMES IN:**
- **Webhook:** `https://abc123.ngrok.io/api/voice/welcome`
   (Replace with YOUR ngrok or domain URL!)
- **HTTP Method:** POST
- **Configure With:** Webhooks

**PRIMARY HANDLER FAILS:**
- **Webhook:** `https://abc123.ngrok.io/api/voice/welcome`
- **HTTP Method:** POST

**STATUS CALLBACK URL:** (Optional)
- **URL:** `https://abc123.ngrok.io/api/voice/status`
- **HTTP Method:** POST

4. Click **Save**

### Set SMS Webhooks (Text Message Support)

**IMPORTANT:** Configure SMS to enable text message orders!

1. Stay on the same phone number configuration page
2. Scroll to **Messaging Configuration**

**Configure as follows:**

**A MESSAGE COMES IN:**
- **Webhook:** `https://abc123.ngrok.io/api/voice/sms/incoming`
   (Replace with YOUR ngrok or domain URL!)
- **HTTP Method:** POST
- **Configure With:** Webhooks

3. Click **Save**

---

## 🗣️ Step 6: How the Voice Flow Works

### When Customer Calls

```
1. Call connects to Twilio number
   ↓
2. Twilio sends webhook to: /api/voice/welcome
   ↓
3. Your server responds with TwiML:
   <Response>
     <Gather input="speech" timeout="3">
       <Say>Thank you for calling [Restaurant Name]!
            How can I help you today?</Say>
     </Gather>
   </Response>
   ↓
4. Twilio plays greeting, listens for customer
   ↓
5. Customer speaks: "I want to order a pizza"
   ↓
6. Twilio transcribes speech → text
   ↓
7. Twilio sends webhook to: /api/voice/process
   with: SpeechResult="I want to order a pizza"
   ↓
8. Your backend receives transcription
   ↓
9. Backend sends to Ollama AI:
   "Customer says: I want to order a pizza"
   "Menu: [Your full menu]"
   "What do you respond?"
   ↓
10. Ollama responds:
    "Great! We have Margherita, Pepperoni, and
     Vegetarian pizzas. Which would you like?"
   ↓
11. Backend sends TwiML back:
    <Response>
      <Gather input="speech">
        <Say>[Ollama's response]</Say>
      </Gather>
    </Response>
   ↓
12. Twilio speaks response to customer
    ↓
13. Listens for next input...
    (Loop continues until order complete)
```

### Conversation State

The system remembers context:
- What customer asked
- What they're ordering
- Their phone number
- Delivery address
- Previous conversation turns

**Stored in:** `conversation_state` dictionary (in-memory)
**For production:** Use Redis for persistence

---

## 💬 SMS Flow (Text Messages)

### When Customer Texts

```
1. Customer sends text: "I want to order a large pepperoni pizza"
   ↓
2. Twilio receives SMS
   ↓
3. Twilio sends webhook to: /api/voice/sms/incoming
   with:
   - From: +15559876543 (customer phone)
   - To: +15551234567 (your restaurant number)
   - Body: "I want to order a large pepperoni pizza"
   ↓
4. Backend identifies restaurant by "To" number
   ↓
5. Backend loads restaurant menu
   ↓
6. Backend sends to Ollama AI:
   "Customer says: I want to order a large pepperoni pizza"
   "Menu: [Full menu with prices]"
   "Current context: [Previous messages if any]"
   ↓
7. Ollama responds:
   "Great choice! Large Pepperoni Pizza is $18.99.
    Would you like delivery or pickup?"
   ↓
8. Backend creates TwiML SMS response:
   <Response>
     <Message>Great choice! Large Pepperoni Pizza is $18.99.
              Would you like delivery or pickup?</Message>
   </Response>
   ↓
9. Twilio sends SMS to customer
   ↓
10. Customer replies: "Delivery to 123 Main St"
    ↓
11. Process repeats... (maintains conversation context)
    ↓
12. When complete:
    - Order created in database
    - Confirmation SMS sent
    - Order appears in restaurant dashboard
```

### SMS vs Voice Comparison

| Feature | Voice Calls | SMS Messages |
|---------|-------------|--------------|
| **Speed** | Real-time (immediate) | Async (customer can reply anytime) |
| **Input** | Speech-to-text | Direct text |
| **Best For** | Complex orders, elderly customers | Quick orders, busy customers |
| **Cost** | $0.0085/min | $0.0079/message |
| **Context** | Session-based (call duration) | Persistent (hours/days) |

### SMS Advantages

✅ **Convenience** - Customer can text while doing other things
✅ **Accuracy** - No speech recognition errors
✅ **Record** - Customer has text confirmation
✅ **Async** - Customer replies when ready
✅ **Quiet** - Works in noisy environments

### Example SMS Conversations

**Order Pizza:**
```
Customer: Hi, can I order a pizza?
AI: Sure! We have Margherita ($15), Pepperoni ($17), and Veggie ($16). Which would you like?
Customer: Pepperoni please
AI: Great! Pepperoni pizza $17. Delivery or pickup?
Customer: Delivery to 123 Main St
AI: Perfect! Total: $17. Estimated delivery 30 mins. Confirm?
Customer: Yes
AI: ✅ Order Confirmed! Order #1234. We'll text when on the way!
```

**Make Reservation:**
```
Customer: Table for 2 tonight at 7?
AI: Let me check... Yes! We have availability at 7 PM for 2 guests. What name?
Customer: Sarah
AI: ✅ Reservation Confirmed! Table for 2 on Jan 12 at 7:00 PM. Name: Sarah. Confirmation #5678. See you then!
```

**Check Menu:**
```
Customer: What vegetarian options do you have?
AI: Our vegetarian options:
    🥗 Caesar Salad - $12
    🍝 Vegetarian Pasta - $14
    🍕 Veggie Pizza - $16
    🥙 Falafel Wrap - $11
Customer: Thanks!
AI: You're welcome! Text back to order anytime!
```

### SMS Conversation State

The system maintains context per phone number:
- Each customer-restaurant pair has unique conversation
- Context persists for multiple messages
- Auto-expires after inactivity
- Remembers: items in cart, delivery address, customer preferences

**Stored in:** `sms_conversation_state` dictionary
**Cleanup:** Automatic after conversation ends or timeout

---

## 🧪 Step 7: Test the System

### Test Voice Calls

### Test from Your Phone

1. Call your Twilio number: `+15551234567`
2. You should hear: "Thank you for calling [Restaurant]! How can I help you?"
3. Say: "What's on your menu?"
4. AI should respond with menu items
5. Continue conversation naturally

### Test Scenarios

**Scenario 1: Menu Question**
- You: "What vegetarian options do you have?"
- AI: Lists vegetarian items from your menu

**Scenario 2: Order**
- You: "I want to order 2 Margherita pizzas for delivery"
- AI: "Great! 2 Margherita pizzas. What's your delivery address?"
- You: "123 Main Street"
- AI: "Perfect! Total is $33.90. Confirm order?"
- You: "Yes"
- AI: "Order confirmed! We'll have it ready in 20 minutes."

**Scenario 3: Reservation**
- You: "I need a table for 4 on Friday at 7 PM"
- AI: Checks availability
- AI: "Yes, we have a table available. What name?"
- You: "John"
- AI: "Confirmed! Table for 4 on Friday at 7 PM for John."

### Test SMS Messages

1. **Text your Twilio number:** `+15551234567`
2. Send: `"Hi, what's on your menu?"`
3. You should receive an SMS response with menu items
4. Continue texting naturally

**Test SMS Scenarios:**

**Scenario 1: Quick Order**
```
You: "1 large pepperoni pizza, delivery"
AI: "Pepperoni pizza $17.99. Delivery address?"
You: "456 Oak Avenue"
AI: "Total $17.99. Confirm order?"
You: "Yes"
AI: "✅ Order #1234 confirmed! 30 min delivery"
```

**Scenario 2: Menu Browse**
```
You: "What vegetarian options?"
AI: Lists all vegetarian menu items with prices
You: "I'll take the veggie pasta"
AI: "Great! Veggie pasta $14. Pickup or delivery?"
```

**Scenario 3: Table Reservation**
```
You: "Table for 2 tomorrow at 6pm"
AI: "Available! What name for reservation?"
You: "Mike"
AI: "✅ Reserved! Table for 2, Jan 13 at 6pm, Name: Mike. #5678"
```

### Check Dashboard

After voice call or SMS test:
1. Log into restaurant dashboard
2. Go to **Orders** or **Reservations**
3. You should see the test order/booking from both voice AND SMS!

---

## 🔍 Step 8: Monitor & Debug

### Check Twilio Logs

**For Voice Calls:**
1. Twilio Console → Monitor → Logs → Call Logs
2. Click your test call
3. See all webhook requests and responses
4. Check for errors (red indicators)

**For SMS Messages:**
1. Twilio Console → Monitor → Logs → Messaging Logs
2. Click your test message
3. See webhook requests and responses
4. Check for errors (red indicators)

### Check Server Logs

```bash
# If using systemd/launchd
sudo journalctl -u restaurant-backend -f  # Linux
tail -f ~/Library/Logs/restaurant-backend.log  # Mac

# If using PM2
pm2 logs restaurant-backend

# If running manually
# Check the terminal where uvicorn is running
```

**Look for (Voice):**
- `INFO: Voice call received from +15551234567 to +15559876543`
- `INFO: Processing speech from +15551234567: [transcription]`
- `INFO: Ollama response: [AI response]`

**Look for (SMS):**
- `INFO: SMS received from +15551234567 to +15559876543: [message]`
- `INFO: Processing SMS: [message content]`
- `INFO: SMS response sent: [AI response]`

### Common Issues

**Problem:** Call connects but no greeting
**Solution:**
- Check webhook URL is correct
- Verify backend is running
- Check ngrok tunnel is active
- Test webhook: `curl -X POST https://your-domain.com/api/voice/welcome`

**Problem:** SMS not received
**Solution:**
- Check SMS webhook URL is correct
- Verify messaging capability on Twilio number
- Check ngrok tunnel is active
- Test webhook: `curl -X POST https://your-domain.com/api/voice/sms/incoming -d "Body=test&From=%2B15551234567&To=%2B15559876543"`

**Problem:** AI doesn't respond
**Solution:**
- Check Ollama is running: `curl http://localhost:11434/api/tags`
- Verify OLLAMA_URL in .env
- Check server logs for errors
- Test conversation handler directly

**Problem:** Speech not transcribed
**Solution:**
- Speak clearly and wait for beep
- Check phone connection quality
- Try shorter sentences
- Consider using SMS for clearer input

**Problem:** Wrong menu items
**Solution:**
- Verify menu is in database
- Check AI has access to menu
- Review conversation_handler.py
- Test with SMS first (eliminates speech-to-text issues)

**Problem:** Restaurant identification fails
**Solution:**
- Verify `twilio_phone_number` is set in database for restaurant
- Check "To" parameter in webhook logs
- Ensure each restaurant has unique Twilio number

---

## 🎨 Customization

### Change Greeting Message

Edit: `backend/services/voice_service.py`

```python
def create_welcome_response(self) -> VoiceResponse:
    """Create welcome TwiML response."""
    response = VoiceResponse()
    gather = response.gather(
        input='speech',
        timeout=3,
        action='/api/voice/process',
        method='POST'
    )
    # CUSTOMIZE THIS:
    gather.say(
        "Welcome to Mario's Pizza! "
        "I'm your AI assistant. "
        "How may I help you today?",
        voice='Polly.Joanna',
        language='en-US'
    )
    return response
```

### Change AI Voice

Available voices:
- `Polly.Joanna` - Female, clear (default)
- `Polly.Matthew` - Male, professional
- `Polly.Ivy` - Female, warm
- `Polly.Salli` - Female, friendly
- `Polly.Joey` - Male, casual

### Add SMS Confirmations

After order placed, send SMS:

```python
# Already implemented in conversation_handler.py
# Just enable SMS service by adding Twilio credentials
```

Customer receives:
```
📦 Order Confirmed!
Restaurant: Your Restaurant
Order #123

1x Margherita Pizza
2x Caesar Salad

Total: $33.90
Delivery to: 123 Main St

We'll have it ready in 20 minutes!
```

---

## 💰 Costs

### Twilio Pricing

**Phone Number:** $1/month (supports both voice AND SMS)

**Voice Calls:**
- Incoming: $0.0085/minute
- Outgoing: $0.013/minute
- Speech Recognition (Whisper): $0.02/minute of audio
- Text-to-Speech: $0.006 per 1000 characters

**SMS Messages:**
- Incoming: $0.0079/message (160 chars)
- Outgoing: $0.0079/message (160 chars)
- Long messages (>160 chars): Multiple segment charges

### Example Monthly Costs

**Scenario 1: Voice-Heavy Restaurant**
- **100 voice calls/month, 3 min average, 20 SMS/month:**
  - Phone number: $1.00
  - Voice calls: 100 × 3 × $0.0085 = $2.55
  - Speech recognition: 100 × 3 × $0.02 = $6.00
  - Text-to-speech: ~$0.50
  - SMS: 40 messages × $0.0079 = $0.32
  - **Total: ~$10.37/month**

**Scenario 2: SMS-Heavy Restaurant**
- **50 voice calls/month, 200 SMS conversations/month:**
  - Phone number: $1.00
  - Voice calls: 50 × 3 × $0.0085 = $1.28
  - Speech recognition: 50 × 3 × $0.02 = $3.00
  - Text-to-speech: ~$0.25
  - SMS: 400 messages (2 per conversation) × $0.0079 = $3.16
  - **Total: ~$8.69/month**

**Scenario 3: Balanced**
- **75 voice calls, 100 SMS conversations/month:**
  - Phone number: $1.00
  - Voice calls: $1.91
  - Speech recognition: $4.50
  - Text-to-speech: ~$0.38
  - SMS: 200 messages × $0.0079 = $1.58
  - **Total: ~$9.37/month**

**Very affordable!** Much cheaper than hiring phone staff.

### Cost Comparison

| Solution | Monthly Cost | Staff Hours Saved |
|----------|-------------|-------------------|
| **AI Phone + SMS** | $8-12/month | 20-40 hours |
| **Part-time Staff** | $800-1600/month | - |
| **Savings** | **98% cheaper!** | Staff can focus on food |

---

## 🚀 Production Tips

### 1. Use Redis for State

Replace in-memory state with Redis:

```python
import redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Store conversation state
redis_client.setex(
    f"conversation:{call_sid}",
    3600,  # 1 hour expiry
    json.dumps(state)
)
```

### 2. Add Call Recording

In TwiML response:
```xml
<Response>
  <Say>...</Say>
  <Record maxLength="120" action="/api/voice/recording"/>
</Response>
```

### 3. Business Hours Check

```python
def is_open() -> bool:
    """Check if restaurant is open."""
    now = datetime.now().time()
    opening = time(11, 0)  # 11 AM
    closing = time(22, 0)  # 10 PM
    return opening <= now <= closing
```

### 4. Queue System

For busy times:
```python
if too_many_calls:
    response.say("We're experiencing high call volume. "
                 "Please hold or try our online ordering.")
    response.play(music_url)
```

### 5. Fallback to Human

```python
if ai_confidence < 0.7:
    response.say("Let me connect you to a team member.")
    response.dial("+1555RESTAURANT")
```

---

## 📊 Analytics

### Track Metrics

Monitor:
- Call volume by hour/day
- Average call duration
- Order conversion rate
- Most asked questions
- Failed transcriptions

### Dashboard Integration

Add to restaurant dashboard:
- Today's calls: 45
- Orders via phone: 23
- Reservations via phone: 12
- Average call time: 2:34

---

## 🔐 Security

### Validate Twilio Requests

```python
from twilio.request_validator import RequestValidator

validator = RequestValidator(os.getenv('TWILIO_AUTH_TOKEN'))

def verify_twilio_request(request):
    signature = request.headers.get('X-Twilio-Signature', '')
    url = str(request.url)
    params = request.form

    if not validator.validate(url, params, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")
```

**Prevents:** Fake requests to your webhooks

---

## ✅ Testing Checklist

Before going live:

- [ ] Can call Twilio number
- [ ] Greeting plays correctly
- [ ] AI understands menu questions
- [ ] AI can take orders
- [ ] AI can make reservations
- [ ] Orders appear in dashboard
- [ ] Reservations appear in dashboard
- [ ] Customer receives confirmation
- [ ] Works during busy times
- [ ] Graceful error handling

---

## 📞 Where to Put Your API Keys

**You asked: "tell me where i need to put my twilio api key"**

**Answer:**

### On Server Computer:

1. Navigate to your project:
```bash
cd ~/restaurant-ai-managed
```

2. Edit the .env file:
```bash
nano .env
```

3. Add these lines (replace with YOUR actual values):
```bash
# Twilio Voice Configuration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+15551234567

# Your public server URL (ngrok or domain)
PUBLIC_URL=https://abc123.ngrok.io
```

4. Save file (Ctrl+O, Enter, Ctrl+X)

5. Restart backend:
```bash
sudo systemctl restart restaurant-backend
# Or if running manually: kill and restart uvicorn
```

**That's it!** The backend automatically reads these values.

**File location:** `/home/youruser/restaurant-ai-managed/.env`
**Never commit** `.env` to git (it's in .gitignore)

---

## 🎓 Summary

**What you did:**
1. ✅ Created Twilio account
2. ✅ Bought phone number ($1/month)
3. ✅ Added credentials to `.env` file
4. ✅ Made server public (ngrok or domain)
5. ✅ Configured Twilio webhooks
6. ✅ Tested by calling number

**What happens now:**
- Customers call your Twilio number
- AI answers automatically
- Takes orders and reservations
- Orders appear in dashboard
- No human interaction needed!

**Powered by:**
- 🎙️ Twilio Voice (call handling)
- 🗣️ Twilio Whisper (speech-to-text)
- 🤖 Ollama LLM (understanding & responses)
- 💾 Your restaurant database (menu & orders)

**Cost:** ~$10-20/month for typical restaurant volume

**Support:** Check Twilio docs at https://www.twilio.com/docs/voice

---

**Your AI phone assistant is ready!** 🎉📞
