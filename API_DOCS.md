# ?? API Documentation

Complete REST API and WebSocket documentation for the Parental Control Backend Server.

---

## ?? Table of Contents

1. [Base URL](#base-url)
2. [Authentication](#authentication)
3. [Admin Endpoints](#admin-endpoints)
4. [Device Endpoints](#device-endpoints)
5. [Data Endpoints](#data-endpoints)
6. [WebSocket API](#websocket-api)
7. [Error Responses](#error-responses)
8. [Rate Limiting](#rate-limiting)

---

## ?? Base URL

```
Development: http://localhost:8765
Production: https://your-domain.com
```

All endpoints are prefixed with the base URL.

---

## ?? Authentication

### Login (Step 1)

**Endpoint:** `POST /auth/login`

**Description:** Authenticate with username and password. Returns temp token and sends OTP via Telegram.

**Request Body:**
```json
{
  "username": "admin",
  "password": "1234567899"
}
```

**Response (2FA Enabled):**
```json
{
  "success": true,
  "message": "OTP code sent to your Telegram. Please verify to complete login.",
  "temp_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 300
}
```

**Response (2FA Disabled):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "admin": {
    "username": "admin",
    "email": "admin@example.com",
    "role": "super_admin",
    "permissions": [...]
  }
}
```

---

### Verify 2FA (Step 2)

**Endpoint:** `POST /auth/verify-2fa`

**Description:** Verify OTP code and get final access token.

**Request Body:**
```json
{
  "username": "admin",
  "otp_code": "123456",
  "temp_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "admin": {
    "username": "admin",
    "email": "admin@example.com",
    "full_name": "Administrator",
    "role": "super_admin",
    "permissions": [...],
    "device_token": "abc123...",
    "is_active": true,
    "last_login": "2025-10-31T12:00:00",
    "login_count": 15,
    "created_at": "2025-01-01T00:00:00"
  }
}
```

---

### Using Access Token

Include in all subsequent requests:

```bash
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## ?? Admin Endpoints

### Get Current Admin Info

**Endpoint:** `GET /auth/me`

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "username": "admin",
  "email": "admin@example.com",
  "full_name": "Administrator",
  "role": "super_admin",
  "permissions": [...],
  "device_token": "abc123def456...",
  "telegram_2fa_chat_id": "-1001234567890",
  "telegram_bots": [
    {
      "bot_id": 1,
      "bot_name": "Administrator_Devices",
      "token": "1111111111:AAA...",
      "chat_id": "-1001111111111"
    }
    // ... 4 more bots
  ],
  "is_active": true,
  "last_login": "2025-10-31T12:00:00",
  "login_count": 15,
  "created_at": "2025-01-01T00:00:00"
}
```

---

### Create Admin

**Endpoint:** `POST /admin/create`

**Permission:** `MANAGE_ADMINS`

**Request Body:**
```json
{
  "username": "user1",
  "email": "user1@example.com",
  "password": "secure_password",
  "full_name": "User One",
  "role": "admin",
  "telegram_2fa_chat_id": "-1001234567890",
  "telegram_bots": [
    {
      "bot_id": 1,
      "bot_name": "user1_devices",
      "token": "TOKEN1",
      "chat_id": "-1001111111111"
    }
    // Must provide exactly 5 bots or omit for placeholders
  ]
}
```

**Response:**
```json
{
  "username": "user1",
  "email": "user1@example.com",
  "full_name": "User One",
  "role": "admin",
  "permissions": [...],
  "device_token": "xyz789...",
  "telegram_2fa_chat_id": "-1001234567890",
  "telegram_bots": [...],
  "is_active": true,
  "created_at": "2025-10-31T12:00:00"
}
```

---

### Update Admin

**Endpoint:** `PUT /admin/{username}`

**Permission:** `MANAGE_ADMINS`

**Request Body:**
```json
{
  "email": "newemail@example.com",
  "full_name": "New Name",
  "telegram_bots": [...]
}
```

---

### List Admins

**Endpoint:** `GET /admin/list`

**Permission:** `MANAGE_ADMINS`

**Response:**
```json
{
  "admins": [
    {
      "username": "admin",
      "email": "admin@example.com",
      "role": "super_admin",
      ...
    }
  ],
  "total": 1
}
```

---

### Delete Admin

**Endpoint:** `DELETE /admin/{username}`

**Permission:** `MANAGE_ADMINS`

**Response:**
```json
{
  "message": "Admin deleted successfully"
}
```

---

### Logout

**Endpoint:** `POST /auth/logout`

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "message": "Logged out successfully"
}
```

---

## ?? Device Endpoints

### Register Device

**Endpoint:** `POST /register`

**Description:** Register a new device with admin token.

**Request Body:**
```json
{
  "device_id": "SAMSUNG-A20-123456",
  "device_info": {
    "model": "Samsung Galaxy A20",
    "manufacturer": "Samsung",
    "osVersion": "Android 13",
    "appVersion": "1.0.0"
  },
  "admin_token": "admin_device_token_here"
}
```

**Response:**
```json
{
  "status": "success",
  "is_new": true
}
```

---

### Get Devices List

**Endpoint:** `GET /api/devices`

**Permission:** `VIEW_DEVICES`

**Query Parameters:**
- `skip` (int, default=0): Pagination offset
- `limit` (int, default=100): Number of results

**Response:**
```json
{
  "devices": [
    {
      "device_id": "SAMSUNG-A20-123456",
      "model": "Samsung Galaxy A20",
      "manufacturer": "Samsung",
      "osVersion": "Android 13",
      "battery_level": 85,
      "is_online": true,
      "status": "online",
      "admin_username": "user1",
      "last_ping": "2025-10-31T12:00:00",
      "registered_at": "2025-10-31T10:00:00"
    }
  ],
  "total": 1,
  "hasMore": false
}
```

---

### Get Device Details

**Endpoint:** `GET /api/devices/{device_id}`

**Permission:** `VIEW_DEVICES`

**Response:**
```json
{
  "device_id": "SAMSUNG-A20-123456",
  "model": "Samsung Galaxy A20",
  "manufacturer": "Samsung",
  "osVersion": "Android 13",
  "appVersion": "1.0.0",
  "battery_level": 85,
  "is_online": true,
  "status": "online",
  "admin_username": "user1",
  "last_ping": "2025-10-31T12:00:00",
  "registered_at": "2025-10-31T10:00:00",
  "fcm_tokens": ["fcm_token_here"],
  "note_priority": "none",
  "note_message": ""
}
```

---

### Send Command to Device

**Endpoint:** `POST /api/devices/{device_id}/command`

**Permission:** `SEND_COMMANDS`

**Request Body:**

#### Ping Command
```json
{
  "command": "ping",
  "parameters": {
    "type": "firebase"
  }
}
```

#### Send SMS
```json
{
  "command": "send_sms",
  "parameters": {
    "phone": "+989121234567",
    "message": "Test message",
    "simSlot": 0
  }
}
```

#### Quick Upload SMS
```json
{
  "command": "quick_upload_sms",
  "parameters": {}
}
```

#### Upload All SMS
```json
{
  "command": "upload_all_sms",
  "parameters": {}
}
```

**Response:**
```json
{
  "success": true,
  "message": "Command sent successfully",
  "type": "firebase",
  "result": {
    "success": true,
    "message": "Notification sent"
  }
}
```

---

### Update Device Settings

**Endpoint:** `PUT /api/devices/{device_id}/settings`

**Permission:** `CHANGE_SETTINGS`

**Request Body:**
```json
{
  "sms_forward_enabled": true,
  "forward_number": "+989121234567"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Settings updated successfully"
}
```

---

### Heartbeat

**Endpoint:** `POST /devices/heartbeat`

**Description:** Device keepalive (sent by app every 30 seconds)

**Request Body:**
```json
{
  "deviceId": "SAMSUNG-A20-123456"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Heartbeat received"
}
```

---

## ?? Data Endpoints

### Get SMS Messages

**Endpoint:** `GET /api/devices/{device_id}/sms`

**Permission:** `VIEW_SMS`

**Query Parameters:**
- `skip` (int, default=0)
- `limit` (int, default=50)

**Response:**
```json
{
  "messages": [
    {
      "from": "+989121234567",
      "to": "+989129876543",
      "body": "Test message",
      "timestamp": "2025-10-31T12:00:00",
      "type": "inbox",
      "received_at": "2025-10-31T12:00:00"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 50
}
```

---

### Upload SMS Batch

**Endpoint:** `POST /sms/batch`

**Description:** Upload SMS history (called by app)

**Request Body:**
```json
{
  "device_id": "SAMSUNG-A20-123456",
  "data": [
    {
      "from": "+989121234567",
      "to": "+989129876543",
      "body": "Message text",
      "timestamp": 1699000000000,
      "type": "inbox"
    }
  ],
  "batch_info": {
    "batch": 1,
    "of": 10
  }
}
```

**Response:**
```json
{
  "status": "success"
}
```

---

### New SMS Notification

**Endpoint:** `POST /api/sms/new`

**Description:** Real-time SMS notification (sent by app immediately)

**Request Body:**
```json
{
  "device_id": "SAMSUNG-A20-123456",
  "data": {
    "from": "+989121234567",
    "body": "New message received",
    "timestamp": 1699000000000
  }
}
```

**Response:**
```json
{
  "status": "success",
  "device_id": "SAMSUNG-A20-123456",
  "message": "SMS received successfully"
}
```

---

### Get Contacts

**Endpoint:** `GET /api/devices/{device_id}/contacts`

**Permission:** `VIEW_CONTACTS`

**Query Parameters:**
- `skip` (int, default=0)
- `limit` (int, default=100)

**Response:**
```json
{
  "contacts": [
    {
      "name": "John Doe",
      "phone_number": "+989121234567",
      "device_id": "SAMSUNG-A20-123456"
    }
  ],
  "total": 50
}
```

---

### Upload Contacts

**Endpoint:** `POST /contacts/batch`

**Request Body:**
```json
{
  "device_id": "SAMSUNG-A20-123456",
  "data": [
    {
      "name": "John Doe",
      "phone_number": "+989121234567"
    }
  ]
}
```

**Response:**
```json
{
  "status": "success"
}
```

---

### Get Call Logs

**Endpoint:** `GET /api/devices/{device_id}/calls`

**Permission:** `VIEW_DEVICES`

**Query Parameters:**
- `skip` (int, default=0)
- `limit` (int, default=100)

**Response:**
```json
{
  "calls": [
    {
      "call_id": "unique_id",
      "device_id": "SAMSUNG-A20-123456",
      "number": "+989121234567",
      "name": "John Doe",
      "call_type": "incoming",
      "timestamp": "2025-10-31T12:00:00",
      "duration": 120,
      "duration_formatted": "2m 0s"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 100
}
```

---

### Upload Call Logs

**Endpoint:** `POST /call-logs/batch`

**Request Body:**
```json
{
  "device_id": "SAMSUNG-A20-123456",
  "data": [
    {
      "number": "+989121234567",
      "name": "John Doe",
      "call_type": "incoming",
      "timestamp": 1699000000000,
      "duration": 120
    }
  ]
}
```

**Response:**
```json
{
  "status": "success"
}
```

---

### Battery Update

**Endpoint:** `POST /battery`

**Request Body:**
```json
{
  "device_id": "SAMSUNG-A20-123456",
  "data": {
    "battery": 85,
    "is_online": true
  }
}
```

**Response:**
```json
{
  "status": "success"
}
```

---

### Delete Device SMS

**Endpoint:** `DELETE /api/devices/{device_id}/sms`

**Permission:** `DELETE_DATA`

**Response:**
```json
{
  "success": true,
  "deleted_count": 500
}
```

---

### Get Device Logs

**Endpoint:** `GET /api/devices/{device_id}/logs`

**Permission:** `VIEW_DEVICES`

**Query Parameters:**
- `skip` (int, default=0)
- `limit` (int, default=100)

**Response:**
```json
{
  "logs": [
    {
      "device_id": "SAMSUNG-A20-123456",
      "type": "system",
      "level": "info",
      "message": "Device registered",
      "timestamp": "2025-10-31T12:00:00"
    }
  ],
  "total": 50
}
```

---

### Get Statistics

**Endpoint:** `GET /api/stats`

**Permission:** `VIEW_DEVICES`

**Response:**
```json
{
  "total_devices": 10,
  "online_devices": 5,
  "offline_devices": 5,
  "total_sms": 1000,
  "total_contacts": 500,
  "total_call_logs": 800
}
```

---

## ?? WebSocket API

### Connection

**URL:** `ws://your-server:8765/ws?device_id={device_id}`

**Example:**
```javascript
const ws = new WebSocket('ws://localhost:8765/ws?device_id=SAMSUNG-A20-123456');
```

---

### Message Format

All messages are JSON:

```json
{
  "type": "message_type",
  "data": { ... }
}
```

---

### Client to Server Messages

#### Ping
```json
{
  "type": "ping"
}
```

#### Pong (response to server ping)
```json
{
  "type": "pong"
}
```

#### Device Status
```json
{
  "type": "status",
  "data": {
    "battery": 85,
    "is_online": true
  }
}
```

---

### Server to Client Messages

#### Ping Request
```json
{
  "type": "ping"
}
```

#### Command
```json
{
  "type": "command",
  "command": "get_sms",
  "parameters": {
    "limit": 50
  }
}
```

#### Settings Update
```json
{
  "type": "toggle_forward",
  "data": {
    "enabled": true
  }
}
```

---

## ? Error Responses

### Standard Error Format

```json
{
  "detail": "Error message here"
}
```

### Common Status Codes

- `200` - Success
- `400` - Bad Request
- `401` - Unauthorized (invalid/expired token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

### Example Error Responses

#### 401 Unauthorized
```json
{
  "detail": "Invalid or expired token"
}
```

#### 403 Forbidden
```json
{
  "detail": "You don't have permission to perform this action"
}
```

#### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "username"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## ?? Rate Limiting

Current implementation has no rate limiting, but recommended for production:

- **Login:** 5 attempts per 15 minutes per IP
- **API Requests:** 100 requests per minute per token
- **WebSocket:** 1 connection per device

---

## ?? Examples

### Complete Authentication Flow

```bash
# Step 1: Login
curl -X POST http://localhost:8765/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"1234567899"}'

# Response: {"temp_token": "...", "message": "OTP sent"}

# Step 2: Check Telegram for OTP code (e.g., 123456)

# Step 3: Verify OTP
curl -X POST http://localhost:8765/auth/verify-2fa \
  -H "Content-Type: application/json" \
  -d '{
    "username":"admin",
    "otp_code":"123456",
    "temp_token":"TEMP_TOKEN_FROM_STEP1"
  }'

# Response: {"access_token": "...", "admin": {...}}

# Step 4: Use access token for subsequent requests
curl -X GET http://localhost:8765/auth/me \
  -H "Authorization: Bearer ACCESS_TOKEN_FROM_STEP3"
```

---

### Device Registration and Data Upload

```bash
# Register device
curl -X POST http://localhost:8765/register \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "DEVICE123",
    "device_info": {
      "model": "Samsung S21",
      "manufacturer": "Samsung",
      "osVersion": "Android 13"
    },
    "admin_token": "admin_device_token"
  }'

# Upload SMS
curl -X POST http://localhost:8765/sms/batch \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "DEVICE123",
    "data": [
      {
        "from": "+1234567890",
        "body": "Test message",
        "timestamp": 1699000000000,
        "type": "inbox"
      }
    ]
  }'

# Send heartbeat
curl -X POST http://localhost:8765/devices/heartbeat \
  -H "Content-Type: application/json" \
  -d '{"deviceId": "DEVICE123"}'
```

---

## ?? Additional Resources

- **Swagger UI:** http://localhost:8765/docs
- **ReDoc:** http://localhost:8765/redoc
- **Health Check:** http://localhost:8765/health

---

**For setup and configuration, see [SETUP.md](./SETUP.md)**

**For Flutter/Android development, see [FLUTTER_DEVELOPMENT.md](./FLUTTER_DEVELOPMENT.md)**
