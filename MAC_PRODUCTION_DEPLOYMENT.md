# 🍎 Mac Production Deployment - Complete Guide

**For: Dedicated MacBook Pro M1 16GB as 24/7 server**

**Target: 10-15 restaurants, production-ready**

---

## Prerequisites

✅ MacBook Pro M1 16GB (dedicated server)
✅ macOS up to date
✅ Stable internet connection
✅ Power adapter plugged in
✅ This Mac won't be used for anything else

---

## Step 1: Prevent Sleep & Auto-Updates (15 minutes)

### Keep Mac Awake Forever

```bash
# Prevent sleep when plugged in
sudo pmset -c sleep 0
sudo pmset -c displaysleep 10  # Screen can sleep after 10 min
sudo pmset -c disksleep 0

# Prevent sleep when lid closed (if using external display)
sudo pmset -a lidwake 0

# Disable hibernation
sudo pmset -a hibernatemode 0

# Verify settings
pmset -g
```

### Disable Auto-Updates

```bash
# System Preferences → Software Update → Uncheck:
# - Automatically keep my Mac up to date
# - Download new updates when available

# Or via command line:
sudo defaults write /Library/Preferences/com.apple.SoftwareUpdate AutomaticDownload -bool false
sudo defaults write /Library/Preferences/com.apple.commerce AutoUpdate -bool false
```

### Disable Screen Saver

```bash
# System Preferences → Screen Saver → Start after: Never
defaults -currentHost write com.apple.screensaver idleTime 0
```

### Enable Auto-Login (Optional but Recommended)

```bash
# System Preferences → Users & Groups → Login Options
# Automatic login: [Your User]
```

**Why:** Server needs to restart itself after power outage without manual login.

---

## Step 2: Install PostgreSQL (20 minutes)

### Install via Homebrew

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install PostgreSQL
brew install postgresql@15

# Start PostgreSQL now
brew services start postgresql@15

# Verify it's running
brew services list | grep postgresql
# Should show: postgresql@15  started
```

### Create Database and User

```bash
# Create database
createdb restaurant_ai

# Create user with password
psql postgres -c "CREATE USER restaurant_user WITH PASSWORD 'your_secure_password_here';"

# Grant privileges
psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE restaurant_ai TO restaurant_user;"

# Test connection
psql postgresql://restaurant_user:your_secure_password_here@localhost/restaurant_ai -c "SELECT version();"
```

**Save your password!** You'll need it for the `.env` file.

---

## Step 3: Update Project Configuration (10 minutes)

### Update `.env` File

```bash
cd ~/restaurant-assistant
nano .env
```

**Add/update these settings:**

```bash
# Database (PostgreSQL - PRODUCTION)
DATABASE_URL=postgresql://restaurant_user:your_secure_password_here@localhost/restaurant_ai

# Ollama AI (already running)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Server Config
PORT=8000
HOST=0.0.0.0

# CORS - Add your server's IP and any domain
CORS_ORIGINS=http://localhost:5173,http://YOUR_MAC_IP:5173,https://yourdomain.com

# JWT Secret (generate a strong one)
SECRET_KEY=$(openssl rand -hex 32)

# Twilio (add when ready)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
PUBLIC_URL=

# Stripe (add when ready)
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=

# Platform Settings
PLATFORM_NAME="Restaurant AI Platform"
ADMIN_EMAIL=your-email@example.com
```

**Save:** Ctrl+O, Enter, Ctrl+X

### Find Your Mac's IP Address

```bash
# Get your Mac's local IP
ipconfig getifaddr en0
# Example output: 192.168.1.100

# Or if using WiFi:
ipconfig getifaddr en1
```

**Write this down!** Restaurants will connect to: `http://YOUR_IP:5173`

---

## Step 4: Setup Auto-Start Services (30 minutes)

Mac uses `launchd` (not systemd like Linux). Let's create launch agents.

### Create Backend Service

```bash
# Create launch agent file
cat > ~/Library/LaunchAgents/com.restaurantai.backend.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.restaurantai.backend</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/YOUR_USERNAME/restaurant-assistant/venv/bin/uvicorn</string>
        <string>backend.main:app</string>
        <string>--host</string>
        <string>0.0.0.0</string>
        <string>--port</string>
        <string>8000</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/Users/YOUR_USERNAME/restaurant-assistant</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/Users/YOUR_USERNAME/restaurant-assistant/logs/backend.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/YOUR_USERNAME/restaurant-assistant/logs/backend-error.log</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOF

# Replace YOUR_USERNAME with your actual Mac username
sed -i '' "s/YOUR_USERNAME/$(whoami)/g" ~/Library/LaunchAgents/com.restaurantai.backend.plist

# Create logs directory
mkdir -p ~/restaurant-assistant/logs
```

### Create Frontend Service

```bash
# Build frontend first
cd ~/restaurant-assistant/frontend-new
npm run build

# Install serve globally
npm install -g serve

# Create launch agent
cat > ~/Library/LaunchAgents/com.restaurantai.frontend.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.restaurantai.frontend</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/serve</string>
        <string>-s</string>
        <string>/Users/YOUR_USERNAME/restaurant-assistant/frontend-new/dist</string>
        <string>-l</string>
        <string>5173</string>
        <string>--no-clipboard</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/Users/YOUR_USERNAME/restaurant-assistant/frontend-new</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/Users/YOUR_USERNAME/restaurant-assistant/logs/frontend.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/YOUR_USERNAME/restaurant-assistant/logs/frontend-error.log</string>
</dict>
</plist>
EOF

# Replace YOUR_USERNAME
sed -i '' "s/YOUR_USERNAME/$(whoami)/g" ~/Library/LaunchAgents/com.restaurantai.frontend.plist
```

### Create Ollama Service

```bash
cat > ~/Library/LaunchAgents/com.ollama.service.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ollama.service</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/ollama</string>
        <string>serve</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/Users/YOUR_USERNAME/restaurant-assistant/logs/ollama.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/YOUR_USERNAME/restaurant-assistant/logs/ollama-error.log</string>
</dict>
</plist>
EOF

# Replace YOUR_USERNAME
sed -i '' "s/YOUR_USERNAME/$(whoami)/g" ~/Library/LaunchAgents/com.ollama.service.plist
```

### Load All Services

```bash
# Load services (they'll start automatically)
launchctl load ~/Library/LaunchAgents/com.restaurantai.backend.plist
launchctl load ~/Library/LaunchAgents/com.restaurantai.frontend.plist
launchctl load ~/Library/LaunchAgents/com.ollama.service.plist

# Check if running
launchctl list | grep restaurantai
launchctl list | grep ollama

# Should see:
# - com.restaurantai.backend (PID will be shown)
# - com.restaurantai.frontend (PID will be shown)
# - com.ollama.service (PID will be shown)
```

### Test Services

```bash
# Test backend
curl http://localhost:8000/health

# Test frontend
curl http://localhost:5173

# Test Ollama
curl http://localhost:11434/api/tags

# All should return 200 OK
```

**Services will now:**
- ✅ Start automatically on boot
- ✅ Restart if they crash
- ✅ Run in background forever
- ✅ Log to files

---

## Step 5: Setup Automated Backups (15 minutes)

### Create Backup Script

```bash
# Create backups directory
mkdir -p ~/restaurant-assistant/backups

# Create backup script
cat > ~/restaurant-assistant/backup.sh << 'EOF'
#!/bin/bash
# Restaurant AI Database Backup Script

BACKUP_DIR="$HOME/restaurant-assistant/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/restaurant_ai_$DATE.sql.gz"

# Create backup
pg_dump postgresql://restaurant_user:your_secure_password_here@localhost/restaurant_ai | gzip > "$BACKUP_FILE"

# Keep only last 30 days
find "$BACKUP_DIR" -name "restaurant_ai_*.sql.gz" -mtime +30 -delete

# Log success
echo "$(date): Backup completed: $BACKUP_FILE" >> "$HOME/restaurant-assistant/logs/backup.log"
EOF

# Replace password
nano ~/restaurant-assistant/backup.sh
# Replace "your_secure_password_here" with your actual password

# Make executable
chmod +x ~/restaurant-assistant/backup.sh

# Test it
~/restaurant-assistant/backup.sh

# Check backup was created
ls -lh ~/restaurant-assistant/backups/
```

### Schedule Daily Backups (2 AM)

```bash
# Create launchd plist for backup
cat > ~/Library/LaunchAgents/com.restaurantai.backup.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.restaurantai.backup</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/YOUR_USERNAME/restaurant-assistant/backup.sh</string>
    </array>

    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>2</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>

    <key>StandardOutPath</key>
    <string>/Users/YOUR_USERNAME/restaurant-assistant/logs/backup-cron.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/YOUR_USERNAME/restaurant-assistant/logs/backup-cron-error.log</string>
</dict>
</plist>
EOF

# Replace YOUR_USERNAME
sed -i '' "s/YOUR_USERNAME/$(whoami)/g" ~/Library/LaunchAgents/com.restaurantai.backup.plist

# Load backup schedule
launchctl load ~/Library/LaunchAgents/com.restaurantai.backup.plist
```

**Backups will now run daily at 2 AM automatically.**

---

## Step 6: Configure Firewall (10 minutes)

```bash
# Enable macOS firewall
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on

# Allow incoming connections for Python (backend)
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /Users/$(whoami)/restaurant-assistant/venv/bin/python3
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /Users/$(whoami)/restaurant-assistant/venv/bin/python3

# Allow incoming connections for Node (frontend)
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add /usr/local/bin/node
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --unblockapp /usr/local/bin/node

# Check firewall status
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
```

**Or use GUI:**
- System Preferences → Security & Privacy → Firewall
- Click "Firewall Options"
- Add Python and Node to allowed apps

---

## Step 7: Network Configuration (10 minutes)

### Reserve Static IP (Router Settings)

**Why:** Mac's IP shouldn't change (restaurants bookmark it)

1. Open router admin (usually http://192.168.1.1)
2. Find DHCP Reservations or Static IP
3. Reserve current IP for Mac's MAC address
4. Reboot router if needed

### Enable Port Forwarding (If Accessing from Internet)

**Only if restaurants access from outside your network:**

1. Router admin → Port Forwarding
2. Forward ports:
   - External 8000 → Mac IP:8000 (Backend)
   - External 5173 → Mac IP:5173 (Frontend)
3. Get public IP: `curl ifconfig.me`
4. Restaurants access: `http://YOUR_PUBLIC_IP:5173`

**Security note:** Only do this if you add HTTPS later!

---

## Step 8: Setup Monitoring (20 minutes)

### Install Monitoring Tools

```bash
# Install htop (system monitoring)
brew install htop

# Install lnav (log viewer)
brew install lnav
```

### Create Health Check Script

```bash
cat > ~/restaurant-assistant/healthcheck.sh << 'EOF'
#!/bin/bash
# Health check script - runs every 5 minutes

LOG_FILE="$HOME/restaurant-assistant/logs/healthcheck.log"

# Check backend
if curl -sf http://localhost:8000/health > /dev/null; then
    echo "$(date): Backend OK" >> "$LOG_FILE"
else
    echo "$(date): Backend DOWN - Restarting" >> "$LOG_FILE"
    launchctl kickstart -k gui/$(id -u)/com.restaurantai.backend
fi

# Check frontend
if curl -sf http://localhost:5173 > /dev/null; then
    echo "$(date): Frontend OK" >> "$LOG_FILE"
else
    echo "$(date): Frontend DOWN - Restarting" >> "$LOG_FILE"
    launchctl kickstart -k gui/$(id -u)/com.restaurantai.frontend
fi

# Check Ollama
if curl -sf http://localhost:11434/api/tags > /dev/null; then
    echo "$(date): Ollama OK" >> "$LOG_FILE"
else
    echo "$(date): Ollama DOWN - Restarting" >> "$LOG_FILE"
    launchctl kickstart -k gui/$(id -u)/com.ollama.service
fi

# Check database
if pg_isready -h localhost > /dev/null 2>&1; then
    echo "$(date): Database OK" >> "$LOG_FILE"
else
    echo "$(date): Database DOWN - Check PostgreSQL" >> "$LOG_FILE"
fi
EOF

chmod +x ~/restaurant-assistant/healthcheck.sh
```

### Schedule Health Checks (Every 5 Minutes)

```bash
cat > ~/Library/LaunchAgents/com.restaurantai.healthcheck.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.restaurantai.healthcheck</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/YOUR_USERNAME/restaurant-assistant/healthcheck.sh</string>
    </array>

    <key>StartInterval</key>
    <integer>300</integer>

    <key>StandardOutPath</key>
    <string>/dev/null</string>

    <key>StandardErrorPath</key>
    <string>/Users/YOUR_USERNAME/restaurant-assistant/logs/healthcheck-error.log</string>
</dict>
</plist>
EOF

sed -i '' "s/YOUR_USERNAME/$(whoami)/g" ~/Library/LaunchAgents/com.restaurantai.healthcheck.plist
launchctl load ~/Library/LaunchAgents/com.restaurantai.healthcheck.plist
```

---

## Step 9: Setup External Monitoring (15 minutes)

### Option 1: UptimeRobot (FREE)

1. Go to https://uptimerobot.com
2. Sign up (free account)
3. Add monitor:
   - Type: HTTP(s)
   - URL: http://YOUR_PUBLIC_IP:8000/health
   - Interval: 5 minutes
4. Add email/SMS alerts

### Option 2: Better Uptime (FREE)

1. Go to https://betteruptime.com
2. Sign up
3. Add monitor with your API endpoint
4. Get Slack/Discord/Email alerts

**You'll get notified immediately if server goes down.**

---

## Step 10: Performance Tuning for M1 (10 minutes)

### Optimize PostgreSQL for M1

```bash
# Edit PostgreSQL config
nano /opt/homebrew/var/postgresql@15/postgresql.conf
```

**Add/update these settings:**

```conf
# Memory settings for 16GB Mac (use ~4GB for PostgreSQL)
shared_buffers = 1GB
effective_cache_size = 4GB
maintenance_work_mem = 256MB
work_mem = 16MB

# Connections
max_connections = 100

# Performance
random_page_cost = 1.1  # SSD optimization
effective_io_concurrency = 200
```

**Restart PostgreSQL:**

```bash
brew services restart postgresql@15
```

### Optimize Ollama for M1

```bash
# M1 is already optimized for Ollama!
# Just ensure using GPU acceleration:

ollama pull llama2:latest
# Verify using Metal GPU:
# Should see "Using Metal" in logs
```

---

## Step 11: Testing Everything (15 minutes)

### Test Auto-Start

```bash
# Reboot Mac
sudo reboot

# After reboot, wait 2 minutes, then check:
curl http://localhost:8000/health
curl http://localhost:5173
curl http://localhost:11434/api/tags

# Check services are running
launchctl list | grep restaurantai
launchctl list | grep ollama

# All should show PIDs (running)
```

### Test Database Migration

```bash
# Backend should auto-create tables
cd ~/restaurant-assistant
source venv/bin/activate
python -c "from backend.database import init_db; init_db()"

# Check tables exist
psql postgresql://restaurant_user:your_password@localhost/restaurant_ai -c "\dt"
```

### Test from Another Device

```bash
# From another computer/phone on same network:
# Open browser, go to:
http://YOUR_MAC_IP:5173

# Should see login page
```

### Load Test

```bash
# Install hey (HTTP load tester)
brew install hey

# Test backend can handle load
hey -n 1000 -c 10 http://localhost:8000/health

# Should handle 1000 requests easily
```

---

## Step 12: Access URLs for Restaurants

### Local Network Access

**Give restaurants this URL:**
```
http://YOUR_MAC_IP:5173
```

**Example:** `http://192.168.1.100:5173`

### Internet Access (Optional)

**Option 1: Port Forwarding**
- Forward router ports
- Access via: `http://YOUR_PUBLIC_IP:5173`
- **Insecure** - only for testing

**Option 2: Cloudflare Tunnel (Recommended)**
```bash
# Install cloudflared
brew install cloudflare/cloudflare/cloudflared

# Login
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create restaurant-ai

# Configure
cat > ~/.cloudflared/config.yml << EOF
tunnel: YOUR_TUNNEL_ID
credentials-file: /Users/$(whoami)/.cloudflared/YOUR_TUNNEL_ID.json

ingress:
  - hostname: api.yourdomain.com
    service: http://localhost:8000
  - hostname: app.yourdomain.com
    service: http://localhost:5173
  - service: http_status:404
EOF

# Run tunnel
cloudflared tunnel run restaurant-ai
```

**Result:** HTTPS URLs without port numbers!
- `https://app.yourdomain.com` (Frontend)
- `https://api.yourdomain.com` (Backend)

---

## Management Commands

### View Logs

```bash
# Backend logs
tail -f ~/restaurant-assistant/logs/backend.log

# Frontend logs
tail -f ~/restaurant-assistant/logs/frontend.log

# Ollama logs
tail -f ~/restaurant-assistant/logs/ollama.log

# All logs together (nice viewer)
lnav ~/restaurant-assistant/logs/
```

### Restart Services

```bash
# Restart backend
launchctl kickstart -k gui/$(id -u)/com.restaurantai.backend

# Restart frontend
launchctl kickstart -k gui/$(id -u)/com.restaurantai.frontend

# Restart Ollama
launchctl kickstart -k gui/$(id -u)/com.ollama.service

# Restart all
launchctl kickstart -k gui/$(id -u)/com.restaurantai.backend
launchctl kickstart -k gui/$(id -u)/com.restaurantai.frontend
launchctl kickstart -k gui/$(id -u)/com.ollama.service
```

### Stop Services

```bash
launchctl unload ~/Library/LaunchAgents/com.restaurantai.backend.plist
launchctl unload ~/Library/LaunchAgents/com.restaurantai.frontend.plist
launchctl unload ~/Library/LaunchAgents/com.ollama.service.plist
```

### Check System Resources

```bash
# CPU/Memory usage
htop

# Database size
psql postgresql://restaurant_user:password@localhost/restaurant_ai -c "SELECT pg_size_pretty(pg_database_size('restaurant_ai'));"

# Disk space
df -h

# Network connections
lsof -i :8000
lsof -i :5173
lsof -i :11434
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
cat ~/restaurant-assistant/logs/backend-error.log
cat ~/restaurant-assistant/logs/frontend-error.log

# Check if port is already in use
lsof -i :8000
lsof -i :5173

# Kill process using port
kill -9 <PID>

# Restart service
launchctl kickstart -k gui/$(id -u)/com.restaurantai.backend
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
brew services list | grep postgresql

# Restart PostgreSQL
brew services restart postgresql@15

# Test connection
psql postgresql://restaurant_user:password@localhost/restaurant_ai -c "SELECT 1;"
```

### Can't Access from Other Devices

```bash
# Check firewall allows connections
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --listapps

# Check Mac IP hasn't changed
ipconfig getifaddr en0

# Check services are listening on 0.0.0.0 (not 127.0.0.1)
lsof -i :8000 | grep LISTEN
# Should show: *:8000 (not localhost:8000)
```

### High CPU Usage

```bash
# Check what's using CPU
top -o cpu

# Check Ollama isn't processing multiple requests
curl http://localhost:11434/api/tags

# Check database query performance
psql restaurant_ai -c "SELECT * FROM pg_stat_activity;"
```

---

## Performance Expectations (M1 16GB)

### Single Restaurant:
- API response time: 10-50ms
- Database queries: 5-20ms
- Ollama AI response: 1-3 seconds
- Concurrent users: 20-50 easily

### 10 Restaurants:
- API response time: 10-50ms (same)
- Database queries: 10-30ms
- Ollama AI: 2-3 concurrent calls (queue if more)
- Total concurrent users: 100-200
- **No noticeable slowdown**

### Resource Usage (10 Restaurants):
- CPU: 10-30% average, 50-70% during AI calls
- RAM: 8-10GB used (Ollama: 4GB, PostgreSQL: 1GB, Rest: 3-5GB)
- Disk: 500MB-2GB (database grows with orders)
- Network: Minimal (local network)

**Your M1 can handle this easily!** 💪

---

## Security Checklist

- [x] PostgreSQL requires password
- [x] Firewall configured
- [ ] TODO: Add HTTPS (required for internet access)
- [ ] TODO: Add rate limiting
- [ ] TODO: Add JWT secret rotation
- [x] Backups automated
- [x] Services auto-restart
- [x] Logs monitored

---

## Maintenance Schedule

### Daily (Automated):
- ✅ Database backup (2 AM)
- ✅ Health checks (every 5 min)
- ✅ Log rotation (built-in)

### Weekly (Manual):
```bash
# Check disk space
df -h

# Check backup sizes
ls -lh ~/restaurant-assistant/backups/

# Review error logs
tail -100 ~/restaurant-assistant/logs/backend-error.log
tail -100 ~/restaurant-assistant/logs/healthcheck.log
```

### Monthly (Manual):
```bash
# Update system
brew update && brew upgrade

# Check PostgreSQL performance
psql restaurant_ai -c "VACUUM ANALYZE;"

# Review old backups (auto-deleted after 30 days)
ls -lh ~/restaurant-assistant/backups/
```

---

## Production Checklist

Before onboarding restaurants:

- [ ] Mac configured to never sleep
- [ ] PostgreSQL installed and running
- [ ] All services auto-start on boot
- [ ] Tested reboot (everything comes back)
- [ ] Daily backups scheduled and tested
- [ ] Health checks running
- [ ] External monitoring configured (UptimeRobot)
- [ ] Static IP reserved in router
- [ ] Restaurants can access from their devices
- [ ] Test order/reservation flow works
- [ ] Ollama AI responds to test calls
- [ ] Logs are being written
- [ ] Firewall configured
- [ ] .env file has all settings

---

## Cost Summary

### One-time:
- $0 (using existing Mac)

### Monthly:
- Electricity: ~$5-10
- Internet: $0 (existing)
- External monitoring: $0 (free tier)
- **Total: $5-10/month**

**To run 10 restaurants!** 🚀

---

## Next Steps

1. **Run this deployment** (2-3 hours)
2. **Test with dummy restaurant** (30 minutes)
3. **Onboard first real restaurant** (beta test)
4. **Monitor for 1 week**
5. **Onboard remaining restaurants**

---

## Support

**Check status:**
```bash
curl http://localhost:8000/health
curl http://localhost:5173
```

**View all logs:**
```bash
lnav ~/restaurant-assistant/logs/
```

**Emergency restart:**
```bash
sudo reboot
```

**Everything documented here!**

---

**Your M1 Mac is now a production-grade restaurant AI server!** 🍎🚀
