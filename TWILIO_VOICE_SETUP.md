# 📞 Twilio Voice Integration - AI Phone Assistant Setup

**Complete guide to enable AI-powered phone calls for your restaurant**

---

## 🎯 What This Enables

When a customer calls your restaurant:
1. **Twilio answers** the call
2. **Customer speaks**: "I'd like to order 2 pizzas for delivery"
3. **Twilio Whisper** converts speech → text
4. **Ollama AI** understands the request
5. **AI responds** with order confirmation
6. **Twilio speaks** response back to customer
7. **Order created** in your dashboard

**All automatic!** No human needed to answer.

---

## 🏗️ System Architecture

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
3. Check **Voice** capability
4. Search for available numbers
5. Choose a number you like
6. Buy it (**$1/month**, uses your free credit)

**Your restaurant phone number!** Customers will call this.

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

## 🧪 Step 7: Test the System

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

### Check Dashboard

After test call:
1. Log into restaurant dashboard
2. Go to **Orders** or **Reservations**
3. You should see the test order/booking!

---

## 🔍 Step 8: Monitor & Debug

### Check Twilio Logs

1. Twilio Console → Monitor → Logs → Call Logs
2. Click your test call
3. See all webhook requests and responses
4. Check for errors (red indicators)

### Check Server Logs

```bash
# If using systemd
sudo journalctl -u restaurant-backend -f

# If using PM2
pm2 logs restaurant-backend

# If running manually
# Check the terminal where uvicorn is running
```

**Look for:**
- `INFO: Voice call received`
- `INFO: Processing speech from +15551234567: [transcription]`
- `INFO: Ollama response: [AI response]`

### Common Issues

**Problem:** Call connects but no greeting
**Solution:**
- Check webhook URL is correct
- Verify backend is running
- Check ngrok tunnel is active

**Problem:** AI doesn't respond
**Solution:**
- Check Ollama is running: `curl http://localhost:11434/api/tags`
- Verify OLLAMA_URL in .env
- Check server logs for errors

**Problem:** Speech not transcribed
**Solution:**
- Speak clearly and wait for beep
- Check phone connection quality
- Try shorter sentences

**Problem:** Wrong menu items
**Solution:**
- Verify menu is in database
- Check AI has access to menu
- Review conversation_handler.py line 62-76

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

**Phone Number:** $1/month
**Voice Calls:**
- Incoming: $0.0085/minute
- Outgoing: $0.013/minute

**Speech Recognition (Whisper):**
- $0.02 per minute of audio

**Text-to-Speech:**
- $0.006 per 1000 characters

### Example Monthly Cost

**100 calls/month, 3 minutes average:**
- Phone number: $1.00
- Voice calls: 100 × 3 × $0.0085 = $2.55
- Speech recognition: 100 × 3 × $0.02 = $6.00
- Text-to-speech: ~$0.50
- **Total: ~$10/month**

**Very affordable!** Much cheaper than hiring phone staff.

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
TWILIO_ACCOUNT_SID=AC1234567890abcdef1234567890abcdef
TWILIO_AUTH_TOKEN=your_32_character_auth_token_here
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
