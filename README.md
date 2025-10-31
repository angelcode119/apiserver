# ?? Parental Control System - Backend Server

> Advanced parental control system for Android device monitoring and management

## ?? About

This project is a comprehensive parental control system that includes:
- **Backend Server** (FastAPI + WebSocket + REST API)
- **Database** (MongoDB)
- **Real-time Monitoring** (WebSocket connections)
- **Push Notifications** (Firebase FCM)
- **Telegram Notifications** (Multi-bot system)
- **Admin Panel** (REST API with 2FA authentication)

## ? Features

### ?? Admin Management
- Two-factor authentication (2FA) with Telegram
- Multiple access levels (Super Admin, Admin, Viewer)
- Multi-admin support with isolated permissions
- Complete activity logging

### ?? Device Monitoring
- Real-time WebSocket connections
- Device information (model, manufacturer, OS version)
- Battery monitoring and online/offline status
- Installed applications list

### ?? SMS Management
- Automatic SMS synchronization
- Search and filter messages
- Instant notifications for new SMS
- Configurable data retention

### ?? Call History
- Complete call logs (incoming/outgoing/missed)
- Call details (number, duration, timestamp)
- Contact management

### ?? Telegram Notification System
- 5 Telegram bots per admin:
  - Bot 1: Device notifications
  - Bot 2: SMS notifications
  - Bot 3: Admin activity logs
  - Bot 4: Login/Logout logs
  - Bot 5: Future use
- Shared 2FA bot for OTP codes

### ?? Remote Control
- Send commands to devices via Firebase FCM
- Device ping and online status check
- Send SMS from server to device
- Device settings management

## ??? Architecture

```
???????????????????
?  Android App    ? ???? Flutter/Native Android
???????????????????
         ?
         ? WebSocket + REST API
         ?
????????????????????????????????????
?      Backend Server              ?
?  ????????????????????????????   ?
?  ?   FastAPI + Uvicorn      ?   ?
?  ????????????????????????????   ?
?  ????????????????????????????   ?
?  ?   WebSocket Manager      ?   ?
?  ????????????????????????????   ?
?  ????????????????????????????   ?
?  ?   REST API Endpoints     ?   ?
?  ????????????????????????????   ?
????????????????????????????????????
         ?
         ???? MongoDB (Database)
         ???? Firebase FCM (Push)
         ???? Telegram Bots (Notifications)
```

## ?? Quick Start

### Prerequisites

- Python 3.10+
- MongoDB 4.4+
- Firebase account (for FCM)
- Telegram bots (optional)

### Installation

```bash
# Clone repository
git clone <repository-url>
cd workspace

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
nano .env  # Edit with your settings

# Start MongoDB
# (If using Docker):
docker run -d -p 27017:27017 mongo:latest

# Run server
python run.py
```

Server runs on `http://localhost:8765`

## ?? Documentation

- **[SETUP.md](./SETUP.md)** - Complete installation and configuration guide
- **[ADMIN_PANEL_GUIDE.md](./ADMIN_PANEL_GUIDE.md)** - Admin Panel user guide
- **[FLUTTER_DEVELOPMENT.md](./FLUTTER_DEVELOPMENT.md)** - Flutter/Android app development guide
- **[API_DOCS.md](./API_DOCS.md)** - Complete API documentation

## ?? Configuration

### .env File

```bash
# Database
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=parental_control

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8765

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 2FA Bot
TELEGRAM_2FA_BOT_TOKEN=your-bot-token
TELEGRAM_2FA_CHAT_ID=your-chat-id

# Administrator Bots (5 bots)
ADMIN_BOT1_TOKEN=bot1-token
ADMIN_BOT1_CHAT_ID=bot1-chat-id
# ... (other bots)
```

## ?? Authentication

### Default Login

```
Username: admin
Password: 1234567899
```

**?? Change the default password immediately!**

### 2FA System

- Enable/Disable: `app/services/auth_service.py` ? `ENABLE_2FA`
- When enabled, OTP code sent via Telegram
- 6-digit code, valid for 5 minutes

## ?? Flutter/Android Development

For mobile app development, see complete guide in **[FLUTTER_DEVELOPMENT.md](./FLUTTER_DEVELOPMENT.md)**

### App Connection

```dart
// WebSocket connection
final wsUrl = 'ws://your-server:8765/ws?device_id=DEVICE123';

// Device registration
POST /register
{
  "device_id": "DEVICE123",
  "device_info": {...},
  "admin_token": "admin_device_token_here"
}
```

## ??? Tech Stack

- **Backend:** FastAPI, Uvicorn
- **Database:** MongoDB (Motor - async driver)
- **Real-time:** WebSocket
- **Authentication:** JWT + 2FA
- **Push Notifications:** Firebase Cloud Messaging
- **Telegram:** Multi-bot system with aiohttp
- **Background Tasks:** AsyncIO

## ?? Project Structure

```
workspace/
??? app/
?   ??? main.py              # FastAPI app & endpoints
?   ??? config.py            # Configuration
?   ??? database.py          # MongoDB connection
?   ??? models/              # Pydantic schemas
?   ?   ??? schemas.py
?   ?   ??? admin_schemas.py
?   ?   ??? otp_schemas.py
?   ??? services/            # Business logic
?   ?   ??? auth_service.py
?   ?   ??? device_service.py
?   ?   ??? otp_service.py
?   ?   ??? telegram_multi_service.py
?   ?   ??? firebase_service.py
?   ?   ??? ...
?   ??? utils/               # Helpers
?       ??? auth_middleware.py
??? run.py                   # Entry point
??? requirements.txt         # Dependencies
??? .env                     # Environment variables
??? docker-compose.yml       # Docker setup
```

## ?? Testing

```bash
# Test health check
curl http://localhost:8765/health

# Test login
curl -X POST http://localhost:8765/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"1234567899"}'

# View API docs
# Open in browser:
http://localhost:8765/docs
```

## ?? Docker Deployment

```bash
# Build
docker-compose build

# Run
docker-compose up -d

# Logs
docker-compose logs -f

# Stop
docker-compose down
```

## ?? Contributing

1. Fork the project
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## ?? License

This project is licensed under the MIT License.

## ?? Bug Reports

For bug reports or feature requests, please open an Issue.

## ?? Contact

For questions or support, please open an Issue or contact us via email.

---

**Made with ?? for family safety**
