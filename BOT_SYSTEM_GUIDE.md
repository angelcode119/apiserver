# ?? Telegram Bot System Guide

Complete guide to the multi-bot notification system.

## Table of Contents

1. [System Overview](#system-overview)
2. [Bot Types](#bot-types)
3. [Bot Assignment](#bot-assignment)
4. [Administrator Notifications](#administrator-notifications)
5. [Configuration](#configuration)
6. [Examples](#examples)

---

## System Overview

The system uses **6 types of Telegram bots**:

### 1. One Shared 2FA Bot
- **Purpose:** OTP codes for authentication
- **Token:** Shared (in `.env`)
- **Chat ID:** Personal per admin (`telegram_2fa_chat_id`)

### 2. Five Activity Bots (per admin)
- **Purpose:** Different notification types
- **Token:** Unique per bot
- **Chat ID:** Unique per bot

```
Each admin has:
??? telegram_2fa_chat_id (for 2FA bot)
??? 5 activity bots
    ??? Bot 1: Device notifications
    ??? Bot 2: SMS notifications
    ??? Bot 3: Admin activity logs
    ??? Bot 4: Login/Logout logs
    ??? Bot 5: Future use (app builds)
```

---

## Bot Types

### ?? 2FA Bot (Shared)

**Configuration:**
- Token: `TELEGRAM_2FA_BOT_TOKEN` in `.env`
- Chat ID: `telegram_2fa_chat_id` per admin (in database)

**Sends:**
- ? OTP codes (6-digit numbers)
- ? Login authentication requests
- ? Logout notifications

**Example Message:**
```
?? Two-Factor Authentication

?? Admin: user1
?? IP: 192.168.1.100
?? Code: 123456
?? Time: 2025-10-31 10:00:00 UTC
```

---

### ?? Bot 1 - Device Notifications

**Sends:**
- ? Device registered
- ? Device online/offline
- ? Device status changes
- ? Data uploads (SMS, contacts)

**Example Message:**
```
?? New Device Registered

?? Admin: user1
?? Device ID: SAMSUNG-A20-123456
?? Model: Samsung Galaxy A20
?? Manufacturer: Samsung
?? OS: Android 11
?? Time: 2025-10-31 10:00:00 UTC

? Device is now being monitored!
```

**Configuration:**
```json
{
  "bot_id": 1,
  "bot_name": "user1_devices",
  "token": "1111111111:AAA_USER1_BOT1",
  "chat_id": "-1001111111111"
}
```

---

### ?? Bot 2 - SMS Notifications

**Sends:**
- ? New SMS received (ONLY)

**Example Message:**
```
?? New SMS Received

?? Admin: user1
?? Device: SAMSUNG-A20-123456
?? From: +989121234567
?? Preview: Hello! Your verification code is 123456...
?? Time: 2025-10-31 10:15:00 UTC
```

**Configuration:**
```json
{
  "bot_id": 2,
  "bot_name": "user1_sms",
  "token": "2222222222:BBB_USER1_BOT2",
  "chat_id": "-1002222222222"
}
```

---

### ?? Bot 3 - Admin Activity Logs

**Sends:**
- ? Command sent to device
- ? New admin created
- ? Settings changed
- ? Device deleted
- ? Any admin action

**Example Message:**
```
?? Command Sent

?? Admin: user1
?? Device: SAMSUNG-A20-123456
? Command: get_location
?? Time: 2025-10-31 11:00:00 UTC
```

**Configuration:**
```json
{
  "bot_id": 3,
  "bot_name": "user1_logs",
  "token": "3333333333:CCC_USER1_BOT3",
  "chat_id": "-1003333333333"
}
```

---

### ?? Bot 4 - Login/Logout Logs

**Sends:**
- ? Successful login
- ? Failed login
- ? Logout

**Example Message:**
```
? Admin Login Successful

?? Username: user1
?? IP: 192.168.1.100
?? Time: 2025-10-31 09:00:00 UTC
```

**Configuration:**
```json
{
  "bot_id": 4,
  "bot_name": "user1_auth",
  "token": "4444444444:DDD_USER1_BOT4",
  "chat_id": "-1004444444444"
}
```

---

### ?? Bot 5 - Future Use

**Purpose:** App builds, system reports, etc.

**Status:** Currently unused

**Configuration:**
```json
{
  "bot_id": 5,
  "bot_name": "user1_builds",
  "token": "5555555555:EEE_USER1_BOT5",
  "chat_id": "-1005555555555"
}
```

---

## Bot Assignment

### Event ? Bot Mapping

| Event | 2FA Bot | Bot 1 | Bot 2 | Bot 3 | Bot 4 | Bot 5 |
|-------|---------|-------|-------|-------|-------|-------|
| **OTP Code** | ? | ? | ? | ? | ? | ? |
| **Device Registered** | ? | ? | ? | ? | ? | ? |
| **Device Online/Offline** | ? | ? | ? | ? | ? | ? |
| **New SMS** | ? | ? | ? | ? | ? | ? |
| **Command Sent** | ? | ? | ? | ? | ? | ? |
| **Admin Created** | ? | ? | ? | ? | ? | ? |
| **Admin Login** | ? | ? | ? | ? | ? | ? |
| **Admin Logout** | ? | ? | ? | ? | ? | ? |
| **App Build** | ? | ? | ? | ? | ? | ?? |

---

## Administrator Notifications

### How It Works

**Administrator (Super Admin)** receives ALL notifications from ALL admins, but **segregated by bot type**.

### Example Flow

**Event:** user1 registers a device

```
Step 1: Notify device owner (user1)
??? Bot 1 user1 (token: AAA, chat_id: -1001111111111)
??? Message: "Device registered by user1"

Step 2: Notify Administrator
??? Bot 1 admin (token: ZZZ, chat_id: -1009991111111)
??? Same message: "Device registered by user1"
```

### Benefits

**Segregated Notifications:**
```
Administrator's Chat Organization:
??? Chat 1 (Bot 1): All device activities from all admins
??? Chat 2 (Bot 2): All SMS from all devices
??? Chat 3 (Bot 3): All admin actions
??? Chat 4 (Bot 4): All login/logout activities
??? Chat 5 (Bot 5): Future use
```

**Easy Filtering:**
- Want to see only SMS? ? Open Bot 2 chat
- Want to see only logins? ? Open Bot 4 chat
- Want to see device activities? ? Open Bot 1 chat

### Duplicate Prevention

If Administrator performs an action, they receive notification only once:
```python
exclude_username=admin_username
# Prevents duplicate notifications
```

---

## Configuration

### Admin Database Structure

```json
{
  "username": "user1",
  "role": "admin",
  
  "device_token": "abc123def456...",
  
  "telegram_2fa_chat_id": "-1001234567890",
  
  "telegram_bots": [
    {
      "bot_id": 1,
      "bot_name": "user1_devices",
      "token": "1111111111:AAA_USER1_BOT1",
      "chat_id": "-1001111111111"
    },
    {
      "bot_id": 2,
      "bot_name": "user1_sms",
      "token": "2222222222:BBB_USER1_BOT2",
      "chat_id": "-1002222222222"
    },
    {
      "bot_id": 3,
      "bot_name": "user1_logs",
      "token": "3333333333:CCC_USER1_BOT3",
      "chat_id": "-1003333333333"
    },
    {
      "bot_id": 4,
      "bot_name": "user1_auth",
      "token": "4444444444:DDD_USER1_BOT4",
      "chat_id": "-1004444444444"
    },
    {
      "bot_id": 5,
      "bot_name": "user1_builds",
      "token": "5555555555:EEE_USER1_BOT5",
      "chat_id": "-1005555555555"
    }
  ]
}
```

### Can I Use Same Chat ID for All Bots?

**Yes!** You can set all 5 bots to use the same `chat_id`:

```json
{
  "telegram_bots": [
    {"bot_id": 1, "token": "AAA...", "chat_id": "-1001111111111"},
    {"bot_id": 2, "token": "BBB...", "chat_id": "-1001111111111"},
    {"bot_id": 3, "token": "CCC...", "chat_id": "-1001111111111"},
    {"bot_id": 4, "token": "DDD...", "chat_id": "-1001111111111"},
    {"bot_id": 5, "token": "EEE...", "chat_id": "-1001111111111"}
  ]
}
```

All notifications will arrive in one chat, but you can still see which bot sent it.

---

## Examples

### Example 1: New Admin Registration

**API Request:**
```bash
POST /admin/create

{
  "username": "user1",
  "email": "user1@example.com",
  "password": "password123",
  "telegram_2fa_chat_id": "-1001001001001",
  "telegram_bots": [
    {
      "bot_id": 1,
      "bot_name": "user1_devices",
      "token": "1111111111:AAA",
      "chat_id": "-1001111111111"
    },
    ... (4 more)
  ]
}
```

**What Happens:**
1. Admin created in database
2. Device token generated: `abc123def456...`
3. Notification sent to:
   - Super Admin's Bot 3 (admin creation log)

---

### Example 2: Device Registration

**Android App Request:**
```bash
POST /register

{
  "device_id": "SAMSUNG-A20-123456",
  "device_info": {...},
  "admin_token": "abc123def456..."
}
```

**What Happens:**
1. Device linked to user1 (owner of token)
2. Notification sent to:
   - user1's Bot 1 (device owner)
   - admin's Bot 1 (Super Admin)

**user1 receives:**
```
?? New Device Registered
?? Admin: user1
?? Device ID: SAMSUNG-A20-123456
```

**admin receives:**
```
?? New Device Registered
?? Admin: user1
?? Device ID: SAMSUNG-A20-123456
```

---

### Example 3: SMS Received

**Android App Sends:**
```bash
POST /devices/save/sms

{
  "device_id": "SAMSUNG-A20-123456",
  "sms_data": [{
    "address": "+989121234567",
    "body": "Your code is 123456",
    ...
  }]
}
```

**What Happens:**
1. SMS saved to database
2. Notification sent to:
   - user1's Bot 2 (device owner)
   - admin's Bot 2 (Super Admin)

**Both receive:**
```
?? New SMS Received
?? Admin: user1
?? Device: SAMSUNG-A20-123456
?? From: +989121234567
?? Preview: Your code is 123456
```

---

### Example 4: user1 Logs In

**Login Request:**
```bash
POST /auth/login

{
  "username": "user1",
  "password": "password123"
}
```

**What Happens:**

**Step 1: 2FA Notification**
```
?? 2FA Bot (shared token)
   ? Sends to: user1's telegram_2fa_chat_id
   
Message:
?? Two-Factor Authentication
?? Admin: user1
?? IP: 192.168.1.100
```

**Step 2: Login Log**
```
Bot 4 user1
   ? Sends to: user1's Bot 4 chat_id

Bot 4 admin
   ? Sends to: admin's Bot 4 chat_id

Message:
? Admin Login Successful
?? Username: user1
?? IP: 192.168.1.100
```

---

## Summary

### Key Points

1. **Each bot serves a specific purpose**
   - Bot 1: Devices
   - Bot 2: SMS only
   - Bot 3: Admin actions
   - Bot 4: Login/Logout
   - Bot 5: Future

2. **Each bot has its own token + chat_id**
   - Independent configuration
   - Can use same chat_id for all

3. **Administrator sees everything**
   - Segregated by bot type
   - Easy to filter

4. **2FA is separate**
   - Shared token
   - Personal chat_id per admin

### Configuration Checklist

```
? Create 2FA bot
? Get 2FA bot token
? Get personal chat_id for 2FA
? Create 5 activity bots per admin
? Get token for each activity bot
? Get chat_id for each activity bot
? Configure in admin profile
? Test notifications
```

---

**For setup instructions, see: SETUP_GUIDE.md**
