# Quick Start Guide

Get up and running in 10 minutes.

---

## Prerequisites

- Python 3.10+
- MongoDB 4.4+
- Telegram Bot (for 2FA)
- Firebase account (for push notifications)

---

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd device-management-system
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create `.env` file:

```env
# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=parental_control

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production

# Telegram (for 2FA)
TELEGRAM_ENABLED=true
TELEGRAM_2FA_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_2FA_CHAT_ID=your-telegram-chat-id

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false
```

### 4. Setup Firebase

Download Firebase service account keys:

1. **Device Firebase** ? `device-firebase-adminsdk.json`
2. **Admin Firebase** ? `admin-firebase-adminsdk.json`

Place both files in project root.

See [Firebase Setup Guide](./FIREBASE.md) for details.

### 5. Start Server

```bash
python run.py
```

Server starts on `http://localhost:8000`

---

## First Steps

### 1. Create Super Admin

```python
import requests

response = requests.post("http://localhost:8000/admin/create", json={
    "username": "superadmin",
    "password": "secure_password_123",
    "email": "admin@example.com",
    "full_name": "Super Admin",
    "role": "super_admin",
    "telegram_2fa_chat_id": "123456789",
    "telegram_bots": [
        {
            "bot_id": 1,
            "bot_name": "Device Notifications",
            "token": "BOT_TOKEN_1",
            "chat_id": "-1001234567890"
        },
        # ... 4 more bots (total 5)
    ]
})

print(response.json())
```

**Note:** First admin must be created directly in database or via API without authentication.

### 2. Login

**Step 1: Request OTP**
```python
response = requests.post("http://localhost:8000/auth/login", json={
    "username": "superadmin",
    "password": "secure_password_123"
})

temp_token = response.json()["temp_token"]
```

**Step 2: Check Telegram for OTP**

**Step 3: Verify OTP**
```python
response = requests.post("http://localhost:8000/auth/verify-2fa", json={
    "username": "superadmin",
    "otp_code": "123456",
    "temp_token": temp_token
})

access_token = response.json()["access_token"]
```

### 3. Register Device

```python
response = requests.post("http://localhost:8000/register", json={
    "type": "register",
    "device_id": "test_device_001",
    "device_info": {
        "model": "Samsung Galaxy S21",
        "manufacturer": "Samsung",
        "os_version": "Android 13",
        "battery": 85,
        "total_storage_mb": 128000.0,
        "free_storage_mb": 95000.0,
        "total_ram_mb": 8192.0,
        "free_ram_mb": 4096.0,
        "network_type": "WiFi",
        "is_rooted": false,
        "fcm_token": "device_fcm_token_here"
    },
    "user_id": "superadmin_device_token",  # From login response
    "app_type": "sexychat"
})
```

### 4. View Devices

```python
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get("http://localhost:8000/api/devices", headers=headers)

print(response.json())
```

### 5. Send Command

```python
response = requests.post(
    "http://localhost:8000/api/devices/test_device_001/command",
    headers=headers,
    json={"command": "ping"}
)

print(response.json())
```

---

## API Documentation

Complete API documentation available at:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Admin API:** [docs/ADMIN_API.md](./ADMIN_API.md)
- **Device API:** [docs/DEVICE_API.md](./DEVICE_API.md)

---

## Common Tasks

### Create Admin Account

```bash
curl -X POST "http://localhost:8000/admin/create" \
  -H "Authorization: Bearer SUPER_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newadmin",
    "password": "password123",
    "email": "newadmin@example.com",
    "full_name": "New Admin",
    "role": "admin",
    "expires_at": "2025-12-31T23:59:59"
  }'
```

### List Devices

```bash
curl -X GET "http://localhost:8000/api/devices?limit=50" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Filter by App Type

```bash
curl -X GET "http://localhost:8000/api/devices?app_type=sexychat" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### View Admin's Devices

```bash
curl -X GET "http://localhost:8000/api/admin/johndoe/devices" \
  -H "Authorization: Bearer SUPER_ADMIN_TOKEN"
```

### Send Command

```bash
curl -X POST "http://localhost:8000/api/devices/device123/command" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"command": "get_sms"}'
```

---

## Troubleshooting

### MongoDB Connection Error

```bash
# Check MongoDB running
sudo systemctl status mongodb

# Start MongoDB
sudo systemctl start mongodb
```

### Firebase Error

```bash
# Verify files exist
ls -la *-firebase-adminsdk.json

# Check permissions
chmod 600 *-firebase-adminsdk.json
```

### Telegram OTP Not Received

- Check bot token in `.env`
- Verify chat ID correct
- Ensure bot has send message permission
- Check server logs

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

---

## Next Steps

1. **Setup Admin Panel** - Configure web interface
2. **Configure Telegram Bots** - Setup all 5 bots
3. **Setup Firebase** - Complete Firebase configuration
4. **Deploy to Production** - See [DEPLOYMENT.md](./DEPLOYMENT.md)
5. **Read Documentation** - Explore API docs

---

## Resources

- **Main README:** [../README.md](../README.md)
- **Admin API:** [ADMIN_API.md](./ADMIN_API.md)
- **Device API:** [DEVICE_API.md](./DEVICE_API.md)
- **Authentication:** [AUTHENTICATION.md](./AUTHENTICATION.md)
- **Firebase Setup:** [FIREBASE.md](./FIREBASE.md)
- **Bot Auth:** [BOT_AUTH.md](./BOT_AUTH.md)

---

**Version:** 2.0.0  
**Last Updated:** November 2, 2025
