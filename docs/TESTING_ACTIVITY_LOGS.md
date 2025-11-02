# Testing Activity Logs & Telegram Notifications

Quick guide to test admin activity logging and Telegram notifications.

---

## Overview

All admin activities are now:
1. ? Logged to MongoDB database
2. ? Sent to Telegram Bot 3 (Admin Activity) in real-time

---

## Test Scenarios

### Scenario 1: Login Activity

**Test:**
```bash
# Step 1: Request OTP
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Step 2: Verify OTP (get from Telegram)
curl -X POST "http://localhost:8000/auth/verify-2fa" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "otp_code": "123456",
    "temp_token": "TEMP_TOKEN_FROM_STEP1"
  }'
```

**Expected Telegram Notification (Bot 3):**
```
?? Admin Activity

?? Admin: admin
?? Action: login
?? Details: Login step 2: OTP verified, login complete
?? IP: 192.168.1.100
? Time: 2025-11-02 10:30:00 UTC
```

**Check Database:**
```javascript
db.admin_activities.find({admin_username: "admin", activity_type: "login"}).sort({timestamp: -1}).limit(1)
```

---

### Scenario 2: Send Command Activity

**Test:**
```bash
curl -X POST "http://localhost:8000/api/devices/abc123/command" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"command": "ping"}'
```

**Expected Telegram Notification (Bot 3):**
```
?? Admin Activity

?? Admin: admin
?? Action: send_command
?? Details: Sent Firebase ping to device: abc123
?? Device: abc123
?? IP: 192.168.1.100
? Time: 2025-11-02 10:35:00 UTC
```

---

### Scenario 3: View SMS Activity

**Test:**
```bash
curl -X GET "http://localhost:8000/api/devices/abc123/sms" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected Telegram Notification (Bot 3):**
```
?? Admin Activity

?? Admin: admin
?? Action: view_sms
?? Details: Viewed SMS for device: abc123
?? Device: abc123
?? IP: 192.168.1.100
? Time: 2025-11-02 10:40:00 UTC
```

---

### Scenario 4: Create Admin Activity (Super Admin)

**Test:**
```bash
curl -X POST "http://localhost:8000/admin/create" \
  -H "Authorization: Bearer SUPER_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newadmin",
    "password": "pass123",
    "email": "new@example.com",
    "full_name": "New Admin",
    "role": "admin"
  }'
```

**Expected Telegram Notification (Bot 3):**
```
?? Admin Activity

?? Admin: superadmin
?? Action: create_admin
?? Details: Created new admin: newadmin
?? IP: 192.168.1.100
? Time: 2025-11-02 11:00:00 UTC
```

---

## Verification Steps

### 1. Check Server Logs

```bash
tail -f logs/app.log | grep "Activity logged"
```

**Expected output:**
```
2025-11-02 10:30:00 - app.services.admin_activity_service - INFO - ?? Activity logged: admin - login
2025-11-02 10:30:00 - app.services.admin_activity_service - DEBUG - ?? Telegram notification sent for activity: login
```

### 2. Check MongoDB

```javascript
// Connect to MongoDB
use parental_control

// View recent activities
db.admin_activities.find().sort({timestamp: -1}).limit(10).pretty()

// Count by type
db.admin_activities.aggregate([
  {$group: {_id: "$activity_type", count: {$sum: 1}}},
  {$sort: {count: -1}}
])
```

### 3. Check Telegram Bot 3

**For Admin:**
- Open Telegram
- Go to Bot 3 chat for your admin
- Should see activity notifications

**For Super Admin:**
- Open Bot 3 chat
- Should see ALL admin activities

---

## Troubleshooting

### No Telegram Notification Received

**Check 1: Bot 3 Configuration**
```bash
# Query admin's telegram bots
curl -X GET "http://localhost:8000/admin/admin" \
  -H "Authorization: Bearer SUPER_ADMIN_TOKEN" | jq '.telegram_bots[] | select(.bot_id == 3)'
```

**Expected:**
```json
{
  "bot_id": 3,
  "bot_name": "Admin Activity",
  "token": "BOT_TOKEN_HERE",
  "chat_id": "CHAT_ID_HERE"
}
```

**Check 2: Server Logs**
```bash
tail -f logs/app.log | grep -E "Telegram notification|Activity logged"
```

**Check 3: Telegram Service**
```bash
# Check if telegram_multi_service initialized
grep "TelegramMultiService initialized" logs/app.log
```

**Check 4: notify_admin_action Method**
```python
# Test directly
from app.services.telegram_multi_service import telegram_multi_service
import asyncio

asyncio.run(telegram_multi_service.notify_admin_action(
    admin_username="admin",
    action="test",
    details="Test notification",
    ip_address="127.0.0.1"
))
```

### Activities Logged but No Telegram

**Possible Causes:**
1. Bot 3 token invalid
2. Chat ID incorrect
3. Bot blocked by user
4. Network issues

**Solution:**
```bash
# Check Telegram bot status
curl "https://api.telegram.org/bot<BOT_TOKEN>/getMe"

# Test sending message
curl "https://api.telegram.org/bot<BOT_TOKEN>/sendMessage?chat_id=<CHAT_ID>&text=Test"
```

### Circular Import Error

**If you see:**
```
ImportError: cannot import name 'telegram_multi_service'
```

**Don't worry:** We use lazy import inside the function, so this shouldn't happen.

**If it does:**
```python
# The import is inside log_activity function
if send_telegram:
    from .telegram_multi_service import telegram_multi_service  # Lazy import
    await telegram_multi_service.notify_admin_action(...)
```

---

## Testing with Postman

### Collection Variables
```json
{
  "base_url": "http://localhost:8000",
  "admin_token": "your_access_token_here"
}
```

### Test Requests

**1. Login and Check Telegram:**
```
POST {{base_url}}/auth/login
{
  "username": "admin",
  "password": "password"
}
```
? Check Bot 3 for login activity

**2. Send Command and Check Telegram:**
```
POST {{base_url}}/api/devices/abc123/command
Authorization: Bearer {{admin_token}}
{
  "command": "ping"
}
```
? Check Bot 3 for command activity

**3. View Devices and Check Telegram:**
```
GET {{base_url}}/api/devices
Authorization: Bearer {{admin_token}}
```
? Check Bot 3 for view_device activity

---

## Expected Results

### For Each Activity

**1. Database:**
```javascript
{
  "admin_username": "admin",
  "activity_type": "send_command",
  "description": "Sent ping to device: abc123",
  "ip_address": "192.168.1.100",
  "device_id": "abc123",
  "success": true,
  "timestamp": ISODate("2025-11-02T10:35:00Z")
}
```

**2. Telegram (Bot 3):**
```
?? Admin Activity
?? Admin: admin
?? Action: send_command
?? Details: Sent ping to device: abc123
?? Device: abc123
?? IP: 192.168.1.100
? Time: 2025-11-02 10:35:00 UTC
```

**3. Server Logs:**
```
2025-11-02 10:35:00 - INFO - ?? Activity logged: admin - send_command
2025-11-02 10:35:00 - DEBUG - ?? Telegram notification sent for activity: send_command
```

---

## Performance Notes

**Activity Logging:**
- Async operation (non-blocking)
- Telegram errors don't block logging
- ~50ms average latency per activity

**Telegram Notification:**
- Sent in background
- Doesn't delay API response
- Retries on network errors

**Database Impact:**
- Lightweight documents (~500 bytes each)
- Indexed by admin_username and timestamp
- Auto-cleanup after 90 days

---

## Summary

? **All admin activities** automatically logged  
? **Real-time Telegram notifications** to Bot 3  
? **Dual delivery** - Admin + Super Admin  
? **Error resilient** - Telegram failures don't block logging  
? **Complete audit trail** - All actions tracked  

**Test it now:**
1. Login to admin panel
2. Perform any action
3. Check Bot 3 in Telegram
4. Should see notification instantly!

---

**Last Updated:** November 2, 2025  
**Version:** 2.0.0
