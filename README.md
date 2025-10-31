<<<<<<< HEAD
# ?? Android Control System

Multi-admin Android device monitoring and control system with Telegram bot integration.

## Features

- ?? Multi-device monitoring
- ?? Multi-admin support with role-based access
- ?? Advanced Telegram bot notification system
- ?? Real-time device tracking
- ?? SMS monitoring
- ?? Call logs tracking
- ?? Contact management
- ?? Two-factor authentication (2FA)
- ?? JWT-based authentication
- ?? Device-specific admin assignment

## Quick Start

Get running in 5 minutes:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Setup environment
cp .env.example .env
nano .env  # Edit MongoDB and Telegram settings

# 3. Run server
python run.py
```

**See:** [QUICK_START.md](QUICK_START.md) for detailed quick start guide.

## Documentation

?? **Complete Guides:**

- **[QUICK_START.md](QUICK_START.md)** - Get running in 5 minutes
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Complete setup instructions
- **[BOT_SYSTEM_GUIDE.md](BOT_SYSTEM_GUIDE.md)** - Telegram bot system explained
- **[ADMIN_GUIDE.md](ADMIN_GUIDE.md)** - Admin management guide

## System Overview

### Multi-Admin Architecture

Each admin has:
- **Unique device token** for device registration
- **Personal 2FA chat ID** for authentication codes
- **5 dedicated Telegram bots** for different notification types

### Telegram Bot System

The system uses **6 types of bots**:

1. **2FA Bot (Shared)** - Authentication codes
2. **Bot 1** - Device notifications
3. **Bot 2** - SMS notifications only
4. **Bot 3** - Admin activity logs
5. **Bot 4** - Login/Logout logs
6. **Bot 5** - Future use (app builds)

**Administrator (Super Admin)** receives ALL notifications from ALL admins, segregated by bot type.

See [BOT_SYSTEM_GUIDE.md](BOT_SYSTEM_GUIDE.md) for complete details.

## Tech Stack

- **Backend:** FastAPI (Python)
- **Database:** MongoDB
- **Authentication:** JWT + 2FA
- **Notifications:** Telegram Bot API
- **Push Notifications:** Firebase Cloud Messaging (Optional)
- **WebSocket:** Real-time device communication

## Default Credentials

```
Username: admin
Password: 1234567899
Role: super_admin
```

?? **IMPORTANT:** Change the default password immediately after first login!

## API Documentation

Once running, access interactive API docs at:

```
http://localhost:8765/docs
```

## Requirements

- Python 3.8+
- MongoDB 4.4+
- Telegram Bot (for notifications)
- Firebase (optional, for push notifications)

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd workspace
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set:
- MongoDB connection string
- JWT secret key
- Telegram 2FA bot token
- Telegram 2FA chat ID

### 4. Run Server

```bash
python run.py
```

Or with Docker:

```bash
docker-compose up -d
```

## Configuration

### Environment Variables

Key settings in `.env`:

```bash
# MongoDB
MONGODB_URL=mongodb://localhost:27017/android_control

# JWT Secret (change this!)
SECRET_KEY=your_very_long_random_secret_key

# Telegram 2FA Bot
TELEGRAM_2FA_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrs
TELEGRAM_2FA_CHAT_ID=-1001234567890

# Server
SERVER_PORT=8765
DEBUG=True
```

## Project Structure

```
workspace/
??? app/
?   ??? main.py                 # FastAPI application
?   ??? config.py               # Configuration
?   ??? database.py             # MongoDB connection
?   ??? models/                 # Data models
?   ?   ??? schemas.py          # Device schemas
?   ?   ??? admin_schemas.py    # Admin schemas
?   ??? services/               # Business logic
?   ?   ??? auth_service.py
?   ?   ??? device_service.py
?   ?   ??? telegram_multi_service.py
?   ??? utils/                  # Utilities
?       ??? auth_middleware.py
??? requirements.txt
??? Dockerfile
??? docker-compose.yml
??? run.py
```

## API Endpoints

### Authentication
- `POST /auth/login` - Admin login
- `POST /auth/logout` - Admin logout
- `GET /auth/me` - Get current admin info

### Admin Management
- `POST /admin/create` - Create new admin
- `GET /admin/list` - List all admins
- `PUT /admin/update/{username}` - Update admin
- `DELETE /admin/{username}` - Delete admin

### Device Management
- `POST /register` - Register device
- `GET /api/devices` - List devices
- `GET /api/devices/{device_id}` - Get device details
- `POST /devices/save/sms` - Save SMS data
- `POST /devices/save/contacts` - Save contacts
- `POST /devices/save/call-logs` - Save call logs

### Commands
- `POST /api/commands/send` - Send command to device
- `GET /api/commands/{device_id}` - Get pending commands

## Security Features

- ? JWT-based authentication
- ? Two-factor authentication (2FA) via Telegram
- ? Role-based access control (RBAC)
- ? Device-specific admin assignment
- ? Encrypted data transmission
- ? Activity logging

## Roles & Permissions

### Super Admin
- Full system access
- Manage all admins and devices
- Receive all notifications
- System configuration

### Admin
- Manage assigned devices only
- Send commands to own devices
- View own device data
- Cannot manage other admins

### Viewer
- Read-only access
- View assigned devices
- Cannot send commands
- Cannot edit settings

## Contributing

This is a private project. Contact the repository owner for contribution guidelines.

## License

Proprietary - All rights reserved

## Support

For setup help and troubleshooting, see:
- [SETUP_GUIDE.md](SETUP_GUIDE.md)
- [BOT_SYSTEM_GUIDE.md](BOT_SYSTEM_GUIDE.md)
- [ADMIN_GUIDE.md](ADMIN_GUIDE.md)

---

**Built with ?? using FastAPI and Python**
=======
# apiserver
>>>>>>> b51b4916098f530a30dc5e298e6f2c82b0792e65
