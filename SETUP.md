# ?? Setup & Configuration Guide

Complete guide for installing and configuring the Parental Control Backend Server.

---

## ?? Table of Contents

1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Database Setup](#database-setup)
5. [Telegram Bots Setup](#telegram-bots-setup)
6. [Firebase Setup](#firebase-setup)
7. [Running the Server](#running-the-server)
8. [Docker Deployment](#docker-deployment)
9. [Production Deployment](#production-deployment)
10. [Troubleshooting](#troubleshooting)

---

## ?? System Requirements

### Minimum Requirements
- **OS:** Linux, macOS, or Windows
- **Python:** 3.10 or higher
- **RAM:** 2GB minimum, 4GB recommended
- **Storage:** 10GB minimum
- **MongoDB:** 4.4 or higher

### Recommended for Production
- **RAM:** 8GB+
- **CPU:** 4 cores+
- **Storage:** SSD with 50GB+
- **Network:** Static IP with open ports

---

## ?? Installation

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd workspace
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Verify Installation

```bash
python3 -c "from app.config import settings; print('? Installation successful!')"
```

---

## ?? Configuration

### Step 1: Create .env File

```bash
cp .env.example .env
```

### Step 2: Edit .env File

Open `.env` and configure:

```bash
# =============================================================================
# Database Configuration
# =============================================================================
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=parental_control

# =============================================================================
# Server Configuration
# =============================================================================
SERVER_HOST=0.0.0.0
SERVER_PORT=8765
DEBUG=True

# =============================================================================
# Security & Authentication
# =============================================================================
# Generate secure key: python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=CHANGE_THIS_TO_SECURE_RANDOM_KEY
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# =============================================================================
# 2FA Telegram Bot (Shared for all admins)
# =============================================================================
TELEGRAM_2FA_BOT_TOKEN=YOUR_2FA_BOT_TOKEN_HERE
TELEGRAM_2FA_CHAT_ID=YOUR_2FA_CHAT_ID_HERE

# =============================================================================
# Administrator's 5 Telegram Bots
# =============================================================================
# Bot 1: Device notifications
ADMIN_BOT1_TOKEN=YOUR_BOT1_TOKEN_HERE
ADMIN_BOT1_CHAT_ID=YOUR_BOT1_CHAT_ID_HERE

# Bot 2: SMS notifications
ADMIN_BOT2_TOKEN=YOUR_BOT2_TOKEN_HERE
ADMIN_BOT2_CHAT_ID=YOUR_BOT2_CHAT_ID_HERE

# Bot 3: Admin activity logs
ADMIN_BOT3_TOKEN=YOUR_BOT3_TOKEN_HERE
ADMIN_BOT3_CHAT_ID=YOUR_BOT3_CHAT_ID_HERE

# Bot 4: Login/Logout logs
ADMIN_BOT4_TOKEN=YOUR_BOT4_TOKEN_HERE
ADMIN_BOT4_CHAT_ID=YOUR_BOT4_CHAT_ID_HERE

# Bot 5: Future use
ADMIN_BOT5_TOKEN=YOUR_BOT5_TOKEN_HERE
ADMIN_BOT5_CHAT_ID=YOUR_BOT5_CHAT_ID_HERE

# =============================================================================
# Telegram Settings
# =============================================================================
TELEGRAM_ENABLED=True

# =============================================================================
# Data Retention (days)
# =============================================================================
SMS_RETENTION_DAYS=180
LOGS_RETENTION_DAYS=30
ADMIN_ACTIVITY_RETENTION_DAYS=90
```

### Step 3: Generate Secure SECRET_KEY

```bash
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
```

Copy the output and replace `SECRET_KEY` in `.env`

---

## ??? Database Setup

### Option 1: Local MongoDB Installation

#### Ubuntu/Debian
```bash
# Import MongoDB public key
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -

# Add MongoDB repository
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list

# Install MongoDB
sudo apt-get update
sudo apt-get install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod
```

#### macOS
```bash
# Install via Homebrew
brew tap mongodb/brew
brew install mongodb-community

# Start MongoDB
brew services start mongodb-community
```

### Option 2: Docker MongoDB

```bash
# Run MongoDB container
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=your_password \
  -v mongodb_data:/data/db \
  mongo:latest

# Update .env
MONGODB_URL=mongodb://admin:your_password@localhost:27017
```

### Option 3: MongoDB Atlas (Cloud)

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create free cluster
3. Get connection string
4. Update `.env`:
```bash
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/parental_control?retryWrites=true&w=majority
```

### Verify Database Connection

```bash
python3 -c "
from app.database import mongodb
import asyncio

async def test():
    from motor.motor_asyncio import AsyncIOMotorClient
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    await client.admin.command('ping')
    print('? MongoDB connection successful!')

asyncio.run(test())
"
```

---

## ?? Telegram Bots Setup

### Step 1: Create Bots

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` command
3. Follow instructions to create 6 bots:
   - 1 bot for 2FA
   - 5 bots for Administrator

#### Example:
```
You: /newbot
BotFather: Alright, a new bot. How are we going to call it?
You: My 2FA Bot
BotFather: Good. Now let's choose a username for your bot.
You: my_2fa_bot
BotFather: Done! Token: 1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ
```

Save all tokens!

### Step 2: Get Chat IDs

#### Method 1: Using Your Personal Chat
```
1. Start each bot in Telegram
2. Send a message: /start
3. Open in browser:
   https://api.telegram.org/bot<TOKEN>/getUpdates
4. Find "chat":{"id":123456789}
5. Save the ID
```

#### Method 2: Using a Channel/Group
```
1. Create a channel or group
2. Add bot as admin
3. Send a message in the channel
4. Use getUpdates URL above
5. Find chat ID (will be negative: -1001234567890)
```

### Step 3: Configure .env

Update `.env` with all bot tokens and chat IDs.

### Step 4: Test Telegram Bots

```bash
# Test 2FA bot
curl "https://api.telegram.org/bot<YOUR_2FA_TOKEN>/sendMessage?chat_id=<YOUR_CHAT_ID>&text=Test"

# Should receive "Test" message in Telegram
```

---

## ?? Firebase Setup

### Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project"
3. Enter project name
4. Enable/disable Google Analytics (optional)
5. Create project

### Step 2: Add Android App

1. In Firebase Console, click "Add app" ? Android
2. Enter package name (e.g., `com.yourcompany.parentalcontrol`)
3. Download `google-services.json`
4. **Save for Android app development**

### Step 3: Generate Service Account Key

1. Go to Project Settings ? Service Accounts
2. Click "Generate new private key"
3. Download JSON file
4. Rename to `firebase-credentials.json`
5. Place in project root (next to `run.py`)

### Step 4: Configure Firebase in Code

The server automatically loads `firebase-credentials.json` from the project root.

Verify:
```bash
ls -la firebase-credentials.json
# Should show the file
```

### Step 5: Test Firebase

```bash
python3 -c "
from app.services.firebase_service import firebase_service
print('? Firebase initialized successfully!' if firebase_service else '? Failed')
"
```

---

## ?? Running the Server

### Development Mode

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Run server
python run.py
```

Server starts on `http://localhost:8765`

### Access API Documentation

Open browser:
- **Swagger UI:** http://localhost:8765/docs
- **ReDoc:** http://localhost:8765/redoc
- **Health Check:** http://localhost:8765/health

### Test Default Admin

```bash
curl -X POST http://localhost:8765/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"1234567899"}'
```

Should receive access token.

---

## ?? Docker Deployment

### Step 1: Build Image

```bash
docker-compose build
```

### Step 2: Start Services

```bash
docker-compose up -d
```

This starts:
- Backend server on port 8765
- MongoDB on port 27017

### Step 3: View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
```

### Step 4: Stop Services

```bash
docker-compose down
```

---

## ?? Production Deployment

### Using Nginx as Reverse Proxy

#### 1. Install Nginx

```bash
sudo apt update
sudo apt install nginx
```

#### 2. Configure Nginx

Create `/etc/nginx/sites-available/parental-control`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8765;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 3. Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/parental-control /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Using Systemd Service

#### 1. Create Service File

Create `/etc/systemd/system/parental-control.service`:

```ini
[Unit]
Description=Parental Control Backend Server
After=network.target mongodb.service

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/workspace
Environment="PATH=/path/to/workspace/venv/bin"
ExecStart=/path/to/workspace/venv/bin/python /path/to/workspace/run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 2. Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable parental-control
sudo systemctl start parental-control
sudo systemctl status parental-control
```

### SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal (already configured by certbot)
sudo certbot renew --dry-run
```

---

## ?? Troubleshooting

### Server Won't Start

**Problem:** Server fails to start

**Solutions:**
```bash
# Check Python version
python3 --version  # Should be 3.10+

# Check dependencies
pip install -r requirements.txt

# Check MongoDB connection
mongosh  # or mongo

# Check port availability
sudo lsof -i :8765
```

### MongoDB Connection Failed

**Problem:** `MongoDB connection failed`

**Solutions:**
```bash
# Check MongoDB status
sudo systemctl status mongod

# Start MongoDB
sudo systemctl start mongod

# Check connection string in .env
cat .env | grep MONGODB_URL
```

### Telegram Bots Not Working

**Problem:** No Telegram notifications

**Solutions:**
```bash
# Check .env file
cat .env | grep TELEGRAM

# Test bot token
curl "https://api.telegram.org/bot<TOKEN>/getMe"

# Check server logs
# Should see: "? Telegram Multi-Service initialized"
```

### Firebase Not Working

**Problem:** FCM commands not sent

**Solutions:**
```bash
# Check firebase-credentials.json exists
ls -la firebase-credentials.json

# Check file permissions
chmod 644 firebase-credentials.json

# Verify JSON format
python3 -c "import json; json.load(open('firebase-credentials.json'))"
```

### 2FA Code Not Received

**Problem:** OTP code not sent to Telegram

**Solutions:**
1. Check `ENABLE_2FA` is `True` in `app/services/auth_service.py`
2. Verify `TELEGRAM_2FA_BOT_TOKEN` in `.env`
3. Verify `telegram_2fa_chat_id` for admin in database
4. Test bot manually:
```bash
curl "https://api.telegram.org/bot<TOKEN>/sendMessage?chat_id=<CHAT_ID>&text=Test"
```

### Can't Read .env File

**Problem:** Settings use default values, not from `.env`

**Solutions:**
```bash
# Verify .env file exists (not .env.example)
ls -la .env

# Check file location (must be in project root)
pwd
ls .env

# Restart server after .env changes
# Ctrl+C, then python run.py
```

### WebSocket Connection Dropped

**Problem:** Devices disconnect frequently

**Solutions:**
1. Check firewall settings
2. Increase `CONNECTION_TIMEOUT` in `.env`
3. Check nginx WebSocket configuration
4. Monitor server resources (RAM/CPU)

---

## ?? Monitoring & Logs

### View Logs

```bash
# Development
# Logs appear in terminal

# Production (systemd)
sudo journalctl -u parental-control -f

# Docker
docker-compose logs -f backend
```

### Health Check

```bash
curl http://localhost:8765/health
```

Expected response:
```json
{
  "status": "healthy",
  "mongodb": "healthy",
  "websocket_connections": 0,
  "timestamp": "2025-10-31T12:00:00"
}
```

---

## ?? Security Checklist

- [ ] Changed default admin password
- [ ] Generated secure `SECRET_KEY`
- [ ] Configured firewall (allow only necessary ports)
- [ ] Set up SSL certificate
- [ ] Configured MongoDB authentication
- [ ] `.env` file not committed to git
- [ ] Firebase credentials secured
- [ ] Telegram bot tokens secured
- [ ] Regular backups configured
- [ ] Monitoring set up

---

## ?? Next Steps

1. ? Server running successfully
2. ?? Read [FLUTTER_DEVELOPMENT.md](./FLUTTER_DEVELOPMENT.md) for app development
3. ?? Check [API_DOCS.md](./API_DOCS.md) for API reference
4. ?? Deploy to production
5. ?? Set up monitoring

---

**Need help? Open an issue on GitHub!**
