# ?? Complete Setup Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [MongoDB Setup](#mongodb-setup)
3. [Telegram Bot Creation](#telegram-bot-creation)
4. [Environment Configuration](#environment-configuration)
5. [Firebase Setup (Optional)](#firebase-setup-optional)
6. [Running the Project](#running-the-project)
7. [First Admin Setup](#first-admin-setup)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- Python 3.8 or higher
- MongoDB 4.4 or higher
- pip (Python package manager)
- Git

### Check Python Version
```bash
python --version
# Should be 3.8 or higher
```

### Install Dependencies
```bash
cd /workspace
pip install -r requirements.txt
```

---

## MongoDB Setup

### Option 1: Local MongoDB Installation

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y mongodb
sudo systemctl start mongodb
sudo systemctl enable mongodb
```

#### macOS
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community
```

#### Windows
1. Download from: https://www.mongodb.com/try/download/community
2. Run installer
3. Start MongoDB service

### Option 2: MongoDB Atlas (Cloud - Free Tier)

1. Go to: https://www.mongodb.com/cloud/atlas
2. Create free account
3. Create Cluster (Free M0)
4. Click **Connect** ? **Connect your application**
5. Copy connection string:
   ```
   mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/myDatabase
   ```

---

## Telegram Bot Creation

### 1. Create 2FA Bot (Shared for all admins)

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Enter bot name: `My2FABot`
4. Enter bot username: `my2fa_bot` (must end with 'bot')
5. Save the **token**: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

### 2. Get Your Personal Chat ID (for 2FA)

1. Start your 2FA bot
2. Send any message (e.g., `/start`)
3. Open this URL in browser (replace `<TOKEN>` with your bot token):
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
4. Find `"chat":{"id":-1001234567890}`
5. Save this chat ID: `-1001234567890`

### 3. Create 5 Activity Bots for Super Admin

Create each bot with @BotFather:

#### Bot 1 - Devices
```
Command: /newbot
Name: Admin Devices Bot
Username: admin_devices_bot
Token: 1111111111:AAA_ADMIN_BOT1_TOKEN
```

#### Bot 2 - SMS
```
Command: /newbot
Name: Admin SMS Bot
Username: admin_sms_bot
Token: 2222222222:BBB_ADMIN_BOT2_TOKEN
```

#### Bot 3 - Admin Logs
```
Command: /newbot
Name: Admin Logs Bot
Username: admin_logs_bot
Token: 3333333333:CCC_ADMIN_BOT3_TOKEN
```

#### Bot 4 - Authentication
```
Command: /newbot
Name: Admin Auth Bot
Username: admin_auth_bot
Token: 4444444444:DDD_ADMIN_BOT4_TOKEN
```

#### Bot 5 - Builds (Future)
```
Command: /newbot
Name: Admin Builds Bot
Username: admin_builds_bot
Token: 5555555555:EEE_ADMIN_BOT5_TOKEN
```

### 4. Get Chat ID for Each Bot

For **each of the 5 bots**:
1. Start the bot in Telegram
2. Send a message
3. Visit: `https://api.telegram.org/bot<BOT_TOKEN>/getUpdates`
4. Find and save the chat ID

**Note:** You can use the same chat ID for all 5 bots if you want all messages in one chat!

---

## Environment Configuration

### 1. Copy Example File
```bash
cd /workspace
cp .env.example .env
```

### 2. Edit .env File
```bash
nano .env
```

### 3. Required Configuration

```bash
# ???????????????????????????????????????
# MongoDB Configuration
# ???????????????????????????????????????

# For local MongoDB:
MONGODB_URL=mongodb://localhost:27017/android_control

# For MongoDB Atlas:
# MONGODB_URL=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/android_control

MONGODB_DB_NAME=android_control


# ???????????????????????????????????????
# Server Configuration
# ???????????????????????????????????????

SERVER_HOST=0.0.0.0
SERVER_PORT=8765
DEBUG=True


# ???????????????????????????????????????
# Security & JWT
# ???????????????????????????????????????

# Generate random string: https://randomkeygen.com/
SECRET_KEY=CHANGE_THIS_TO_VERY_LONG_RANDOM_STRING_123456789

JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440


# ???????????????????????????????????????
# Telegram 2FA Bot (Shared)
# ???????????????????????????????????????

TELEGRAM_ENABLED=True

# Your 2FA bot token
TELEGRAM_2FA_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Your personal chat ID for 2FA
TELEGRAM_2FA_CHAT_ID=-1001234567890


# ???????????????????????????????????????
# Firebase (Optional - for push notifications)
# ???????????????????????????????????????

FIREBASE_ENABLED=False
# FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
```

### Complete .env Example

```bash
MONGODB_URL=mongodb://localhost:27017/android_control
MONGODB_DB_NAME=android_control

SERVER_HOST=0.0.0.0
SERVER_PORT=8765
DEBUG=True

SECRET_KEY=my_very_secure_random_secret_key_change_this_in_production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

TELEGRAM_ENABLED=True
TELEGRAM_2FA_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_2FA_CHAT_ID=-1001234567890

FIREBASE_ENABLED=False

SMS_RETENTION_DAYS=180
LOGS_RETENTION_DAYS=30
ADMIN_ACTIVITY_RETENTION_DAYS=90

PING_INTERVAL=30
CONNECTION_TIMEOUT=60
MAX_MESSAGE_SIZE=10485760
```

---

## Firebase Setup (Optional)

If you want push notifications to Android app:

### 1. Create Firebase Project
1. Go to: https://console.firebase.google.com/
2. Click **Add project**
3. Enter project name
4. Go to **Project Settings** ? **Service Accounts**
5. Click **Generate New Private Key**
6. Download JSON file

### 2. Add Credentials File
```bash
cp ~/Downloads/your-project-firebase-adminsdk.json /workspace/firebase-credentials.json
```

### 3. Enable in .env
```bash
FIREBASE_ENABLED=True
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
```

---

## Running the Project

### Method 1: Direct Run

```bash
cd /workspace
python run.py
```

Or:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8765 --reload
```

### Method 2: Docker

```bash
cd /workspace

# Build image
docker-compose build

# Run
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Verify Running

Open browser:
```
http://localhost:8765
```

Should see:
```json
{"message": "Android Control Server is running"}
```

### API Documentation (Swagger)
```
http://localhost:8765/docs
```

---

## First Admin Setup

### Automatic Super Admin

When the server starts for the first time, it automatically creates:

```
Username: admin
Password: 1234567899
Role: super_admin
```

?? **IMPORTANT: Change this password immediately!**

### Configure Super Admin's Telegram Bots

#### Step 1: Login

**Request:**
```bash
POST http://localhost:8765/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "1234567899"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

Save the `access_token`!

#### Step 2: Update Admin with Bot Configuration

**Request:**
```bash
PUT http://localhost:8765/admin/update/admin
Authorization: Bearer <ACCESS_TOKEN>
Content-Type: application/json

{
  "telegram_2fa_chat_id": "-1001234567890",
  
  "telegram_bots": [
    {
      "bot_id": 1,
      "bot_name": "admin_devices",
      "token": "1111111111:AAA_ADMIN_BOT1_TOKEN",
      "chat_id": "-1001111111111"
    },
    {
      "bot_id": 2,
      "bot_name": "admin_sms",
      "token": "2222222222:BBB_ADMIN_BOT2_TOKEN",
      "chat_id": "-1002222222222"
    },
    {
      "bot_id": 3,
      "bot_name": "admin_logs",
      "token": "3333333333:CCC_ADMIN_BOT3_TOKEN",
      "chat_id": "-1003333333333"
    },
    {
      "bot_id": 4,
      "bot_name": "admin_auth",
      "token": "4444444444:DDD_ADMIN_BOT4_TOKEN",
      "chat_id": "-1004444444444"
    },
    {
      "bot_id": 5,
      "bot_name": "admin_builds",
      "token": "5555555555:EEE_ADMIN_BOT5_TOKEN",
      "chat_id": "-1005555555555"
    }
  ]
}
```

#### Step 3: Get Device Token

**Request:**
```bash
GET http://localhost:8765/auth/me
Authorization: Bearer <ACCESS_TOKEN>
```

**Response:**
```json
{
  "username": "admin",
  "device_token": "a1b2c3d4e5f6...",
  "telegram_2fa_chat_id": "-1001234567890",
  "telegram_bots": [...]
}
```

Save the `device_token` - use this in Android app for device registration!

---

## Testing

### Test 1: Login

```bash
POST http://localhost:8765/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "1234567899"
}
```

Expected:
- ? Receive access token
- ? Telegram message to Bot 4 (if configured)

### Test 2: Create New Admin

```bash
POST http://localhost:8765/admin/create
Authorization: Bearer <ACCESS_TOKEN>
Content-Type: application/json

{
  "username": "user1",
  "email": "user1@example.com",
  "password": "password123",
  "full_name": "User One",
  "role": "admin",
  
  "telegram_2fa_chat_id": "-1009876543210",
  
  "telegram_bots": [
    {
      "bot_id": 1,
      "bot_name": "user1_devices",
      "token": "7777777777:XXX_USER1_BOT1",
      "chat_id": "-1007777777777"
    },
    {
      "bot_id": 2,
      "bot_name": "user1_sms",
      "token": "8888888888:YYY_USER1_BOT2",
      "chat_id": "-1008888888888"
    },
    {
      "bot_id": 3,
      "bot_name": "user1_logs",
      "token": "9999999999:ZZZ_USER1_BOT3",
      "chat_id": "-1009999999999"
    },
    {
      "bot_id": 4,
      "bot_name": "user1_auth",
      "token": "1010101010:WWW_USER1_BOT4",
      "chat_id": "-1000000000000"
    },
    {
      "bot_id": 5,
      "bot_name": "user1_builds",
      "token": "1111111111:VVV_USER1_BOT5",
      "chat_id": "-1001111111111"
    }
  ]
}
```

Expected:
- ? New admin created
- ? Receive device_token for user1
- ? Telegram message to Super Admin's Bot 3

### Test 3: Register Device

```bash
POST http://localhost:8765/register
Content-Type: application/json

{
  "device_id": "TEST-DEVICE-123",
  "device_info": {
    "model": "Samsung Galaxy A20",
    "manufacturer": "Samsung",
    "os_version": "Android 11"
  },
  "admin_token": "device_token_from_step_2"
}
```

Expected:
- ? Device registered
- ? Telegram message to owner's Bot 1
- ? Telegram message to Super Admin's Bot 1

---

## Troubleshooting

### Problem 1: Cannot Connect to MongoDB

**Check if MongoDB is running:**
```bash
# Linux
sudo systemctl status mongodb

# Mac
brew services list
```

**Start MongoDB:**
```bash
# Linux
sudo systemctl start mongodb

# Mac
brew services start mongodb-community
```

### Problem 2: Telegram Messages Not Received

**Checklist:**
- ? Bot tokens are correct
- ? Chat IDs are correct
- ? You've started the bot in Telegram
- ? `TELEGRAM_ENABLED=True` in `.env`

**Test bot manually:**
```bash
curl https://api.telegram.org/bot<TOKEN>/sendMessage \
  -d chat_id=-1001234567890 \
  -d text="Test message"
```

### Problem 3: Cannot Login

**Default credentials:**
- Username: `admin`
- Password: `1234567899`

**Reset admin password:**
```bash
# Connect to MongoDB
mongo android_control

# Update password (hashed with bcrypt)
db.admins.updateOne(
  {username: "admin"},
  {$set: {password_hash: "$2b$12$..."}}
)
```

### Problem 4: Port Already in Use

**Find process using port 8765:**
```bash
# Linux/Mac
lsof -i :8765

# Windows
netstat -ano | findstr :8765
```

**Kill process:**
```bash
# Linux/Mac
kill -9 <PID>

# Windows
taskkill /PID <PID> /F
```

### Problem 5: Dependencies Installation Failed

**Upgrade pip:**
```bash
pip install --upgrade pip
```

**Install with verbose output:**
```bash
pip install -r requirements.txt -v
```

**Use virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

pip install -r requirements.txt
```

---

## Setup Checklist

```
? Python 3.8+ installed
? Dependencies installed (pip install -r requirements.txt)
? MongoDB installed and running
? 2FA bot created
? 5 activity bots created for Super Admin
? All bot tokens obtained
? All chat IDs obtained
? .env file configured
? Server running (python run.py)
? Login tested
? Super Admin configured with bots
? device_token obtained
```

---

## Next Steps

1. Read **BOT_SYSTEM_GUIDE.md** to understand how the bot system works
2. Read **ADMIN_GUIDE.md** for admin management
3. Configure Android app with device_token
4. Start monitoring devices!

---

## Getting Help

- Check logs: `tail -f logs/app.log`
- API Documentation: http://localhost:8765/docs
- Issues: Create an issue on GitHub

---

**Setup Complete! ??**

Your Android Control System is now ready to use!
