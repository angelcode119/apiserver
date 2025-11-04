# 🚀 Device Control Server

A powerful FastAPI-based server for remote device monitoring and control with comprehensive admin management, 2FA authentication, and multi-bot Telegram integration.

## ✨ Features

### 🔐 Security
- **Two-Factor Authentication (2FA)** with OTP via Telegram
- **Single Session Control** - prevent simultaneous logins
- **Service vs Interactive Tokens** - separate authentication for bots
- **Role-Based Access Control** - granular permissions system
- **Admin Expiry** - time-limited admin accounts
- **Activity Logging** - comprehensive audit trail

### 📱 Device Management
- Real-time device monitoring
- SMS/Contacts/Call logs collection
- Battery and online status tracking
- Firebase Cloud Messaging (FCM) integration
- Remote command execution
- Device-to-admin association

### 📢 Notifications
- **Multi-Bot System** - 5 specialized Telegram bots per admin:
  - Bot 1: Device notifications
  - Bot 2: SMS notifications  
  - Bot 3: Admin activity logs
  - Bot 4: Login/Logout tracking
  - Bot 5: Reserved for future use
- Firebase push notifications for admins
- Background task processing

### 🎯 Admin Features
- Super Admin and regular Admin roles
- Device token-based authentication
- Activity monitoring and statistics
- Admin account management
- Telegram 2FA integration

## 🏗️ Architecture

```
app/
├── main.py                 # FastAPI application and routes
├── config.py               # Configuration management
├── database.py             # MongoDB connection and indexes
├── background_tasks.py     # Async notification tasks
├── models/                 # Pydantic schemas
│   ├── schemas.py          # Device models
│   ├── admin_schemas.py    # Admin models
│   ├── otp_schemas.py      # 2FA models
│   ├── bot_schemas.py      # Bot auth models
│   └── upi_schemas.py      # UPI PIN models
├── services/               # Business logic
│   ├── auth_service.py     # Authentication
│   ├── device_service.py   # Device management
│   ├── telegram_multi_service.py  # Telegram integration
│   ├── firebase_service.py        # Device FCM
│   ├── firebase_admin_service.py  # Admin FCM
│   ├── otp_service.py            # 2FA OTP
│   └── admin_activity_service.py  # Activity logging
├── middleware/            # Custom middleware
│   └── rate_limit.py      # Rate limiting
└── utils/                 # Helper functions
    └── auth_middleware.py # JWT authentication
```

## 🚦 Quick Start

### Prerequisites
- Python 3.11+
- MongoDB 6.0+
- Firebase project with FCM enabled
- Telegram bots (created via @BotFather)

### Installation

1. **Clone repository**
```bash
git clone <repository-url>
cd <project-directory>
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your credentials
```

4. **Set up Firebase**
- Download service account JSON from Firebase Console
- Place it in project root
- Update path in `app/services/firebase_service.py`

5. **Create Telegram bots**
- Create 6 bots via @BotFather (1 for 2FA + 5 for admin)
- Get bot tokens and chat IDs
- Update `.env` file

6. **Run server**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8765 --reload
```

## 📚 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8765/docs
- **ReDoc**: http://localhost:8765/redoc

### Key Endpoints

#### Authentication
```
POST /auth/login                 # Step 1: Login (get OTP)
POST /auth/verify-2fa            # Step 2: Verify OTP
POST /auth/logout                # Logout
GET  /auth/me                    # Current admin info
```

#### Device Management
```
POST /register                   # Register device
POST /devices/heartbeat          # Device heartbeat
GET  /api/devices                # List devices
GET  /api/devices/{id}           # Device details
POST /api/devices/{id}/command   # Send command
GET  /api/devices/{id}/sms       # Get SMS messages
GET  /api/devices/{id}/contacts  # Get contacts
```

#### Admin Management
```
POST /admin/create               # Create admin
GET  /admin/list                 # List admins
PUT  /admin/{username}           # Update admin
DELETE /admin/{username}         # Delete admin
GET  /admin/activities           # Admin activity logs
```

#### Bot Authentication
```
POST /bot/auth/request-otp       # Request OTP for bot
POST /bot/auth/verify-otp        # Verify OTP, get service token
GET  /bot/auth/check             # Check bot status
```

## 🔧 Configuration

### Environment Variables

Key variables in `.env`:

```bash
# Database
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=parental_control

# Security
SECRET_KEY=your-super-secret-key-change-this
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 2FA Bot (shared)
TELEGRAM_2FA_BOT_TOKEN=your-2fa-bot-token
TELEGRAM_2FA_CHAT_ID=-1001234567890

# Administrator's 5 Bots
ADMIN_BOT1_TOKEN=bot-1-token
ADMIN_BOT1_CHAT_ID=-1001111111111
# ... (repeat for BOT2-BOT5)

# Settings
DEBUG=True
TELEGRAM_ENABLED=True
```

### Default Admin

Default super admin is created on first run:
- **Username**: `admin`
- **Password**: `1234567899`
- ⚠️ **Change immediately in production!**

## 🔒 Security Best Practices

### Before Production

1. **Change SECRET_KEY**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

2. **Update default admin password**
```python
# Set via environment variable
DEFAULT_ADMIN_PASSWORD=your-strong-password
```

3. **Enable SSL/TLS**
- Use HTTPS for all connections
- Enable SSL verification in Telegram service

4. **Restrict CORS origins**
```python
allow_origins=["https://yourdomain.com"]
```

5. **Add MongoDB authentication**
```bash
MONGODB_URL=mongodb://user:pass@localhost:27017
```

6. **Set up firewall rules**
- Allow only necessary ports
- Restrict database access

## 📊 Database Collections

- `admins` - Admin accounts and sessions
- `devices` - Registered devices
- `sms_messages` - SMS history
- `contacts` - Contact lists
- `call_logs` - Call history
- `logs` - Device activity logs
- `admin_activities` - Admin action logs
- `otp_codes` - 2FA OTP codes
- `commands` - Device commands

## 🔥 Performance

### Optimizations
- Connection pooling (MongoDB)
- Background task processing
- Rate limiting middleware
- Database indexing
- Data retention policies

### Scaling
- Supports 25,000+ concurrent users
- Horizontal scaling ready
- Load balancer compatible
- Redis-ready for caching

## 🛠️ Development

### Run tests
```bash
pytest
```

### Code quality
```bash
# Format
black app/

# Lint
flake8 app/
```

### Create indexes
```bash
python scripts/create_indexes.py
```

## 📝 License

[Add your license here]

## 🤝 Contributing

[Add contributing guidelines]

## 📧 Support

[Add support information]

---

Made with ❤️ by [Your Team]
