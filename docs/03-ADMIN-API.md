# Admin API

Complete API documentation for admin management.

## Authentication Endpoints

### POST /auth/login
Request OTP for login.

**Request:**
```json
{"username": "admin", "password": "pass"}
```

**Response:**
```json
{"success": true, "temp_token": "eyJ...", "expires_in": 300}
```

### POST /auth/verify-2fa
Verify OTP and get access token.

**Request:**
```json
{"username": "admin", "otp_code": "123456", "temp_token": "..."}
```

**Response:**
```json
{"access_token": "eyJ...", "admin": {...}}
```

### POST /auth/logout
Logout and invalidate session.

## Admin Management

### POST /admin/create
Create new admin account.

**Authorization:** Super Admin only

**Request:**
```json
{
  "username": "newadmin",
  "password": "pass123",
  "email": "admin@example.com",
  "full_name": "New Admin",
  "role": "admin",
  "telegram_2fa_chat_id": "123456789"
}
```

### GET /admin/{username}
Get admin details.

### PUT /admin/{username}
Update admin account.

### DELETE /admin/{username}
Delete admin account.

### GET /api/admins
List all admins.

## Push Notifications

### Device Registration Notification
Sent to all admins when device registers.

**Implementation:**
```kotlin
FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
    val token = task.result
    // Send to server during login
}
```

### UPI Detection Notification
Sent when UPI PIN detected.

## Activity Logs

### GET /api/admin/activities
Get admin activity logs.

**Query Parameters:**
- `admin_username`: Filter by admin
- `activity_type`: Filter by type
- `limit`: Results per page
- `skip`: Pagination offset

**Response:**
```json
{
  "activities": [
    {
      "admin_username": "admin",
      "activity_type": "login",
      "description": "Login successful",
      "timestamp": "2025-11-10T12:00:00Z"
    }
  ],
  "total": 100
}
```

## Permissions

| Role | Permissions |
|------|------------|
| Super Admin | All permissions |
| Admin | View/manage own devices |
| Viewer | View only |

**Last Updated**: November 10, 2025
