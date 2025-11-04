# 🚀 Device Control Server

A powerful, scalable FastAPI-based server for remote device management, monitoring, and control with comprehensive admin panel, multi-bot Telegram integration, and Firebase push notifications.

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)
![MongoDB](https://img.shields.io/badge/MongoDB-6.0+-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## ✨ Key Features

### 🔐 Advanced Security
- **Two-Factor Authentication (2FA)** with OTP via Telegram
- **Single Session Control** - Force logout from other devices
- **Role-Based Access Control (RBAC)** - Super Admin, Admin, Viewer roles
- **JWT Authentication** with session validation
- **Service vs Interactive Tokens** - Separate token types for services and users
- **Admin Account Expiration** - Set expiration dates for temporary admins

### 📱 Device Management
- **Real-time Device Monitoring** - Track online/offline status
- **SMS & Contact Sync** - Automatic synchronization in batches
- **Call Log Tracking** - Monitor incoming/outgoing calls
- **Battery & Storage Monitoring** - Track device health
- **Remote Commands** - Send SMS, enable call forwarding, ping devices
- **Firebase Cloud Messaging (FCM)** - Push commands to devices
- **Multiple App Flavor Support** - Support different app types per device

### 🤖 Multi-Bot Telegram Integration
Each admin gets **5 dedicated Telegram bots**:
1. **Bot 1** - Device notifications (registration, online/offline)
2. **Bot 2** - SMS notifications
3. **Bot 3** - Admin activity logs
4. **Bot 4** - Login/logout notifications
5. **Bot 5** - Future use (builds, updates)

Plus a **shared 2FA bot** for authentication codes.

### 📊 Admin Features
- **Activity Logging** - Track all admin actions
- **Device Filtering** - By admin, app type, status
- **Statistics Dashboard** - Real-time device stats
- **Push Notifications** - Alert admins via Firebase
- **Comprehensive API** - RESTful endpoints for all operations

### ⚡ Performance & Scalability
- **MongoDB Connection Pooling** - Optimized for 25,000+ devices
- **Background Task Processing** - Non-blocking notifications
- **Rate Limiting** - Prevent abuse with configurable limits
- **Data Retention Policies** - Auto-cleanup of old data
- **Efficient Indexing** - Fast queries even with large datasets

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│                  FastAPI Server                  │
├─────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐            │
│  │   REST API   │  │  WebSocket   │            │
│  └──────────────┘  └──────────────┘            │
├─────────────────────────────────────────────────┤
│            Services Layer                        │
│  ┌──────┐ ┌─────────┐ ┌──────────┐            │
│  │ Auth │ │ Device  │ │ Telegram │            │
│  └──────┘ └─────────┘ └──────────┘            │
│  ┌──────────┐ ┌────────────┐                   │
│  │ Firebase │ │ Activity   │                   │
│  └──────────┘ └────────────┘                   │
├─────────────────────────────────────────────────┤
│              Database Layer                      │
│            MongoDB (Motor)                       │
└─────────────────────────────────────────────────┘
```

---

## 📋 Requirements

- **Python 3.11+**
- **MongoDB 6.0+**
- **Redis** (optional, for caching)
- **Telegram Bot Token(s)**
- **Firebase Admin SDK** credentials

---

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd device-control-server
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

**Key configurations:**

```env
# Database
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=parental_control

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8765
DEBUG=False

# Security (IMPORTANT!)
SECRET_KEY=your-super-secret-key-here  # Generate a strong key!
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Telegram 2FA Bot (shared for all admins)
TELEGRAM_2FA_BOT_TOKEN=your-2fa-bot-token
TELEGRAM_2FA_CHAT_ID=-1001234567890

# Administrator's 5 Bots
ADMIN_BOT1_TOKEN=bot1-token-here
ADMIN_BOT1_CHAT_ID=-1001111111111

ADMIN_BOT2_TOKEN=bot2-token-here
ADMIN_BOT2_CHAT_ID=-1002222222222

# ... (Bot 3, 4, 5)
```

### 4. Run Server

#### Development

```bash
python run.py
```

or

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8765
```

#### Production

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8765 --workers 4
```

---

## 📚 API Documentation

Once running, visit:

- **Interactive API Docs**: http://localhost:8765/docs
- **Alternative Docs**: http://localhost:8765/redoc

### Quick API Reference

#### 🔐 Authentication

```bash
# Login (Step 1: Get OTP)
POST /auth/login
{
  "username": "admin",
  "password": "your-password"
}

# Login (Step 2: Verify OTP)
POST /auth/verify-2fa
{
  "username": "admin",
  "otp_code": "123456",
  "temp_token": "temporary-token-from-step-1",
  "fcm_token": "optional-firebase-token"
}

# Get Current Admin Info
GET /auth/me
Authorization: Bearer <token>
```

#### 📱 Device Management

```bash
# Get All Devices
GET /api/devices?skip=0&limit=50&admin_username=all
Authorization: Bearer <token>

# Get Device Details
GET /api/devices/{device_id}
Authorization: Bearer <token>

# Get Device SMS
GET /api/devices/{device_id}/sms?skip=0&limit=50
Authorization: Bearer <token>

# Send Command to Device
POST /api/devices/{device_id}/command
Authorization: Bearer <token>
{
  "command": "ping",
  "parameters": {"type": "firebase"}
}
```

#### 👥 Admin Management

```bash
# Create New Admin
POST /admin/create
Authorization: Bearer <token>
{
  "username": "newadmin",
  "password": "secure-password",
  "email": "admin@example.com",
  "full_name": "New Admin",
  "role": "admin",
  "telegram_2fa_chat_id": "-1001234567890"
}

# List All Admins
GET /admin/list
Authorization: Bearer <token>

# Update Admin
PUT /admin/{username}
Authorization: Bearer <token>
{
  "is_active": true,
  "role": "admin"
}
```

#### 📊 Statistics

```bash
# Get Device Stats
GET /api/devices/stats
Authorization: Bearer <token>

# Get Admin Activity Logs
GET /admin/activities?admin_username=admin&skip=0&limit=100
Authorization: Bearer <token>
```

---

## 🔧 Configuration Deep Dive

### Admin Roles & Permissions

| Role | Permissions |
|------|-------------|
| **SUPER_ADMIN** | All permissions, view all devices, manage admins |
| **ADMIN** | View own devices, send commands, change settings |
| **VIEWER** | View own devices only (read-only) |

### Rate Limiting

Default limits per minute:
- **Authentication**: 10 requests
- **Device Registration**: 500 requests
- **Heartbeat/Ping**: 2000 requests
- **SMS/Contacts Sync**: 1000 requests
- **General API**: 100 requests

Customize in `app/middleware/rate_limit.py`

### Data Retention

Auto-cleanup policies:
- **SMS**: 180 days
- **Logs**: 30 days
- **Admin Activities**: 90 days
- **OTP Codes**: 1 hour

Configure in `.env`:
```env
SMS_RETENTION_DAYS=180
LOGS_RETENTION_DAYS=30
ADMIN_ACTIVITY_RETENTION_DAYS=90
```

---

## 🐳 Docker Deployment

### Using Docker Compose

```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

### Manual Docker Build

```bash
# Build
docker build -t device-control-server .

# Run
docker run -d \
  --name device-server \
  -p 8765:8765 \
  -v $(pwd)/.env:/app/.env \
  device-control-server
```

---

## 🧪 Testing

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
  "timestamp": "2025-11-04T12:00:00.000Z"
}
```

### Default Admin Credentials

```
Username: admin
Password: 1234567899
```

**⚠️ IMPORTANT**: Change this password immediately in production!

---

## 📖 Advanced Topics

### Setting Up Telegram Bots

1. **Create bots** with [@BotFather](https://t.me/BotFather)
2. **Get bot tokens** from BotFather
3. **Get chat IDs**:
   - Send `/start` to your bot
   - Visit: `https://api.telegram.org/bot<TOKEN>/getUpdates`
   - Find `chat.id` in the response

4. **Configure in `.env`**

### Firebase Setup

1. Create a Firebase project
2. Download service account JSON
3. Place in project root
4. Update `app/services/firebase_service.py` with filename

### Creating New Admins

```bash
curl -X POST http://localhost:8765/admin/create \
  -H "Authorization: Bearer <super-admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "manager",
    "password": "SecurePass123!",
    "email": "manager@company.com",
    "full_name": "John Manager",
    "role": "admin",
    "telegram_2fa_chat_id": "-1001234567890",
    "telegram_bots": [
      {"bot_id": 1, "bot_name": "Manager_Bot_1", "token": "...", "chat_id": "..."},
      {"bot_id": 2, "bot_name": "Manager_Bot_2", "token": "...", "chat_id": "..."},
      {"bot_id": 3, "bot_name": "Manager_Bot_3", "token": "...", "chat_id": "..."},
      {"bot_id": 4, "bot_name": "Manager_Bot_4", "token": "...", "chat_id": "..."},
      {"bot_id": 5, "bot_name": "Manager_Bot_5", "token": "...", "chat_id": "..."}
    ]
  }'
```

---

## 🛡️ Security Best Practices

### Before Production

- [ ] Generate strong `SECRET_KEY`
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
- [ ] Change default admin password
- [ ] Enable MongoDB authentication
- [ ] Restrict CORS origins
- [ ] Enable SSL/TLS
- [ ] Set up firewall rules
- [ ] Configure proper logging
- [ ] Set up monitoring (Sentry, DataDog, etc.)

### Ongoing

- Regularly update dependencies
- Monitor rate limiting logs
- Review admin activity logs
- Rotate secrets periodically
- Backup database regularly

---

## 📊 Monitoring & Logs

### View Logs

```bash
# All logs
tail -f logs/server.log

# Error logs only
tail -f logs/server.log | grep ERROR
```

### Database Indexes

Automatically created on startup. View with:

```javascript
// MongoDB shell
use parental_control
db.devices.getIndexes()
db.admins.getIndexes()
```

---

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 Troubleshooting

### Common Issues

**Issue**: Can't connect to MongoDB
```bash
# Check MongoDB is running
systemctl status mongod

# Check connection string
echo $MONGODB_URL
```

**Issue**: 2FA codes not received
- Verify bot token is correct
- Check bot has permission to send messages
- Ensure `telegram_2fa_chat_id` is set for admin

**Issue**: Devices not appearing
- Check device is sending correct `admin_token`
- Verify admin account is active
- Check device logs

---

## 📞 Support

For issues and questions:
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)

---

## 🎉 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [MongoDB](https://www.mongodb.com/)
- [Firebase](https://firebase.google.com/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

---

**Made with ❤️ for device management at scale**
