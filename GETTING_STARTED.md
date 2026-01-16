# Restaurant AI Assistant - Getting Started Guide

This guide will help you set up and run the Restaurant AI Assistant platform with voice calling capabilities powered by Twilio and Claude AI.

## Prerequisites

- **Python 3.9+** installed
- **Node.js 16+** and npm installed
- **ngrok** account and CLI installed
- **Anthropic API key** (for Claude AI)
- **Twilio account** (for phone calls)

## Architecture Overview

Each Twilio phone number is tied to ONE restaurant account. The AI automatically:
- Greets callers with the restaurant's specific name
- Answers questions about that restaurant's specific menu
- Provides that restaurant's specific operating hours
- Handles reservations for that restaurant's specific tables
- Nothing is hardcoded - all data comes from the database

## Setup Instructions

### 1. Install ngrok

```bash
# macOS
brew install ngrok

# Or download from https://ngrok.com/download

# Authenticate ngrok (get your token from https://dashboard.ngrok.com)
ngrok authtoken YOUR_NGROK_AUTH_TOKEN
```

### 2. Clone and Setup Backend

```bash
cd /Users/youcef/restaurant-assistant

# Create virtual environment (if not already created)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY='your-anthropic-api-key-here'

# Initialize database (if fresh install)
# The database will be created automatically on first run

# Start the backend server
PYTHONPATH=/Users/youcef/restaurant-assistant \
ANTHROPIC_API_KEY='your-anthropic-api-key-here' \
uvicorn backend.main:app --reload --port 8000
```

Backend will be running at: http://localhost:8000

### 3. Start ngrok Tunnel

In a **separate terminal**:

```bash
# Start ngrok tunnel to expose backend to internet
ngrok http 8000
```

You'll see output like:
```
Forwarding   https://abc123def456.ngrok-free.app -> http://localhost:8000
```

**Keep this terminal open** and note your ngrok URL (e.g., `https://abc123def456.ngrok-free.app`).

### 4. Setup Frontend

In a **third terminal**:

```bash
cd frontend-new

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

Frontend will be running at: http://localhost:5173

## Configure Twilio Phone Number

### 1. Log into Twilio Console

Go to: https://console.twilio.com

### 2. Configure Phone Number for Restaurant

1. Navigate to: **Phone Numbers → Manage → Active Numbers**
2. Click on your Twilio phone number (e.g., +18559166538)
3. Scroll to **Voice Configuration** section
4. Set **A CALL COMES IN** to:
   - **Webhook**: `https://YOUR_NGROK_URL/api/voice/welcome`
   - **HTTP Method**: POST
5. Set **STATUS CALLBACK URL** to:
   - **Webhook**: `https://YOUR_NGROK_URL/api/voice/status`
   - **HTTP Method**: POST
6. Click **Save Configuration**

**Important**: Update the webhook URL every time you restart ngrok (the URL changes each time on free plan).

## Create a Restaurant with Voice Assistant

### 1. Login as Platform Admin

Go to http://localhost:5173 and login:
- Email: `admin@platform.com`
- Password: `admin123`

### 2. Create a Restaurant

1. Click **"Restaurants"** in the sidebar
2. Click **"+ Add Restaurant"** button
3. Fill in the form:
   - **Business Name**: (e.g., "Sukhasis Palace")
   - **Owner Email**: (e.g., "owner@restaurant.com")
   - **Owner Password**: Set a password for the restaurant owner
   - **Phone**: Restaurant's public phone number
   - **Twilio Phone Number**: Your Twilio number (e.g., "+18559166538")
   - **Address**: Full address
   - **Opening Time**: (e.g., "11:00")
   - **Closing Time**: (e.g., "22:00")
   - **Operating Days**: Select days (0=Monday, 6=Sunday)
4. Click **"Create Restaurant"**

### 3. Login as Restaurant Owner and Add Menu

1. Logout from platform admin
2. Login with restaurant owner credentials
3. Click **"Menu"** in sidebar
4. Click **"Create Menu"** → Enter menu name (e.g., "Main Menu")
5. Add categories (e.g., "Appetizers", "Main Course", "Desserts")
6. Click **"Add Item"** to add menu items with:
   - Name, description, price
   - Dietary tags (vegetarian, vegan, halal, spicy)
   - Availability toggle

### 4. Add Tables for Reservations (Optional)

1. Click **"Settings"** in sidebar
2. Scroll to **"Table Management"**
3. Add tables with capacity (e.g., Table 1 - 4 seats)

## Test the Voice Assistant

### 1. Call Your Twilio Number

Dial the Twilio phone number you configured (e.g., +18559166538).

### 2. Expected Flow

```
AI: "Hey, thanks for calling [Restaurant Name]. How may I help you?"

You: "Do you have vegetarian options?"

AI: "Great choice! We have several delicious vegetarian options:
     - Palak Paneer ($13.99) - Cottage cheese in spinach sauce
     - Chana Masala ($11.99) - Chickpeas in spicy gravy
     - [more items...]
     Would you like to order any of these?"

You: "What time do you close?"

AI: "We're open from 11:00 AM to 10:00 PM. Is there anything else?"
```

### 3. Monitor Backend Logs

Watch the backend terminal for logs:
```
INFO: Voice call received from +15551234567 to +18559166538
INFO: Using base URL: https://abc123def456.ngrok-free.app
INFO: Anthropic Claude connection configured, using model: claude-sonnet-4-20250514
INFO: Processing speech from +15551234567 to +18559166538: Do you have vegetarian options?
```

## How Restaurant-Specific AI Works

The system automatically personalizes responses for each restaurant:

### 1. Phone Number → Restaurant Mapping

```python
# backend/api/voice.py
restaurant = db.query(RestaurantAccount).filter(
    RestaurantAccount.twilio_phone_number == to_normalized
).first()
```

### 2. Dynamic Menu Loading

```python
# backend/services/conversation_handler.py
menus = db.query(Menu).filter(Menu.account_id == account.id).all()
# Loads ONLY this restaurant's menu items
```

### 3. Restaurant-Specific Greeting

```python
# TwiML generation
f"Hey, thanks for calling {restaurant.business_name}. How may I help you?"
```

### 4. Operating Hours

```python
# AI prompt includes:
f"Hours: {account.opening_time} - {account.closing_time}"
f"Days: {days_str}"
```

### 5. AI Context

The AI receives:
- Restaurant name
- Full menu with prices and dietary info
- Operating hours and days
- Available tables for reservations

**Result**: Each restaurant gets its own AI personality with accurate, specific information.

## Environment Variables

Create a `.env` file or export these:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE

# Optional - defaults work for local development
ANTHROPIC_MODEL=claude-sonnet-4-20250514
DATABASE_URL=sqlite:///./restaurant_reservations.db
CORS_ORIGINS=http://localhost:5173,http://localhost:4173
```

## Troubleshooting

### Backend not starting
```bash
# Check if port 8000 is already in use
lsof -ti:8000 | xargs kill -9

# Restart with proper environment
PYTHONPATH=/Users/youcef/restaurant-assistant \
ANTHROPIC_API_KEY='your-key' \
uvicorn backend.main:app --reload --port 8000
```

### ngrok URL changed
- Restart ngrok to get new URL
- Update Twilio webhook configuration with new URL
- Backend will automatically use correct URL from request headers

### Call says "hi" then hangs up
- Check backend logs for errors
- Verify ngrok is running and forwarding to port 8000
- Confirm Twilio webhook is set correctly
- Check Anthropic API key is valid

### AI responses are slow
- Using Claude Sonnet 4 (5-10 seconds typical)
- For faster responses, upgrade to paid Anthropic tier
- Check network latency to ngrok

### No menu items showing
- Login as restaurant owner
- Create menu and add categories
- Add menu items with prices
- Ensure items are marked as "available"

### AI doesn't know operating hours
- Edit restaurant settings (platform admin)
- Set opening/closing times
- Select operating days
- Save changes

## Production Deployment

For production:

1. **Use persistent ngrok domain**: Upgrade to ngrok paid plan for fixed URL
2. **Set Twilio credentials**: Add to environment variables
3. **Database**: Migrate to PostgreSQL
4. **Redis**: Add for conversation state storage
5. **Monitoring**: Add logging and error tracking
6. **Rate limiting**: Add API rate limits
7. **Authentication**: Use JWT tokens properly

## API Endpoints

### Voice Endpoints
- `POST /api/voice/welcome` - Initial call greeting
- `POST /api/voice/process` - Process speech input
- `POST /api/voice/status` - Call status updates
- `POST /api/voice/sms/incoming` - Handle SMS messages

### Platform Admin
- `POST /api/platform/restaurants` - Create restaurant
- `GET /api/platform/restaurants` - List all restaurants
- `PATCH /api/platform/restaurants/{id}` - Update restaurant

### Restaurant Dashboard
- `GET /api/onboarding/accounts/{id}` - Get restaurant details
- `GET /api/onboarding/accounts/{id}/menu-full` - Get full menu
- `POST /api/onboarding/menus` - Create menu
- `POST /api/onboarding/items` - Add menu item

## Tech Stack

- **Backend**: FastAPI, Python 3.9+
- **Database**: SQLAlchemy with SQLite (dev) / PostgreSQL (prod)
- **AI**: Claude Sonnet 4 via Anthropic API
- **Voice**: Twilio Voice API with Speech Recognition
- **Frontend**: React, TypeScript, Vite, TailwindCSS
- **Tunneling**: ngrok for local development

## Support

- Check backend logs: `tail -f backend.log`
- Check frontend console: Browser DevTools
- View Twilio logs: https://console.twilio.com/monitor/logs
- Test ngrok: Visit `http://localhost:4040` for ngrok inspector

## Next Steps

1. **Add more restaurants** - Each gets its own phone number and AI
2. **Customize AI prompts** - Edit `conversation_handler.py`
3. **Add payment processing** - Integrate Stripe
4. **Enable SMS ordering** - Already supported!
5. **Add online ordering UI** - Customer-facing website
6. **Analytics dashboard** - Track calls, orders, revenue

---

**Need help?** Check the logs, verify your configuration, and ensure all services are running.
