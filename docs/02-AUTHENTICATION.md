# Authentication

Complete guide for authentication, 2FA, and bot authorization.

## Overview

The system uses multi-layer authentication:
- **Admin Login**: JWT + 2FA via Telegram
- **Bot Authentication**: Service tokens (permanent)
- **Single Session Control**: One active session per admin
- **Account Expiry**: Optional time-limited access

## Admin Authentication Flow

### Step 1: Request OTP

```bash
POST /auth/login
{
  "username": "admin",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "success": true,
  "message": "OTP sent to Telegram",
  "temp_token": "eyJ...",
  "expires_in": 300
}
```

### Step 2: Verify OTP

```bash
POST /auth/verify-2fa
{
  "username": "admin",
  "otp_code": "123456",
  "temp_token": "temp_token_from_step1",
  "fcm_token": "firebase_token_optional"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 86400,
  "admin": {
    "username": "admin",
    "role": "admin",
    "permissions": ["view_devices", "manage_devices"]
  }
}
```

## 2FA Telegram Setup

### System Bot Configuration

One bot for all admins:

```env
TELEGRAM_2FA_BOT_TOKEN=7891234567:AAH-XxXxXxXx
```

### Per-Admin Chat IDs

Each admin has personal chat ID:

```python
{
  "username": "john",
  "telegram_2fa_chat_id": "123456789"
}
```

### Getting Chat ID

1. Start bot in Telegram
2. Send `/start`
3. Get updates:

```bash
curl "https://api.telegram.org/bot<TOKEN>/getUpdates"
```

## Bot Authentication

### For Telegram Bots (Service Tokens)

**Step 1: Request OTP**
```bash
POST /bot/auth/request-otp
{"username": "admin"}
```

**Step 2: Verify OTP**
```bash
POST /bot/auth/verify-otp
{
  "username": "admin",
  "otp_code": "123456"
}
```

**Response:**
```json
{
  "service_token": "eyJ...",
  "admin": {
    "username": "admin",
    "device_token": "abc123..."
  }
}
```

**Service tokens never expire!**

### Check Bot Status

```bash
GET /bot/auth/check?username=admin&service_token=TOKEN
```

## Single Session Control

- One active session per admin
- New login invalidates old sessions
- Session ID stored in JWT
- Validated on every request

## Token Types

| Feature | Interactive | Service |
|---------|------------|---------|
| Expiry | 24 hours | Never |
| Sessions | One active | Unlimited |
| Used By | Admins | Bots |
| Revocation | Logout/New login | Admin disabled |

## Account Expiry

```python
{
  "username": "trial_user",
  "expires_at": "2025-12-31T23:59:59",
  "is_active": true
}
```

Automatically disabled after expiry date.

## Logout

```bash
POST /auth/logout
Authorization: Bearer YOUR_TOKEN
```

Clears session, invalidates all tokens.

## Security Best Practices

- Use HTTPS in production
- Rotate secrets regularly
- Monitor failed login attempts
- Enable rate limiting
- Store tokens securely

## Troubleshooting

### OTP Not Received
- Check `telegram_2fa_chat_id` in admin document
- Verify bot token
- Ensure admin sent `/start` to bot

### Session Expired
- Another device logged in
- Logout and login again

### Invalid Token
- Token expired (24h for interactive)
- Wrong token type
- Login again

**Last Updated**: November 10, 2025
