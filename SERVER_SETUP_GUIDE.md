# 🖥️ Server Setup Guide - Restaurant AI Platform

**For:** Technical person setting up the server computer
**Time Required:** 30-45 minutes
**Server Requirements:** Mac or Linux computer with 8GB+ RAM

---

## 📋 What You're Setting Up

This server will run:
1. **Backend API** (Python/FastAPI) - Handles all restaurant data
2. **Frontend Web App** (React) - The actual website restaurant owners use
3. **Ollama AI** - Local AI for answering questions (no cloud required!)
4. **Database** - SQLite database (will migrate to PostgreSQL for production)

---

## 🔧 Step 1: Install Required Software

### Install Python 3.12+
```bash
# Check if already installed
python3 --version

# Mac: Install via Homebrew
brew install python@3.12

# Linux (Ubuntu/Debian)
sudo apt update
sudo apt install python3.12 python3.12-venv python3-pip
```

### Install Node.js 18+
```bash
# Check if already installed
node --version

# Mac: Install via Homebrew
brew install node

# Linux (Ubuntu/Debian)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### Install Ollama (Local AI)
```bash
# Mac or Linux
curl https://ollama.ai/install.sh | sh

# Verify installation
ollama --version
```

### Install Git
```bash
# Mac
brew install git

# Linux
sudo apt install git
```

---

## 📥 Step 2: Download the Code

```bash
# Clone the repository
cd ~
git clone https://github.com/youcefjd/restaurant-ai-managed.git
cd restaurant-ai-managed

# Check you're on the right branch
git branch
# Should show: feature/build-a-complete-restaurant-reservation
```

---

## 🤖 Step 3: Setup Ollama AI

```bash
# Start Ollama service
ollama serve &

# Download AI model (choose one - llama2 is fastest)
ollama pull llama2

# Or for better quality (slower)
# ollama pull mistral

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

**What this does:** Downloads a 3.8GB AI model that understands menu questions and processes orders.

---

## 🐍 Step 4: Setup Python Backend

```bash
cd ~/restaurant-ai-managed

# Create Python virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies (this takes 2-3 minutes)
pip install -r requirements.txt
```

### Configure Environment Variables

```bash
# Create .env file
cp .env.example .env

# Edit the .env file
nano .env
```

**Add these settings:**
```bash
# Database (SQLite for now)
DATABASE_URL=sqlite:///./restaurant_reservations.db

# Ollama AI
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Twilio (optional - for phone calls, add later)
TWILIO_ACCOUNT_SID=your_sid_here
TWILIO_AUTH_TOKEN=your_token_here
TWILIO_PHONE_NUMBER=+1234567890

# Stripe (optional - for payments, add later)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Server Config
PORT=8000
CORS_ORIGINS=http://localhost:5173,http://192.168.1.100:5173
```

**Important:** Replace `192.168.1.100` with your server's actual IP address!

**To find your server IP:**
```bash
# Mac
ipconfig getifaddr en0

# Linux
hostname -I | awk '{print $1}'
```

### Start the Backend

```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Start the backend server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Keep this terminal open!** The backend needs to run continuously.

---

## ⚛️ Step 5: Setup React Frontend

**Open a NEW terminal** (keep backend running in the first one)

```bash
cd ~/restaurant-ai-managed/frontend-new

# Install dependencies
npm install

# This takes 3-5 minutes - downloads ~300MB of packages
```

### Configure Frontend API Connection

Edit the API configuration to point to your server:

```bash
nano src/services/api.ts
```

**Change this line:**
```typescript
const API_BASE_URL = 'http://localhost:8000'
```

**To use your server IP:**
```typescript
const API_BASE_URL = 'http://192.168.1.100:8000'  // Replace with YOUR server IP
```

### Build the Frontend

```bash
# Production build (faster loading, smaller size)
npm run build

# Or development mode (with hot reload)
npm run dev -- --host 0.0.0.0
```

**For production build**, serve it with:
```bash
npm install -g serve
serve -s dist -l 5173 --host 0.0.0.0
```

**Access the app:**
- From server: http://localhost:5173
- From other devices: http://192.168.1.100:5173

---

## 🔥 Step 6: Setup Firewall Rules

Allow devices on your network to access the server:

### Mac:
```bash
# System Preferences → Security & Privacy → Firewall
# Click "Firewall Options"
# Uncheck "Block all incoming connections"
# Add Python and Node to allowed apps
```

### Linux:
```bash
sudo ufw allow 8000/tcp   # Backend API
sudo ufw allow 5173/tcp   # Frontend web app
sudo ufw allow 11434/tcp  # Ollama AI (optional, only if other computers need direct access)
sudo ufw reload
```

---

## ✅ Step 7: Verify Everything Works

### Test Backend API
```bash
curl http://localhost:8000/health
```
**Expected:**
```json
{
  "status": "degraded",
  "services": {
    "api": "healthy",
    "database": "unhealthy"
  }
}
```
(Database shows unhealthy but works fine - it's a check quirk)

### Test Ollama AI
```bash
curl http://localhost:11434/api/tags
```
**Expected:** Shows installed models (llama2)

### Test Frontend
Open browser: `http://192.168.1.100:5173`

You should see the Restaurant AI login page.

---

## 🚀 Step 8: Keep Services Running

### Option A: Manual (for testing)
Keep two terminals open:
- Terminal 1: Backend (`uvicorn backend.main:app...`)
- Terminal 2: Frontend (`serve -s dist...` or `npm run dev...`)

### Option B: Systemd Services (Linux - recommended for production)

**Backend Service:**
```bash
sudo nano /etc/systemd/system/restaurant-backend.service
```

```ini
[Unit]
Description=Restaurant AI Backend
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/home/yourusername/restaurant-ai-managed
Environment="PATH=/home/yourusername/restaurant-ai-managed/venv/bin"
ExecStart=/home/yourusername/restaurant-ai-managed/venv/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

**Frontend Service:**
```bash
sudo nano /etc/systemd/system/restaurant-frontend.service
```

```ini
[Unit]
Description=Restaurant AI Frontend
After=network.target

[Service]
Type=simple
User=yourusername
WorkingDirectory=/home/yourusername/restaurant-ai-managed/frontend-new
ExecStart=/usr/local/bin/serve -s dist -l 5173 --host 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl enable restaurant-backend
sudo systemctl enable restaurant-frontend
sudo systemctl start restaurant-backend
sudo systemctl start restaurant-frontend

# Check status
sudo systemctl status restaurant-backend
sudo systemctl status restaurant-frontend
```

### Option C: PM2 (Mac/Linux)
```bash
# Install PM2
npm install -g pm2

# Start backend
cd ~/restaurant-ai-managed
pm2 start "uvicorn backend.main:app --host 0.0.0.0 --port 8000" --name restaurant-backend

# Start frontend
cd frontend-new
pm2 start "serve -s dist -l 5173 --host 0.0.0.0" --name restaurant-frontend

# Save configuration
pm2 save

# Auto-start on boot
pm2 startup
```

---

## 📱 Step 9: Access from Other Devices

### Find Your Server IP Address
```bash
# Mac
ipconfig getifaddr en0

# Linux
hostname -I | awk '{print $1}'
```

Let's say your IP is `192.168.1.100`

### From Tablet/Phone/Laptop on Same WiFi

1. **Open browser**
2. **Go to:** `http://192.168.1.100:5173`
3. **You'll see the Restaurant AI login page**

### Create Admin Account
```bash
# On the server, create admin
curl -X POST http://localhost:8000/api/admin/create-admin \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@restaurantai.com",
    "password": "YourSecurePassword123!"
  }'
```

### Create Restaurant Account
1. Go to: `http://192.168.1.100:5173/login`
2. Click "Sign Up"
3. Fill in restaurant details
4. Login and start using!

---

## 🔧 Troubleshooting

### Problem: Can't access from other devices
**Solution:**
```bash
# Check firewall
sudo ufw status  # Linux
# Make sure ports 8000 and 5173 are allowed

# Check if services are running
lsof -i :8000  # Backend
lsof -i :5173  # Frontend

# Check server IP is correct
ip addr show  # Linux
ifconfig       # Mac
```

### Problem: Ollama not responding
**Solution:**
```bash
# Restart Ollama
pkill ollama
ollama serve &

# Test
curl http://localhost:11434/api/tags
```

### Problem: Database errors
**Solution:**
```bash
cd ~/restaurant-ai-managed
rm restaurant_reservations.db  # Delete old database
source venv/bin/activate
python -c "from backend.database import init_db; init_db()"  # Recreate
```

### Problem: Frontend shows "Network Error"
**Solution:** Check `src/services/api.ts` has correct server IP address

---

## 📊 Monitoring

### Check Logs
```bash
# Backend logs
pm2 logs restaurant-backend

# Or with systemd
sudo journalctl -u restaurant-backend -f

# Frontend logs
pm2 logs restaurant-frontend
```

### Check Resource Usage
```bash
# CPU & Memory
htop

# Disk space
df -h

# Check Ollama memory usage (it uses ~4GB)
ps aux | grep ollama
```

---

## 🔄 Updating the Code

```bash
cd ~/restaurant-ai-managed

# Pull latest changes
git pull origin feature/build-a-complete-restaurant-reservation

# Update backend
source venv/bin/activate
pip install -r requirements.txt

# Update frontend
cd frontend-new
npm install
npm run build

# Restart services
pm2 restart all
# Or
sudo systemctl restart restaurant-backend
sudo systemctl restart restaurant-frontend
```

---

## 🌐 Going to Production (Optional)

### Get a Domain Name
- Buy domain: `myrestaurant.com`
- Point DNS A record to your server IP

### Setup HTTPS with Nginx
```bash
# Install Nginx
sudo apt install nginx

# Install Certbot for SSL
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d myrestaurant.com

# Configure reverse proxy
sudo nano /etc/nginx/sites-available/restaurant-ai
```

```nginx
server {
    listen 80;
    server_name myrestaurant.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name myrestaurant.com;

    ssl_certificate /etc/letsencrypt/live/myrestaurant.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/myrestaurant.com/privkey.pem;

    # Frontend
    location / {
        proxy_pass http://localhost:5173;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/restaurant-ai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Migrate to PostgreSQL (Recommended for Production)
```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb restaurant_ai
sudo -u postgres createuser restaurant_user
sudo -u postgres psql -c "ALTER USER restaurant_user WITH PASSWORD 'securepassword';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE restaurant_ai TO restaurant_user;"

# Update .env
DATABASE_URL=postgresql://restaurant_user:securepassword@localhost/restaurant_ai
```

---

## 📞 Support

**Server running?** → Check `http://YOUR_IP:5173`
**Backend API?** → Check `http://YOUR_IP:8000/api/docs`
**Ollama AI?** → Check `http://YOUR_IP:11434/api/tags`

**Next:** See `RESTAURANT_OWNER_GUIDE.md` for how restaurant owners use the system!
