# 2FA Telegram Setup Guide

Complete guide for setting up personal 2FA Telegram bots for each admin.

---

## Overview

Each admin receives their **OTP codes via their personal Bot 4 (2FA)**, not a shared channel. This ensures:
- ? **Privacy** - Each admin sees only their own OTP codes
- ? **Security** - No shared channel with multiple admins
- ? **Personal Chat** - Direct message to admin's Telegram account
- ? **No Confusion** - Clear separation of admin accounts

---

## Bot Assignment

| Bot ID | Purpose | Example Notification |
|--------|---------|---------------------|
| Bot 1 | Device Notifications | New device registered, UPI detected |
| Bot 2 | SMS Notifications | New SMS received |
| Bot 3 | Admin Activity | Admin actions, device status |
| **Bot 4** | **2FA & Login/Logout** | **OTP codes, login events** |
| Bot 5 | Reserved | Future use |

---

## Setup Process

### Step 1: Create Bot via @BotFather

1. Open Telegram and search for `@BotFather`
2. Send command: `/newbot`
3. Choose a name: `Admin John 2FA Bot`
4. Choose username: `admin_john_2fa_bot`
5. **Save the token**: `7891234567:AAH-XxXxXxXxXxXxXxXxXxXxXxXxXxXx`

**Example:**
```
BotFather: Alright, a new bot. How are we going to call it?
You: Admin John 2FA Bot

BotFather: Good. Now let's choose a username for your bot.
You: admin_john_2fa_bot

BotFather: Done! Congratulations on your new bot.
Token: 7891234567:AAH-XxXxXxXxXxXxXxXxXxXxXxXxXxXx
```

### Step 2: Get Chat ID

**Option A: Using Bot**
1. Search for your new bot in Telegram
2. Click Start or send: `/start`
3. Go to: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
4. Find `"chat":{"id":123456789}`

**Example URL:**
```
https://api.telegram.org/bot7891234567:AAH-XxXxXxXxXxXxXxXxXxXxXxXxXxXx/getUpdates
```

**Example Response:**
```json
{
  "ok": true,
  "result": [
    {
      "update_id": 123456,
      "message": {
        "message_id": 1,
        "from": {
          "id": 123456789,
          "is_bot": false,
          "first_name": "John",
          "username": "johndoe"
        },
        "chat": {
          "id": 123456789,  ? THIS IS YOUR CHAT ID
          "first_name": "John",
          "username": "johndoe",
          "type": "private"
        },
        "text": "/start"
      }
    }
  ]
}
```

**Option B: Using @userinfobot**
1. Search for `@userinfobot` in Telegram
2. Send any message
3. Bot will reply with your chat ID

### Step 3: Create Admin with Bot 4

**Using cURL:**
```bash
curl -X POST "http://your-server:8000/admin/create" \
  -H "Authorization: Bearer SUPER_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "password": "securepass123",
    "email": "john@example.com",
    "full_name": "John Doe",
    "role": "admin",
    "telegram_bots": [
      {
        "bot_id": 4,
        "bot_name": "2FA & Login",
        "token": "7891234567:AAH-XxXxXxXxXxXxXxXxXxXxXxXxXxXx",
        "chat_id": "123456789"
      }
    ]
  }'
```

**Using Python:**
```python
import requests

url = "http://your-server:8000/admin/create"
headers = {
    "Authorization": "Bearer SUPER_ADMIN_TOKEN",
    "Content-Type": "application/json"
}
data = {
    "username": "john",
    "password": "securepass123",
    "email": "john@example.com",
    "full_name": "John Doe",
    "role": "admin",
    "telegram_bots": [
        {
            "bot_id": 4,
            "bot_name": "2FA & Login",
            "token": "7891234567:AAH-XxXxXxXxXxXxXxXxXxXxXxXxXxXx",
            "chat_id": "123456789"
        }
    ]
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

### Step 4: Test the Setup

**1. Login:**
```bash
curl -X POST "http://your-server:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "password": "securepass123"
  }'
```

**2. Check Telegram Bot:**

You should receive a message in your personal bot:

```
?? Two-Factor Authentication

?? Admin: john
?? IP: 192.168.1.100
?? Code: 123456
? Time: 2025-11-02 10:30:00 UTC
```

**3. Verify OTP:**
```bash
curl -X POST "http://your-server:8000/auth/verify-2fa" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "otp_code": "123456",
    "temp_token": "TEMP_TOKEN_FROM_LOGIN_RESPONSE"
  }'
```

---

## Adding Bot 4 to Existing Admin

If you already created an admin without Bot 4, update it:

```bash
curl -X PUT "http://your-server:8000/admin/john" \
  -H "Authorization: Bearer SUPER_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_bots": [
      {
        "bot_id": 4,
        "bot_name": "2FA & Login",
        "token": "7891234567:AAH-XxXxXxXxXxXxXxXxXxXxXxXxXxXx",
        "chat_id": "123456789"
      }
    ]
  }'
```

**Note:** This will **replace** existing telegram_bots. To add Bot 4 without removing others, include all bots in the array.

---

## Complete Bot Setup (All 4 Bots)

For best experience, configure all 4 bots for each admin:

```json
{
  "username": "john",
  "password": "securepass123",
  "email": "john@example.com",
  "full_name": "John Doe",
  "role": "admin",
  "telegram_bots": [
    {
      "bot_id": 1,
      "bot_name": "Device Notifications",
      "token": "BOT1_TOKEN_HERE",
      "chat_id": "JOHN_CHAT_ID"
    },
    {
      "bot_id": 2,
      "bot_name": "SMS Notifications",
      "token": "BOT2_TOKEN_HERE",
      "chat_id": "JOHN_CHAT_ID"
    },
    {
      "bot_id": 3,
      "bot_name": "Admin Activity",
      "token": "BOT3_TOKEN_HERE",
      "chat_id": "JOHN_CHAT_ID"
    },
    {
      "bot_id": 4,
      "bot_name": "2FA & Login",
      "token": "BOT4_TOKEN_HERE",
      "chat_id": "JOHN_CHAT_ID"
    }
  ]
}
```

**Options:**
- **Separate Bots**: Create 4 different bots (recommended for organization)
- **Single Bot**: Use same bot token, different chat IDs
- **Mixed**: Some bots shared, Bot 4 always personal

---

## Technical Details

### How It Works

**Old Behavior (WRONG):**
```python
# Sent to shared channel
await self._send_message_to_chat(
    self.twofa_bot_token,    # Shared bot token
    self.twofa_chat_id,      # Shared channel ID
    message
)
```

**New Behavior (CORRECT):**
```python
# Get admin's personal Bot 4
admin = await mongodb.db.admins.find_one({"username": admin_username})
bot_4 = next(bot for bot in admin["telegram_bots"] if bot["bot_id"] == 4)

# Send to admin's personal chat
await self._send_message_to_chat(
    bot_4["token"],          # Admin's Bot 4 token
    bot_4["chat_id"],        # Admin's personal chat ID
    message
)
```

### Message Format

**2FA OTP Message:**
```
?? Two-Factor Authentication

?? Admin: {username}
?? IP: {ip_address}
?? Code: {otp_code}
? Time: {timestamp} UTC
```

**Login Success Message:**
```
? Admin Login Successful

?? Username: {username}
?? IP: {ip_address}
? Time: {timestamp} UTC
```

**Logout Message:**
```
?? Admin Logged Out

?? Username: {username}
?? IP: {ip_address}
? Time: {timestamp} UTC
```

---

## Troubleshooting

### Issue: OTP Not Received

**Check 1: Bot 4 Configured?**
```bash
curl -X GET "http://your-server:8000/admin/john" \
  -H "Authorization: Bearer SUPER_ADMIN_TOKEN" | jq '.telegram_bots[] | select(.bot_id == 4)'
```

**Expected:**
```json
{
  "bot_id": 4,
  "bot_name": "2FA & Login",
  "token": "7891234567:AAH...",
  "chat_id": "123456789"
}
```

**If empty:** Bot 4 not configured, add it using PUT /admin/{username}

**Check 2: Server Logs**
```bash
tail -f logs/app.log | grep "2FA"
```

**Expected:**
```
2025-11-02 10:30:00 - INFO - ?? 2FA code sent to john
```

**If you see:**
```
??  Bot 4 (2FA) not configured for admin: john
```
? Bot 4 is missing in admin's telegram_bots array

**Check 3: Bot Token Valid?**
```bash
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"
```

**Expected:**
```json
{
  "ok": true,
  "result": {
    "id": 7891234567,
    "is_bot": true,
    "first_name": "Admin John 2FA Bot",
    "username": "admin_john_2fa_bot"
  }
}
```

**If error:** Token is invalid, get new token from @BotFather

**Check 4: Started Bot?**

You must send `/start` to the bot before it can message you!

**Fix:**
1. Open bot in Telegram
2. Click "START" button or send `/start`
3. Try login again

### Issue: Gets Channel Message Instead of Personal

**This was the old bug, now fixed!**

If you still see this:
1. Make sure you're running latest code
2. Restart server: `systemctl restart parental-control`
3. Check that `send_2fa_notification` uses admin's Bot 4, not global config

### Issue: Multiple Admins Share Same Bot

**Acceptable if:**
- Each admin has **different chat_id**
- Example:
  ```
  Admin John: bot_4.chat_id = "123456789"  (John's personal chat)
  Admin Jane: bot_4.chat_id = "987654321"  (Jane's personal chat)
  ```

**Not acceptable if:**
- Both admins have **same chat_id** ? Both will see each other's OTPs!

---

## Security Best Practices

### ? DO:
- Use personal chat ID for each admin
- Keep bot tokens secret
- Use different bots for different admins (recommended)
- Regularly rotate bot tokens
- Monitor unauthorized access attempts

### ? DON'T:
- Share bot tokens publicly
- Use channel IDs for 2FA
- Share chat IDs between admins
- Commit tokens to git
- Store tokens in plain text config files

---

## Environment Variables

Add to `.env`:

```bash
# Legacy - Not used anymore for personal OTPs
# TWOFA_BOT_TOKEN=...
# TWOFA_CHAT_ID=...

# Each admin has personal bot in database
# No global config needed!
```

**Migration:** Remove old `TWOFA_BOT_TOKEN` and `TWOFA_CHAT_ID` from config, they're not used anymore.

---

## FAQ

**Q: Can I use one bot for all admins?**  
A: Yes, but each admin must have a **unique chat_id**. The bot token can be the same.

**Q: What if admin doesn't have Bot 4?**  
A: Login will work, but OTP won't be sent. Admin can't complete 2FA verification.

**Q: Can I disable 2FA for some admins?**  
A: Yes, set `require_2fa=False` in admin settings. They'll login without OTP.

**Q: Bot Authentication (for Telegram bots) also uses this?**  
A: Yes! Bot auth also sends OTP via admin's Bot 4.

**Q: Can Super Admin see other admins' OTPs?**  
A: No! Each admin receives OTP in their own Bot 4 chat. Super Admin sees login notifications (without OTP) in their Bot 4.

**Q: What about Bot 3 for activity logs?**  
A: Bot 3 sends activity notifications to both the acting admin AND Super Admin. But Bot 4 (2FA) only goes to the authenticating admin.

**Q: Old OTPs going to channel, how to fix?**  
A: Upgrade to latest code. The issue is fixed. `send_2fa_notification` now uses personal Bot 4.

---

## Testing Checklist

- [ ] Bot created via @BotFather
- [ ] Bot token saved
- [ ] Sent /start to bot
- [ ] Chat ID obtained
- [ ] Admin created with Bot 4
- [ ] Login attempted
- [ ] OTP received in personal bot
- [ ] OTP verification successful
- [ ] Login success notification received
- [ ] Logout notification received

---

**Last Updated:** November 2, 2025  
**Version:** 2.0.0  
**Status:** ? Fixed - Personal Bot 4 for each admin
