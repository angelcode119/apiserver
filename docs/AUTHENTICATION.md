# Authentication Guide

Complete authentication and security documentation.

---

## Table of Contents

1. [Two-Factor Authentication (2FA)](#two-factor-authentication-2fa)
2. [Single Session Control](#single-session-control)
3. [JWT Tokens](#jwt-tokens)
4. [Service vs Interactive Tokens](#service-vs-interactive-tokens)
5. [Account Expiry](#account-expiry)
6. [Session Management](#session-management)
7. [Security Best Practices](#security-best-practices)

---

## Two-Factor Authentication (2FA)

### Overview

All admin logins require **two-step verification**:

1. **Step 1**: Username + Password ? Receive OTP via Telegram
2. **Step 2**: Enter OTP ? Get access token

### Authentication Flow

```
???????????????????????????????????????????????????????????????
?                     Login Flow                               ?
???????????????????????????????????????????????????????????????

1. Admin ? POST /auth/login
   Body: { username, password }
   
2. Server validates credentials
   
3. Server generates 6-digit OTP
   
4. Server sends OTP to admin's Telegram
   
5. Server returns temp_token (5 min expiry)
   
6. Admin checks Telegram for OTP
   
7. Admin ? POST /auth/verify-2fa
   Body: { username, otp_code, temp_token, fcm_token? }
   
8. Server validates temp_token and OTP
   
9. Server generates session_id
   
10. Server invalidates all previous sessions
   
11. Server saves FCM token (if provided)
   
12. Server returns access_token (24h expiry)
   
13. Admin uses access_token for API requests
```

### Step 1: Request OTP

**Endpoint:** `POST /auth/login`

**Request:**
```json
{
  "username": "admin",
  "password": "secure_password"
}
```

**Success Response:**
```json
{
  "success": true,
  "message": "OTP sent to Telegram",
  "temp_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 300
}
```

**Telegram Message (Bot 4):**
```
?? Login Verification

?? Username: admin
?? OTP Code: 749675
? Valid for: 5 minutes
?? IP: 192.168.1.100

?? If this wasn't you, ignore this message.
```

**Validations:**
- Username exists
- Password correct
- Account is active
- Account not expired
- OTP not rate-limited (max 5 attempts)

### Step 2: Verify OTP

**Endpoint:** `POST /auth/verify-2fa`

**Request:**
```json
{
  "username": "admin",
  "otp_code": "749675",
  "temp_token": "temp_token_from_step1",
  "fcm_token": "firebase_cloud_messaging_token"  // Optional
}
```

**Success Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "admin": {
    "username": "admin",
    "email": "admin@example.com",
    "full_name": "Admin User",
    "role": "admin",
    "permissions": ["view_devices", "manage_devices"],
    "device_token": "abc123...",
    "is_active": true,
    "last_login": "2025-11-02T10:00:00",
    "login_count": 42,
    "expires_at": null
  }
}
```

**Validations:**
- Temp token valid (not expired)
- OTP code correct
- OTP not used before
- Account still active
- Account not expired

**What Happens:**
1. New `session_id` generated (UUID)
2. Previous `session_id` invalidated
3. Old tokens stop working
4. FCM token saved (for push notifications)
5. `last_login` updated
6. `login_count` incremented
7. Activity logged
8. Telegram notification sent

---

## Single Session Control

### Overview

Each admin can only have **one active session** at a time. When you login from a new device, all previous sessions are invalidated.

### How It Works

**Database Structure:**
```json
{
  "username": "admin",
  "current_session_id": "550e8400-e29b-41d4-a716-446655440000",
  "last_session_ip": "192.168.1.100",
  "last_session_device": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)..."
}
```

**Token Structure:**
```json
{
  "sub": "admin",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "client_type": "interactive",
  "exp": 1698912000
}
```

### Session Flow Example

```
Device A: Login ? session_id_1 generated
  ?
Admin database: current_session_id = session_id_1
  ?
Device A: API requests work ?

Device B: Login ? session_id_2 generated
  ?
Admin database: current_session_id = session_id_2
  ?
Device A: API requests fail ? (session_id_1 != session_id_2)
Device B: API requests work ?
```

### Validation Logic

**Middleware checks:**
```python
if token.client_type == "interactive":
    if admin.current_session_id is None:
        raise HTTPException(403, "No active session")
    
    if token.session_id != admin.current_session_id:
        raise HTTPException(403, "Session expired")
```

### Error Messages

**Session Expired:**
```json
{
  "detail": "Session expired. Another login detected from different location."
}
```

**No Active Session:**
```json
{
  "detail": "No active session. Please login again."
}
```

### Exception: Service Tokens

Service tokens (used by Telegram bots) **bypass** single-session check:

```json
{
  "sub": "bot_admin",
  "client_type": "service",
  "device_token": "abc123..."
  // No session_id
  // No exp (permanent)
}
```

---

## JWT Tokens

### Token Types

1. **Temporary Token** - For OTP step (5 min)
2. **Access Token** - For API access (24 hours)
3. **Service Token** - For bots (permanent)

### Token Structure

**Interactive Token (Web/Mobile):**
```json
{
  "sub": "admin",                    // Username
  "session_id": "uuid-here",         // Session identifier
  "client_type": "interactive",      // Token type
  "exp": 1698912000,                 // Expiry timestamp (24h)
  "iat": 1698825600                  // Issued at
}
```

**Service Token (Bots):**
```json
{
  "sub": "bot_admin",                // Username
  "client_type": "service",          // Token type
  "device_token": "abc123...",       // Admin's device token
  "iat": 1698825600                  // Issued at
  // No exp - Permanent
  // No session_id - Bypasses single-session
}
```

### Token Generation

**Interactive Token:**
```python
from app.services.auth_service import auth_service

token = auth_service.create_access_token(
    username="admin",
    session_id="uuid-here",
    client_type="interactive"
)
```

**Service Token:**
```python
token = auth_service.create_access_token(
    username="bot_admin",
    client_type="service"
)
```

### Token Usage

**Authorization Header:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/devices" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Token Validation

**Middleware validates:**
1. Token signature valid
2. Token not expired (for interactive tokens)
3. Username exists
4. Admin is active
5. Admin not expired
6. Session valid (for interactive tokens)

---

## Service vs Interactive Tokens

### Comparison Table

| Feature | Interactive Token | Service Token |
|---------|------------------|---------------|
| **Used By** | Web/Mobile admins | Telegram bots |
| **Expiry** | 24 hours | Never |
| **Session Check** | Yes | No |
| **Login Required** | Yes (2FA) | Yes (bot OTP) |
| **Revocation** | Logout or new login | Admin disabled |
| **Use Case** | Human interaction | Background services |

### Interactive Token

**Purpose:** Admin panel, mobile apps

**Characteristics:**
- Short-lived (24h)
- Session-based
- One active session
- Invalidated on logout
- Requires 2FA login

**Example Use:**
```python
# Admin login
response = requests.post("/auth/login", json={
    "username": "admin",
    "password": "pass"
})
temp_token = response.json()["temp_token"]

# Verify OTP
response = requests.post("/auth/verify-2fa", json={
    "username": "admin",
    "otp_code": "123456",
    "temp_token": temp_token
})
access_token = response.json()["access_token"]

# Use token
headers = {"Authorization": f"Bearer {access_token}"}
requests.get("/api/devices", headers=headers)
```

### Service Token

**Purpose:** Telegram bots, background services

**Characteristics:**
- Permanent (no expiry)
- No session check
- Multiple concurrent uses
- Only revoked if admin disabled
- Requires bot OTP (one-time setup)

**Example Use:**
```python
# Bot login (one-time)
response = requests.post("/bot/auth/request-otp", json={
    "username": "admin"
})

# Verify OTP (from Telegram)
response = requests.post("/bot/auth/verify-otp", json={
    "username": "admin",
    "otp_code": "123456"
})
service_token = response.json()["service_token"]

# Save token (use forever)
# Check admin status periodically
response = requests.get("/bot/auth/check", params={
    "username": "admin",
    "service_token": service_token
})
if response.json()["is_active"]:
    # Admin active, continue working
else:
    # Admin disabled, stop bot
```

---

## Account Expiry

### Overview

Admin accounts can have expiration dates. After expiration:
- Account automatically disabled
- All login attempts rejected
- All API requests fail
- Requires admin intervention

### Expiry Check Points

**1. Login Time:**
```python
# In /auth/login
if admin.expires_at:
    if datetime.utcnow() > admin.expires_at:
        # Auto-disable
        admin.is_active = False
        raise HTTPException(403, f"Account expired on {expires_at}")
```

**2. Every API Request:**
```python
# In auth_middleware.py
if admin.expires_at:
    if datetime.utcnow() > admin.expires_at:
        # Auto-disable
        admin.is_active = False
        raise HTTPException(403, f"Account expired on {expires_at}")
```

### Creating Accounts

**With Expiry (30 days):**
```python
from datetime import datetime, timedelta

expires_at = datetime.utcnow() + timedelta(days=30)

response = requests.post("/admin/create", json={
    "username": "trial_user",
    "password": "pass123",
    "email": "trial@test.com",
    "full_name": "Trial User",
    "expires_at": expires_at.isoformat()
})
```

**Unlimited Account:**
```python
response = requests.post("/admin/create", json={
    "username": "perm_user",
    "password": "pass123",
    "email": "perm@test.com",
    "full_name": "Permanent User"
    # No expires_at = unlimited
})
```

### Managing Expiry

**Check Expiry:**
```python
response = requests.get("/admin/trial_user")
admin = response.json()

if admin["expires_at"]:
    print(f"Expires: {admin['expires_at']}")
else:
    print("Unlimited")
```

**Extend Expiry:**
```python
new_expiry = datetime.utcnow() + timedelta(days=60)

requests.put("/admin/trial_user", json={
    "expires_at": new_expiry.isoformat()
})
```

**Remove Expiry:**
```python
requests.put("/admin/trial_user", json={
    "expires_at": null
})
```

### Error Messages

**Expired Account:**
```json
{
  "detail": "Account expired on 2025-12-31. Please contact administrator."
}
```

**Disabled Account:**
```json
{
  "detail": "Admin account is disabled"
}
```

---

## Session Management

### Session Data

**Stored in Admin Document:**
```json
{
  "username": "admin",
  "current_session_id": "550e8400-e29b-41d4-a716-446655440000",
  "last_session_ip": "192.168.1.100",
  "last_session_device": "Mozilla/5.0...",
  "last_login": "2025-11-02T10:00:00",
  "login_count": 42
}
```

### Session Lifecycle

**1. Login:**
```python
session_id = str(uuid.uuid4())  # Generate new session
admin.current_session_id = session_id
admin.last_login = datetime.utcnow()
admin.login_count += 1
```

**2. Active Session:**
```python
# Every API request checks:
if token.session_id != admin.current_session_id:
    raise HTTPException(403, "Session expired")
```

**3. Logout:**
```python
admin.current_session_id = None  # Clear session
# All tokens with old session_id stop working
```

**4. New Login:**
```python
new_session_id = str(uuid.uuid4())
admin.current_session_id = new_session_id
# Old session_id invalidated
```

### Logout

**Endpoint:** `POST /auth/logout`

**Request:**
```bash
curl -X POST "http://localhost:8000/auth/logout" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**What Happens:**
1. Clear `current_session_id` (set to `None`)
2. All tokens with old session stop working
3. Log logout activity
4. Send Telegram notification

**Response:**
```json
{
  "message": "Logged out successfully"
}
```

---

## Security Best Practices

### Password Security

**Requirements:**
- Minimum 8 characters
- Store hashed (bcrypt)
- Never log passwords
- Rotate regularly

**Example:**
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"])
hashed = pwd_context.hash("password123")
is_valid = pwd_context.verify("password123", hashed)
```

### Token Security

**Do:**
- ? Use HTTPS in production
- ? Store tokens securely (keychain, secure storage)
- ? Never expose in logs
- ? Set appropriate expiry
- ? Validate on every request
- ? Use different tokens for different purposes

**Don't:**
- ? Store in localStorage (XSS risk)
- ? Send in URL parameters
- ? Share between users
- ? Log token values
- ? Use same token for web and bots

### 2FA Security

**Benefits:**
- Prevents password-only attacks
- Out-of-band verification
- Telegram as second factor
- Time-limited OTP codes

**OTP Configuration:**
```python
OTP_EXPIRY = 300  # 5 minutes
OTP_LENGTH = 6    # 6 digits
OTP_MAX_ATTEMPTS = 5  # Rate limiting
```

### Session Security

**Single Session Benefits:**
- Prevents concurrent access
- Detects account sharing
- Enforces geographic restrictions
- Audit trail (last IP, device)

**Monitoring:**
```python
# Check suspicious logins
if new_ip != last_ip:
    send_alert("Login from new location")

if login_count > 100 and account_age < 1_day:
    flag_for_review()
```

### Account Expiry Security

**Use Cases:**
- Trial accounts (30 days)
- Temporary contractors
- Seasonal access
- License enforcement

**Auto-disable:**
```python
# Runs on every login and API request
if admin.expires_at and datetime.utcnow() > admin.expires_at:
    admin.is_active = False
    raise HTTPException(403, "Account expired")
```

---

## Rate Limiting

### OTP Rate Limiting

**Limits:**
- Max 5 OTP requests per 15 minutes
- Max 5 failed OTP attempts
- Account temporarily locked after threshold

**Implementation:**
```python
otp_attempts = get_otp_attempts(username)
if otp_attempts > 5:
    raise HTTPException(429, "Too many OTP requests")
```

### Login Rate Limiting

**Limits:**
- Max 10 login attempts per hour
- Max 3 failed passwords per 15 minutes

**Lockout:**
- Temporary: 15 minutes
- Permanent: After 10 temporary lockouts

---

## Activity Logging

### Logged Events

1. **Login Attempts:**
   - Successful logins
   - Failed logins
   - OTP requests
   - OTP verifications

2. **Session Events:**
   - New sessions
   - Session expirations
   - Logouts

3. **Security Events:**
   - Password changes
   - Account disabled
   - Expiry triggered

### Log Structure

```json
{
  "admin_username": "admin",
  "activity_type": "login",
  "description": "Login step 2: OTP verified",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "success": true,
  "timestamp": "2025-11-02T10:00:00"
}
```

### Viewing Logs

**Endpoint:** `GET /api/admin/activities`

**Example:**
```bash
curl -X GET "http://localhost:8000/api/admin/activities?admin_username=admin" \
  -H "Authorization: Bearer SUPER_ADMIN_TOKEN"
```

---

## Troubleshooting

### Session Expired Error

**Problem:**
```json
{
  "detail": "Session expired. Another login detected from different location."
}
```

**Solutions:**
1. Logout and login again
2. Check if someone else logged in
3. Verify device/IP hasn't changed unexpectedly

### OTP Not Received

**Problem:** OTP not arriving in Telegram

**Solutions:**
1. Check Telegram bot token
2. Verify chat ID correct
3. Check bot has permissions
4. Review server logs
5. Check network connectivity

### Account Expired

**Problem:**
```json
{
  "detail": "Account expired on 2025-12-31. Please contact administrator."
}
```

**Solutions:**
1. Contact Super Admin
2. Request expiry extension
3. Create new account

### Invalid Token

**Problem:**
```json
{
  "detail": "Could not validate credentials"
}
```

**Solutions:**
1. Check token format
2. Verify not expired
3. Login again
4. Check Authorization header format

---

## Examples

### Complete Login Flow (Python)

```python
import requests

BASE_URL = "http://localhost:8000"

# Step 1: Request OTP
response = requests.post(f"{BASE_URL}/auth/login", json={
    "username": "admin",
    "password": "secure_password"
})

if response.status_code == 200:
    data = response.json()
    temp_token = data["temp_token"]
    print("Check Telegram for OTP")
    
    # Step 2: Verify OTP
    otp_code = input("Enter OTP: ")
    
    response = requests.post(f"{BASE_URL}/auth/verify-2fa", json={
        "username": "admin",
        "otp_code": otp_code,
        "temp_token": temp_token,
        "fcm_token": "optional_fcm_token"
    })
    
    if response.status_code == 200:
        data = response.json()
        access_token = data["access_token"]
        print(f"Login successful! Token: {access_token}")
        
        # Use token
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{BASE_URL}/api/devices", headers=headers)
        print(response.json())
    else:
        print(f"OTP verification failed: {response.json()}")
else:
    print(f"Login failed: {response.json()}")
```

### Logout Example

```python
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.post(f"{BASE_URL}/auth/logout", headers=headers)
print(response.json())  # {"message": "Logged out successfully"}
```

---

**Last Updated:** November 2, 2025  
**Version:** 2.0.0
