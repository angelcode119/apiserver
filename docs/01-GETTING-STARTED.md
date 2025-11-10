# Getting Started

Complete guide to get up and running with the Device Management System.

## Prerequisites

- Python 3.10+
- MongoDB 4.4+
- Telegram Bot (for 2FA)
- Firebase account (for push notifications)

## Quick Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd device-management-system
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Create `.env` file:

```env
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=parental_control

SECRET_KEY=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

TELEGRAM_ENABLED=true
TELEGRAM_2FA_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_2FA_CHAT_ID=your-telegram-chat-id

ADMIN_BOT1_TOKEN=bot1-token
ADMIN_BOT1_CHAT_ID=-1001234567890

ADMIN_BOT2_TOKEN=bot2-token
ADMIN_BOT2_CHAT_ID=-1009876543210

ADMIN_BOT3_TOKEN=bot3-token
ADMIN_BOT3_CHAT_ID=-1001111222233

ADMIN_BOT4_TOKEN=bot4-token
ADMIN_BOT4_CHAT_ID=-1004444555566

ADMIN_BOT5_TOKEN=bot5-token
ADMIN_BOT5_CHAT_ID=-1007777888899

SERVER_HOST=0.0.0.0
SERVER_PORT=8765
DEBUG=false
```

### 4. Setup Firebase

Download Firebase service account keys:
1. **Device Firebase**: `device-firebase-adminsdk.json`
2. **Admin Firebase**: `admin-firebase-adminsdk.json`

Place both files in project root.

### 5. Start Server

```bash
python run.py
```

Server starts on `http://localhost:8765`

## First Steps

### 1. Create Super Admin

```python
import requests

response = requests.post("http://localhost:8765/admin/create", json={
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
        {
            "bot_id": 2,
            "bot_name": "SMS Notifications",
            "token": "BOT_TOKEN_2",
            "chat_id": "-1009876543210"
        },
        {
            "bot_id": 3,
            "bot_name": "Admin Activities",
            "token": "BOT_TOKEN_3",
            "chat_id": "-1001111222233"
        },
        {
            "bot_id": 4,
            "bot_name": "Authentication",
            "token": "BOT_TOKEN_4",
            "chat_id": "-1004444555566"
        },
        {
            "bot_id": 5,
            "bot_name": "System Monitoring",
            "token": "BOT_TOKEN_5",
            "chat_id": "-1007777888899"
        }
    ]
})

print(response.json())
```

### 2. Login

```python
response = requests.post("http://localhost:8765/auth/login", json={
    "username": "superadmin",
    "password": "secure_password_123"
})

temp_token = response.json()["temp_token"]

otp_code = input("Enter OTP from Telegram: ")

response = requests.post("http://localhost:8765/auth/verify-2fa", json={
    "username": "superadmin",
    "otp_code": otp_code,
    "temp_token": temp_token
})

access_token = response.json()["access_token"]
```

### 3. Register Device

```python
response = requests.post("http://localhost:8765/register", json={
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
    "user_id": "superadmin_device_token",
    "app_type": "sexychat"
})
```

### 4. View Devices

```python
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get("http://localhost:8765/api/devices", headers=headers)
print(response.json())
```

### 5. Send Command

```python
response = requests.post(
    "http://localhost:8765/api/devices/test_device_001/command",
    headers=headers,
    json={"command": "ping"}
)
print(response.json())
```

## API Documentation

- **Swagger UI**: http://localhost:8765/docs
- **ReDoc**: http://localhost:8765/redoc

## Common Tasks

### Create Admin

```bash
curl -X POST "http://localhost:8765/admin/create" \
  -H "Authorization: Bearer SUPER_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newadmin",
    "password": "password123",
    "email": "newadmin@example.com",
    "full_name": "New Admin",
    "role": "admin"
  }'
```

### List Devices

```bash
curl -X GET "http://localhost:8765/api/devices?limit=50" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Filter by App Type

```bash
curl -X GET "http://localhost:8765/api/devices?app_type=sexychat" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Troubleshooting

### MongoDB Connection Error

```bash
sudo systemctl status mongodb
sudo systemctl start mongodb
```

### Firebase Error

```bash
ls -la *-firebase-adminsdk.json
chmod 600 *-firebase-adminsdk.json
```

### Telegram OTP Not Received

- Check bot token in `.env`
- Verify chat ID correct
- Ensure bot has send message permission
- Check server logs

### Port Already in Use

```bash
lsof -i :8765
kill -9 <PID>
```

## Docker Deployment (Quick)

### docker-compose.yml

```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:6.0
    container_name: mongodb
    restart: always
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}
    volumes:
      - mongodb_data:/data/db
    ports:
      - "27017:27017"

  backend:
    build: .
    container_name: backend
    restart: always
    depends_on:
      - mongodb
    environment:
      - MONGODB_URL=mongodb://admin:${MONGO_PASSWORD}@mongodb:27017/
      - DATABASE_NAME=parental_control
      - SECRET_KEY=${SECRET_KEY}
      - TELEGRAM_2FA_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - TELEGRAM_2FA_CHAT_ID=${TELEGRAM_CHAT_ID}
    ports:
      - "8765:8765"

volumes:
  mongodb_data:
```

### Deploy

```bash
docker-compose up -d
docker-compose logs -f backend
```

## Next Steps

1. **Authentication** - Read [02-AUTHENTICATION.md](./02-AUTHENTICATION.md)
2. **Admin API** - Read [03-ADMIN-API.md](./03-ADMIN-API.md)
3. **Device API** - Read [04-DEVICE-API.md](./04-DEVICE-API.md)
4. **Firebase** - Read [05-FIREBASE.md](./05-FIREBASE.md)
5. **Telegram Bots** - Read [06-TELEGRAM-BOTS.md](./06-TELEGRAM-BOTS.md)
6. **Production Deployment** - Read [07-DEPLOYMENT.md](./07-DEPLOYMENT.md)

## Resources

- **Main README**: [../README.md](../README.md)
- **GitHub Repository**: <repository-url>
- **API Documentation**: http://localhost:8765/docs

**Last Updated**: November 10, 2025
**Version**: 3.0.0
