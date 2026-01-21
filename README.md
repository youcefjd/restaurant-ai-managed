# 🍽️ Restaurant AI Platform - Complete Multi-Tenant Solution

**AI-powered restaurant management system with voice ordering, reservations, payments, and kitchen management.**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org/)
[![Gemini](https://img.shields.io/badge/AI-Gemini-blue.svg)](https://ai.google.dev/)

---

## 🎯 What This Platform Does

**For Platform Admins:**
- Manage multiple restaurants from one dashboard
- Real-time analytics across all locations
- Revenue tracking and commission management
- User management and access control

**For Restaurant Owners:**
- **AI Phone Assistant** - Automated call handling and order taking (Twilio + Gemini)
- **Menu Management** - Interactive menu with real-time availability toggles
- **Table Reservations** - Automatic booking and table assignment
- **Order Management** - Takeout, delivery, and dine-in orders
- **Kitchen Display** - Clean order view for chefs
- **Payment Processing** - Stripe Connect integration
- **Analytics Dashboard** - Revenue tracking and insights

**For Customers:**
- Call restaurant and talk to AI assistant
- Order takeout/delivery by phone
- Make reservations by phone
- View menu online (future feature)

---

## ✨ Key Features

### 🤖 AI with Google Gemini
- Powered by Google Gemini Flash/Exp models
- Understands menu questions, takes orders, makes reservations
- Fast response times (1-3 seconds)
- Requires GOOGLE_AI_API_KEY (free tier available)

### 📞 AI Phone Assistant (Twilio Integration)
- Answers calls automatically
- Speech-to-text with Twilio Whisper
- Natural conversation handling
- Order processing and confirmation
- Reservation booking
- SMS confirmations

### 🪑 Smart Table Management
- Real-time availability tracking
- Automatic table assignment based on party size
- Time-based conflict detection
- Simple setup (just number + capacity)

### 🍔 Interactive Menu System
- Toggle items available/unavailable instantly
- Handle ingredient shortages on the fly
- Time-based availability (breakfast items, etc.)
- Categorized menu organization

### 📊 Modern Dashboard UI
- Colorful, gradient-based design
- Interactive charts (Area, Bar, Pie)
- Touch-optimized for tablets
- Real-time data updates
- Mobile responsive

### 💳 Payment Processing
- Stripe Connect integration
- Platform commission handling (10%)
- Automatic payouts to restaurants
- Payment tracking and analytics

---

## 🚀 Quick Start

### For Technical Person (Server Setup)

**See complete guide:** [`SERVER_SETUP_GUIDE.md`](SERVER_SETUP_GUIDE.md)

**Quick version:**
```bash
# 1. Install dependencies
brew install python@3.12 node git  # Mac
curl https://ollama.ai/install.sh | sh

# 2. Clone repository
git clone https://github.com/youcefjd/restaurant-ai-managed.git
cd restaurant-ai-managed

# 3. Setup environment variables
# Create .env file with GOOGLE_AI_API_KEY (see .env.example)

# 4. Setup backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Edit with your settings
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 5. Setup frontend (new terminal)
cd frontend
npm install
npm run dev
```

**Access:**
- Frontend: http://YOUR_SERVER_IP:3000
- Backend API: http://YOUR_SERVER_IP:8000
- API Docs: http://YOUR_SERVER_IP:8000/api/docs

### For Restaurant Owners (Using the System)

**See complete guide:** [`RESTAURANT_OWNER_GUIDE.md`](RESTAURANT_OWNER_GUIDE.md)

**Quick version:**
1. Open browser on tablet/phone/laptop
2. Go to: `http://SERVER_IP:3000`
3. Create account (30-day free trial)
4. Add your menu
5. Setup tables
6. Start taking orders!

### For AI Phone Assistant Setup

**See complete guide:** [`TWILIO_VOICE_SETUP.md`](TWILIO_VOICE_SETUP.md)

**Where to put Twilio API keys:**
```bash
# Edit this file on your server:
~/restaurant-ai-managed/.env

# Add these lines:
# Note: Each restaurant sets their own phone number in Settings
# These credentials are only for making Twilio API calls
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
PUBLIC_URL=https://your-ngrok-url.ngrok.io

# Restart backend
sudo systemctl restart restaurant-backend
```

**Cost:** ~$10-20/month for typical restaurant call volume

---

## 📚 Documentation

| Document | Audience | Purpose |
|----------|----------|---------|
| [SERVER_SETUP_GUIDE.md](SERVER_SETUP_GUIDE.md) | Technical person | Complete server installation and configuration |
| [RESTAURANT_OWNER_GUIDE.md](RESTAURANT_OWNER_GUIDE.md) | Restaurant owners | How to use the system (non-technical) |
| [TWILIO_VOICE_SETUP.md](TWILIO_VOICE_SETUP.md) | Technical person | AI phone assistant setup with Twilio |
| [NEW_FEATURES_OLLAMA.md](NEW_FEATURES_OLLAMA.md) | Developers | Latest features and API endpoints |
| [END_TO_END_TEST_REPORT.md](END_TO_END_TEST_REPORT.md) | All | Test results and feature validation |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Customer Devices                      │
│         (Phone, Tablet, Laptop, Mobile)                  │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌──────────────────┐
│  Phone Calls    │    │   Web Browser    │
│  (Twilio)       │    │   (React App)    │
└────────┬────────┘    └────────┬─────────┘
         │                      │
         │                      │
         ▼                      ▼
┌─────────────────────────────────────────┐
│         FastAPI Backend (Port 8000)      │
│                                          │
│  ├─ Authentication (JWT)                │
│  ├─ Multi-tenant Restaurant API         │
│  ├─ Order Management                    │
│  ├─ Reservation System                  │
│  ├─ Payment Processing (Stripe)         │
│  └─ Voice Webhooks (Twilio)             │
└──────────┬──────────────────┬───────────┘
           │                  │
           ▼                  ▼
    ┌─────────────┐   ┌──────────────┐
    │   Gemini    │   │   Database   │
    │  (AI LLM)   │   │   (SQLite/   │
    │ Port 11434  │   │  PostgreSQL) │
    └─────────────┘   └──────────────┘
```

### Tech Stack

**Backend:**
- **Framework:** FastAPI (Python 3.12+)
- **Database:** SQLite (development) / PostgreSQL (production)
- **ORM:** SQLAlchemy
- **Authentication:** JWT tokens
- **AI:** Google Gemini (with OpenAI fallback)
- **Payments:** Stripe Connect
- **Voice:** Twilio Voice + Whisper (speech-to-text)

**Frontend:**
- **Framework:** React 18 + TypeScript
- **Build Tool:** Vite
- **Styling:** TailwindCSS (custom design system)
- **Charts:** Recharts
- **Routing:** React Router v6
- **State:** React Hooks + Context

**Infrastructure:**
- **Deployment:** Systemd, PM2, or Docker
- **Reverse Proxy:** Nginx (production)
- **SSL:** Let's Encrypt (Certbot)
- **Tunneling:** Ngrok (development webhooks)

---

## 🔐 Environment Variables

Create `.env` file in project root:

```bash
# Database
DATABASE_URL=sqlite:///./restaurant_reservations.db
# Production: postgresql://user:pass@localhost/restaurant_ai

# Google Gemini AI (Required for conversation handling and menu parsing)
GOOGLE_AI_API_KEY=your_google_ai_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp  # Optional, defaults to gemini-2.0-flash-exp

# Twilio (Required for AI phone assistant and SMS)
# Note: Each restaurant sets their own phone number in Settings
# These credentials are only for making Twilio API calls
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here

# Stripe Payments (Optional)
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxxxxxxxxx

# Google Maps (Optional - for importing operating hours from Google Maps)
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here

# Server Config
PORT=8000
PUBLIC_URL=https://your-domain.com
CORS_ORIGINS=http://localhost:3000,http://192.168.1.100:3000

# JWT Secret (generate with: openssl rand -hex 32)
SECRET_KEY=your_secret_key_here
```

---

## 📦 Project Structure

```
restaurant-ai-managed/
├── backend/
│   ├── api/               # API endpoints
│   │   ├── admin.py       # Admin routes
│   │   ├── auth.py        # Authentication
│   │   ├── onboarding.py  # Restaurant onboarding
│   │   ├── orders.py      # Order management
│   │   ├── reservations.py # Booking system
│   │   ├── tables.py      # Table management
│   │   └── voice.py       # Twilio voice webhooks
│   ├── models.py          # Database models
│   ├── schemas.py         # Pydantic schemas
│   ├── database.py        # Database connection
│   ├── services/          # Business logic
│   │   ├── conversation_handler.py  # Gemini/OpenAI AI integration
│   │   ├── menu_parser.py           # Gemini-powered menu parsing
│   │   └── voice_service.py         # Twilio TwiML generation
│   └── main.py            # FastAPI application
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── layouts/   # Admin & Restaurant layouts
│   │   │   └── ui/        # Reusable components
│   │   ├── pages/
│   │   │   ├── admin/     # Admin dashboard & management
│   │   │   └── restaurant/ # Restaurant dashboard & features
│   │   ├── services/
│   │   │   └── api.ts     # API client
│   │   └── App.tsx        # Main app component
│   ├── tailwind.config.js # Design system
│   └── package.json
│
├── .env                   # Environment variables (create this!)
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── SERVER_SETUP_GUIDE.md
├── RESTAURANT_OWNER_GUIDE.md
├── TWILIO_VOICE_SETUP.md
└── NEW_FEATURES_OLLAMA.md
```

---

## 🔧 API Endpoints

**Base URL:** `http://localhost:8000`

### Authentication
- `POST /api/auth/token` - Login
- `POST /api/auth/register` - Register restaurant account

### Admin
- `GET /api/admin/dashboard` - Admin statistics
- `GET /api/admin/restaurants` - List all restaurants
- `POST /api/admin/create-admin` - Create admin user

### Restaurant Management
- `GET /api/onboarding/accounts/{id}` - Get restaurant details
- `POST /api/onboarding/create-menu` - Create new menu
- `POST /api/onboarding/menu-items` - Add menu item
- `PATCH /api/onboarding/items/{id}/availability` - Toggle item availability

### Tables & Reservations
- `GET /api/{restaurant_id}/tables` - List tables
- `GET /api/{restaurant_id}/tables/availability/count` - Check availability
- `POST /api/{restaurant_id}/tables` - Create table
- `POST /api/{restaurant_id}/bookings` - Create reservation

### Orders
- `POST /api/{restaurant_id}/orders` - Create order
- `GET /api/{restaurant_id}/orders` - List orders
- `PATCH /api/{restaurant_id}/orders/{id}/status` - Update order status

### Voice (Twilio Webhooks)
- `POST /api/voice/welcome` - Initial call greeting
- `POST /api/voice/process` - Process customer speech
- `POST /api/voice/status` - Call status updates

**Full API Documentation:** http://localhost:8000/api/docs

---

## 🧪 Testing

### End-to-End Test Results
See [`END_TO_END_TEST_REPORT.md`](END_TO_END_TEST_REPORT.md) for complete test coverage.

**Test Summary:**
- ✅ Restaurant onboarding
- ✅ Menu creation and management
- ✅ Takeout orders
- ✅ Table reservations
- ✅ Kitchen display
- ✅ Real-time availability
- ✅ Menu item toggles
- ⚠️ AI conversations (requires GOOGLE_AI_API_KEY)
- ⚠️ Phone system (requires Twilio)
- ⚠️ Payments (requires Stripe)

### Run Tests
```bash
# Backend tests
pytest

# Frontend tests
cd frontend
npm test

# Test AI integration
python3 test_ai_conversation.py

# Test API endpoints
curl http://localhost:8000/health
```

---

## 💰 Cost Breakdown

### Server Costs (One-time + Monthly)
- **Server Hardware:** $500-1000 (Mac Mini, NUC, or used laptop)
- **Electricity:** ~$5-10/month
- **Internet:** Existing connection (or $50/month for business line)

### Optional Services (Per Restaurant)
- **Twilio Phone Number:** $1/month
- **Twilio Voice Calls:** ~$0.03/minute (incoming + speech recognition)
- **Twilio SMS:** $0.0075/message
- **Stripe Processing:** 2.9% + $0.30 per transaction
- **Domain Name:** $12/year (optional)
- **SSL Certificate:** Free (Let's Encrypt)

**Example Monthly Cost (100 calls, $3000 revenue):**
- Phone number: $1
- Voice calls (100 × 3 min × $0.03): $9
- SMS confirmations (100 × $0.0075): $0.75
- Stripe fees (2.9% of $3000): $87
- **Total: ~$100/month**
- **Restaurant keeps: $2,913**
- **Platform commission (10%): $300**

---

## 🚀 Deployment

### Development (Local Testing)
```bash
# Backend
uvicorn backend.main:app --reload

# Frontend
cd frontend && npm run dev
```

### Production (Linux Server)

**1. Use Systemd Services:**
See [`SERVER_SETUP_GUIDE.md`](SERVER_SETUP_GUIDE.md) for complete systemd setup.

**2. Or use PM2:**
```bash
pm2 start "uvicorn backend.main:app --host 0.0.0.0" --name restaurant-backend
cd frontend && pm2 start "npm run preview" --name restaurant-frontend
pm2 save
pm2 startup
```

**3. Setup Nginx Reverse Proxy:**
```nginx
server {
    listen 80;
    server_name myrestaurant.com;

    location / {
        proxy_pass http://localhost:3000;
    }

    location /api {
        proxy_pass http://localhost:8000;
    }
}
```

**4. Get SSL Certificate:**
```bash
sudo certbot --nginx -d myrestaurant.com
```

---

## 📱 Multi-Device Usage

### Server Computer
- Runs backend and frontend (requires GOOGLE_AI_API_KEY)
- Always on and connected to internet
- Can be any Mac/Linux computer with 8GB+ RAM

### Restaurant Tablet (Recommended)
- Access: `http://SERVER_IP:3000`
- Keep at counter for order taking
- Large screen, easy to use
- Touch-optimized interface

### Owner's Phone
- Check orders on the go
- Update menu availability
- View reservations
- Respond to customer needs

### Customer's Phone
- Call restaurant number
- AI answers automatically
- Place orders by voice
- Make reservations

**All devices see the same real-time data!**

---

## 🔒 Security

- **JWT Authentication** - Secure token-based auth
- **Password Hashing** - Bcrypt with salt
- **HTTPS** - SSL encryption (production)
- **Request Validation** - Twilio signature verification
- **Environment Variables** - Secrets not in code
- **Database Isolation** - Multi-tenant data separation
- **CORS Configuration** - Restricted origins

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check Python version
python3 --version  # Should be 3.12+

# Check virtual environment
source venv/bin/activate
pip install -r requirements.txt

# Check .env file exists
ls -la .env
```

### Frontend shows blank page
```bash
# Check Node version
node --version  # Should be 18+

# Rebuild
cd frontend
rm -rf node_modules dist
npm install
npm run build

# Check API URL in src/services/api.ts
```

### Ollama not responding
```bash
# Check if running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve &

# Pull model
ollama pull llama2
```

### Can't access from other devices
```bash
# Check firewall
sudo ufw status  # Linux
# Allow ports 8000 and 3000

# Check server is listening on 0.0.0.0
lsof -i :8000
lsof -i :3000
```

---

## 🤝 Contributing

This is a private restaurant platform. For feature requests or bug reports, contact the development team.

---

## 📄 License

Proprietary - All rights reserved

---

## 🆘 Support

**Technical Issues:**
- Check troubleshooting sections in guides
- Review API documentation: http://localhost:8000/api/docs
- Check server logs: `journalctl -u restaurant-backend -f`

**Restaurant Owner Questions:**
- See [`RESTAURANT_OWNER_GUIDE.md`](RESTAURANT_OWNER_GUIDE.md)
- Contact platform admin

**Twilio/Voice Issues:**
- See [`TWILIO_VOICE_SETUP.md`](TWILIO_VOICE_SETUP.md)
- Check Twilio console logs

---

## 📊 Platform Statistics

**Current Features:**
- ✅ Multi-tenant architecture
- ✅ Admin dashboard with analytics
- ✅ Restaurant management dashboard
- ✅ Menu management with real-time toggles
- ✅ Table and reservation system
- ✅ Order management (takeout/delivery/dine-in)
- ✅ Kitchen display
- ✅ AI conversation handling (Gemini)
- ✅ Voice assistant (Twilio + Whisper)
- ✅ Payment processing (Stripe Connect)
- ✅ JWT authentication
- ✅ Real-time availability tracking

**Future Enhancements:**
- Customer-facing ordering website
- Mobile apps (iOS/Android)
- Advanced analytics and reporting
- Inventory management
- Staff scheduling
- Multi-location management
- Loyalty programs
- Marketing integrations

---

## 🎉 Getting Started

1. **Technical person:** Follow [`SERVER_SETUP_GUIDE.md`](SERVER_SETUP_GUIDE.md)
2. **Restaurant owner:** Follow [`RESTAURANT_OWNER_GUIDE.md`](RESTAURANT_OWNER_GUIDE.md)
3. **Enable phone assistant:** Follow [`TWILIO_VOICE_SETUP.md`](TWILIO_VOICE_SETUP.md)

**Questions?** Check the documentation files above!

---

**Made with ❤️ for restaurants who want to leverage AI without the complexity**
