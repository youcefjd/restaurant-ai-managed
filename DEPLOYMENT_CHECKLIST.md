# 🚀 Final Deployment Checklist - Mac M1 Server

## Overview
This checklist will help you deploy the restaurant AI platform on your MacBook Pro M1 16GB server.

**Estimated time:** 2-3 hours for first-time setup

---

## ✅ Pre-Deployment Checklist

### 1. Hardware & Network
- [ ] Mac is plugged into power (not running on battery)
- [ ] Mac has stable internet connection
- [ ] Mac is on same network you'll access from (or port forwarding is configured)
- [ ] You know the Mac's local IP address (run: `ifconfig | grep "inet " | grep -v 127.0.0.1`)

### 2. Accounts & API Keys
- [ ] Twilio account created
- [ ] Twilio phone number purchased ($1/month per number)
- [ ] Twilio Account SID and Auth Token ready
- [ ] (Optional) Stripe Connect account for payments

---

## 📋 Step-by-Step Deployment

### Phase 1: Server Setup (30 minutes)

**Follow:** `MAC_PRODUCTION_DEPLOYMENT.md` - Steps 1-3

- [ ] Prevent Mac from sleeping: `sudo pmset -c sleep 0`
- [ ] Install Homebrew (if not installed)
- [ ] Install PostgreSQL: `brew install postgresql@15`
- [ ] Start PostgreSQL: `brew services start postgresql@15`
- [ ] Create database: `createdb restaurant_ai`
- [ ] Update `.env` file with PostgreSQL connection string

**Commands:**
```bash
cd ~/restaurant-assistant

# Create .env if it doesn't exist
cat > backend/.env << 'EOF'
DATABASE_URL=postgresql://$(whoami)@localhost/restaurant_ai
SECRET_KEY=$(openssl rand -hex 32)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=your_twilio_number
PUBLIC_URL=http://YOUR_MAC_IP:8000
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama2
ENABLE_PAYMENTS=false
EOF

# Run database migrations
cd backend
source venv/bin/activate
alembic upgrade head
```

---

### Phase 2: Install Ollama (15 minutes)

- [ ] Download Ollama from https://ollama.ai/download/mac
- [ ] Install and open Ollama app
- [ ] Pull the llama2 model: `ollama pull llama2`
- [ ] Verify it's running: `curl http://localhost:11434/api/tags`

**Expected output:**
```json
{"models":[{"name":"llama2:latest",...}]}
```

---

### Phase 3: Setup Auto-Start Services (30 minutes)

**Follow:** `MAC_PRODUCTION_DEPLOYMENT.md` - Step 4

- [ ] Create backend launchd service
- [ ] Create frontend launchd service
- [ ] Create Ollama launchd service
- [ ] Load all services: `launchctl load ~/Library/LaunchAgents/*.restaurantai.*`
- [ ] Verify services are running: `launchctl list | grep restaurantai`

**Quick verification:**
```bash
# Check backend
curl http://localhost:8000/health

# Check frontend (after building)
curl http://localhost:3000

# Check Ollama
curl http://localhost:11434/api/tags
```

---

### Phase 4: Setup Automated Backups (15 minutes)

**Follow:** `MAC_PRODUCTION_DEPLOYMENT.md` - Step 5

- [ ] Create backup script at `~/restaurant-assistant/backup.sh`
- [ ] Make it executable: `chmod +x ~/restaurant-assistant/backup.sh`
- [ ] Test backup manually: `./backup.sh`
- [ ] Create launchd backup service (runs daily at 2 AM)
- [ ] Load backup service

---

### Phase 5: Network & Firewall (20 minutes)

**Follow:** `MAC_PRODUCTION_DEPLOYMENT.md` - Steps 6-7

- [ ] Note Mac's IP address: `ifconfig | grep "inet " | grep -v 127.0.0.1`
- [ ] Update `PUBLIC_URL` in backend/.env to Mac's IP
- [ ] Update frontend to point to Mac's IP
- [ ] Configure Mac firewall to allow ports 8000 and 3000
- [ ] Test access from another device

**Firewall commands:**
```bash
# Enable firewall
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on

# Allow Python (backend)
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/local/bin/python3
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblock /usr/local/bin/python3

# Allow Node (frontend)
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/local/bin/node
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblock /usr/local/bin/node
```

---

### Phase 6: Twilio Configuration (30 minutes)

**Follow:** `TWILIO_VOICE_SETUP.md`

- [ ] Make server publicly accessible (use ngrok for testing)
- [ ] Run: `ngrok http 8000`
- [ ] Copy the ngrok URL (e.g., https://abc123.ngrok.io)
- [ ] Update Twilio webhook:
  - Voice URL: `https://abc123.ngrok.io/api/voice/welcome`
  - Method: POST
- [ ] Test call: Call your Twilio number and verify AI answers

**Important:** For production without ngrok, you'll need:
- Static IP address OR
- Dynamic DNS service (like DuckDNS) OR
- Router port forwarding with your ISP's public IP

---

### Phase 7: Create First Restaurant (15 minutes)

**Follow:** `RESTAURANT_OWNER_GUIDE.md`

- [ ] Access admin dashboard: `http://YOUR_MAC_IP:3000/admin/login`
- [ ] Login with admin credentials
- [ ] Click "Add Restaurant"
- [ ] Fill in restaurant details:
  - Business name
  - Owner email (they'll use this to login)
  - Owner phone
  - Assign Twilio phone number
- [ ] Set subscription tier
- [ ] Set commission settings (or disable commission)

---

### Phase 8: Restaurant Setup (30 minutes)

**Guide restaurant owner through:**

- [ ] Login at `http://YOUR_MAC_IP:3000/restaurant/login`
- [ ] Setup menu (see RESTAURANT_OWNER_GUIDE.md):
  - Create menu categories
  - Add menu items with prices
  - Add modifiers (sizes, extras)
- [ ] Setup tables:
  - Add tables with capacity
  - Mark tables as active
- [ ] Configure settings:
  - Business hours
  - Delivery/takeout options
  - Order preferences

---

### Phase 9: Testing (30 minutes)

**Test everything end-to-end:**

1. **Dashboard Access**
   - [ ] Admin can access admin dashboard
   - [ ] Restaurant can access restaurant dashboard
   - [ ] Both see real-time data

2. **Phone Orders**
   - [ ] Call the Twilio number
   - [ ] AI greets with restaurant name
   - [ ] AI understands menu items
   - [ ] Order appears in dashboard
   - [ ] Kitchen display shows order

3. **Manual Orders**
   - [ ] Create takeout order
   - [ ] Create dine-in order
   - [ ] Update order status
   - [ ] Complete order

4. **Reservations**
   - [ ] Call and request reservation
   - [ ] System checks table availability
   - [ ] Booking appears in dashboard
   - [ ] Table count reduces

5. **Menu Management**
   - [ ] Toggle item availability
   - [ ] Add new item
   - [ ] Edit item price
   - [ ] Changes reflect immediately

---

## 🎯 Production Readiness Verification

### Critical Checks
- [ ] Backend responds: `curl http://YOUR_MAC_IP:8000/health`
- [ ] Frontend loads: Open `http://YOUR_MAC_IP:3000` in browser
- [ ] Ollama running: `curl http://localhost:11434/api/tags`
- [ ] PostgreSQL running: `psql -d restaurant_ai -c "SELECT 1;"`
- [ ] Services auto-start after reboot (test by rebooting Mac)
- [ ] Backups running: Check `~/restaurant-assistant/backups/` for .sql.gz files
- [ ] Phone calls route correctly to respective restaurants

### Performance Checks
- [ ] Dashboard loads in < 2 seconds
- [ ] Menu loads in < 1 second
- [ ] AI responds to phone calls in < 5 seconds
- [ ] Order creation is instant
- [ ] No memory leaks (monitor Activity Monitor)

---

## 📊 Capacity Limits (Mac M1 16GB)

**Your setup can handle:**
- ✅ **10-15 restaurants comfortably** (recommended)
- ⚠️ **20-25 restaurants** (pushing limits)
- ⚠️ **2-3 concurrent phone calls** (Ollama bottleneck)
- ✅ **100+ simultaneous dashboard users**
- ✅ **1000+ orders per day**

**Bottlenecks:**
1. **Ollama** - Can only handle 2-3 calls at once
2. **CPU** - M1 handles this well
3. **RAM** - 16GB is sufficient for 15 restaurants
4. **Storage** - Database grows ~1GB per month per restaurant

---

## 🚨 Troubleshooting

### Backend not starting
```bash
# Check logs
cat ~/Library/Logs/restaurant-backend.log

# Restart manually
cd ~/restaurant-assistant/backend
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend not loading
```bash
# Check logs
cat ~/Library/Logs/restaurant-frontend.log

# Restart manually
cd ~/restaurant-assistant/frontend-new
npm run dev
```

### Ollama not responding
```bash
# Check if running
ps aux | grep ollama

# Restart Ollama app
killall ollama
open -a Ollama
```

### PostgreSQL connection failed
```bash
# Check if running
brew services list | grep postgresql

# Restart PostgreSQL
brew services restart postgresql@15
```

### Phone calls not working
1. Check PUBLIC_URL in .env points to correct IP/domain
2. Verify Twilio webhook is configured correctly
3. Test webhook: `curl -X POST http://YOUR_MAC_IP:8000/api/voice/welcome`
4. Check ngrok is running (if using ngrok)

---

## 📱 Access URLs

After deployment, these URLs will be available:

**From Mac itself:**
- Admin Dashboard: `http://localhost:3000/admin/login`
- Restaurant Dashboard: `http://localhost:3000/restaurant/login`
- API Health: `http://localhost:8000/health`
- API Docs: `http://localhost:8000/docs`

**From tablets/phones on same network:**
- Admin Dashboard: `http://YOUR_MAC_IP:3000/admin/login`
- Restaurant Dashboard: `http://YOUR_MAC_IP:3000/restaurant/login`
- API: `http://YOUR_MAC_IP:8000`

**Replace YOUR_MAC_IP with actual IP address**

---

## 🎉 You're Ready to Launch!

Once all checkboxes are complete:

1. **Onboard your first 2-3 restaurants** (beta testing)
2. **Monitor for 1 week** - Check logs, performance, errors
3. **Collect feedback** - What works, what doesn't
4. **Iterate quickly** - Fix issues, improve UX
5. **Scale gradually** - Add more restaurants slowly

---

## 📚 Reference Documentation

- **Technical Setup:** `MAC_PRODUCTION_DEPLOYMENT.md`
- **Twilio Integration:** `TWILIO_VOICE_SETUP.md`
- **Restaurant Onboarding:** `RESTAURANT_OWNER_GUIDE.md`
- **Commission System:** `COMMISSION_SYSTEM.md`
- **Server Management:** `SERVER_SETUP_GUIDE.md`

---

## 💡 Pro Tips

1. **Start with 3-5 restaurants** - Don't overload initially
2. **Use ngrok for testing** - Switch to permanent solution later
3. **Monitor resource usage** - Keep Activity Monitor open first few days
4. **Test phone system thoroughly** - This is the most critical feature
5. **Have restaurant owners test on their actual tablets** - UX must be perfect
6. **Keep Mac updated** - But test updates on staging environment first
7. **Backup before major changes** - Can't stress this enough

---

## 🆘 Need Help?

If you encounter issues:

1. Check the logs in `~/Library/Logs/restaurant-*.log`
2. Review the troubleshooting section in `MAC_PRODUCTION_DEPLOYMENT.md`
3. Test each component individually (backend, frontend, Ollama, PostgreSQL)
4. Verify network connectivity and firewall settings
5. Check that all environment variables are set correctly

---

**Last updated:** 2026-01-12
**System:** MacBook Pro M1 16GB
**Target capacity:** 10-15 restaurants
**Status:** Production-ready (with Twilio configured)
