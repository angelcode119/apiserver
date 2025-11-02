# 2FA Telegram Setup Guide

Simple guide for setting up 2FA Telegram notifications with one bot for all admins.

---

## Overview

**One Bot, Multiple Admins:**
- ? Single 2FA bot for entire system
- ? Each admin has personal `telegram_2fa_chat_id`
- ? OTP sent to admin's personal chat
- ? No shared channels - complete privacy

---

## Architecture

```
???????????????????????????????????????????????
?         System 2FA Bot (ONE)                ?
?         Token: 7891234567:AAH...            ?
???????????????????????????????????????????????
             ?
    ????????????????????????????????
    ?                 ?            ?
    ?                 ?            ?
???????????      ???????????  ???????????
? John    ?      ? Jane    ?  ? Bob     ?
? Chat:   ?      ? Chat:   ?  ? Chat:   ?
? 1234567 ?      ? 9876543 ?  ? 5556667 ?
???????????      ???????????  ???????????
```

**How it works:**
1. One bot token in `.env` file
2. Each admin has unique chat ID in database
3. OTP sent to admin's chat using same bot

---

## Setup Process

### Step 1: Create System 2FA Bot

**1. Go to @BotFather in Telegram:**
```
/newbot
```

**2. Set bot name:**
```
Name: System 2FA Bot
Username: system_2fa_bot
```

**3. Save the token:**
```
Token: 7891234567:AAH-XxXxXxXxXxXxXxXxXxXxXxXxXxXx
```

### Step 2: Configure Bot in .env

Add to your `.env` file:

```bash
# 2FA Bot Configuration
TELEGRAM_2FA_BOT_TOKEN=7891234567:AAH-XxXxXxXxXxXxXxXxXxXxXxXxXxXx
```

**Restart server:**
```bash
sudo systemctl restart your-service
```

### Step 3: Get Chat IDs for Each Admin

**For each admin who needs 2FA:**

1. **Admin sends `/start` to bot**
   - Open Telegram
   - Search: `@system_2fa_bot`
   - Send: `/start`

2. **Get chat ID via API:**
   ```bash
   curl "https://api.telegram.org/bot7891234567:AAH.../getUpdates"
   ```

3. **Find chat.id in response:**
   ```json
   {
     "ok": true,
     "result": [
       {
         "message": {
           "chat": {
             "id": 123456789,  ? THIS IS THE CHAT ID
             "first_name": "John",
             "type": "private"
           }
         }
       }
     ]
   }
   ```

**Alternative: Use @userinfobot**
- Search for `@userinfobot`
- Send any message
- Bot replies with your chat ID

### Step 4: Create Admin with Chat ID

**Example for Admin "John":**

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
    "telegram_2fa_chat_id": "123456789"
  }'
```

**Python example:**
```python
import requests

url = "http://your-server:8000/admin/create"
headers = {
    "Authorization": "Bearer SUPER_ADMIN_TOKEN",
    "Content-Type": "application/json"
}

# Create multiple admins
admins = [
    {
        "username": "john",
        "telegram_2fa_chat_id": "123456789",
        "email": "john@example.com",
        "full_name": "John Doe",
        "password": "pass123",
        "role": "admin"
    },
    {
        "username": "jane",
        "telegram_2fa_chat_id": "987654321",
        "email": "jane@example.com",
        "full_name": "Jane Smith",
        "password": "pass456",
        "role": "admin"
    }
]

for admin_data in admins:
    response = requests.post(url, headers=headers, json=admin_data)
    print(f"Created: {admin_data['username']} - {response.status_code}")
```

### Step 5: Test the Setup

**1. Admin Login:**
```bash
curl -X POST "http://your-server:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "password": "securepass123"
  }'
```

**2. Check Telegram:**

John should receive in his personal chat with the bot:

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
    "temp_token": "TEMP_TOKEN_FROM_LOGIN"
  }'
```

**Success!** ?

---

## Adding Chat ID to Existing Admin

If admin already exists without `telegram_2fa_chat_id`:

```bash
curl -X PUT "http://your-server:8000/admin/john" \
  -H "Authorization: Bearer SUPER_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "telegram_2fa_chat_id": "123456789"
  }'
```

---

## Database Structure

**Admin Document:**
```json
{
  "username": "john",
  "email": "john@example.com",
  "full_name": "John Doe",
  "role": "admin",
  "telegram_2fa_chat_id": "123456789",  ? Personal chat ID
  "is_active": true,
  ...
}
```

**Multiple Admins:**
```json
[
  {
    "username": "john",
    "telegram_2fa_chat_id": "123456789"
  },
  {
    "username": "jane",
    "telegram_2fa_chat_id": "987654321"
  },
  {
    "username": "bob",
    "telegram_2fa_chat_id": "555666777"
  }
]
```

All use same bot token from `.env`!

---

## Message Format

**OTP Message:**
```
?? Two-Factor Authentication

?? Admin: {username}
?? IP: {ip_address}
?? Code: {otp_code}
? Time: {timestamp} UTC
```

**Bot Authentication (for Telegram bots):**
```
?? Bot Authentication Request
Bot: My Telegram Bot

?? Admin: john
?? IP: 192.168.1.100
?? Code: 123456
? Time: 2025-11-02 10:35:00 UTC
```

---

## Code Implementation

**Backend (`telegram_multi_service.py`):**

```python
async def send_2fa_notification(
    self,
    admin_username: str,
    ip_address: str,
    code: Optional[str] = None,
    message_prefix: Optional[str] = None
) -> bool:
    # Get admin's personal chat ID
    admin = await mongodb.db.admins.find_one({"username": admin_username})
    
    if not admin:
        return False
    
    telegram_2fa_chat_id = admin.get("telegram_2fa_chat_id")
    
    if not telegram_2fa_chat_id:
        logger.warning(f"telegram_2fa_chat_id not configured for {admin_username}")
        return False
    
    # Build message
    message = "?? <b>Two-Factor Authentication</b>\n\n"
    message += f"?? Admin: <code>{admin_username}</code>\n"
    message += f"?? IP: <code>{ip_address}</code>\n"
    message += f"?? Code: <code>{code}</code>\n"
    message += f"? Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
    
    # Send using global bot token + admin's chat ID
    return await self._send_message_to_chat(
        self.twofa_bot_token,    # From .env
        telegram_2fa_chat_id,     # From admin DB
        message,
        "HTML"
    )
```

**Usage:**
```python
# In login endpoint
await telegram_multi_service.send_2fa_notification(
    admin_username="john",
    ip_address="192.168.1.100",
    code="123456"
)
```

---

## Troubleshooting

### Issue: OTP Not Received

**Check 1: Bot Token Configured**
```bash
grep "TELEGRAM_2FA_BOT_TOKEN" .env
```

**Expected:**
```
TELEGRAM_2FA_BOT_TOKEN=7891234567:AAH...
```

**Check 2: Admin Chat ID Set**
```bash
# Get admin info
curl -X GET "http://your-server:8000/admin/john" \
  -H "Authorization: Bearer SUPER_ADMIN_TOKEN"
```

**Expected response:**
```json
{
  "username": "john",
  "telegram_2fa_chat_id": "123456789",
  ...
}
```

**If null:** Add chat ID using PUT endpoint

**Check 3: Server Logs**
```bash
tail -f logs/app.log | grep "2FA"
```

**Expected:**
```
2025-11-02 10:30:00 - INFO - ?? 2FA code sent to john
```

**If warning:**
```
??  telegram_2fa_chat_id not configured for admin: john
```
? Need to add chat ID to admin

**Check 4: Bot Started**
- Admin must send `/start` to bot first
- Bot can't message users who haven't started it

**Fix:**
1. Open bot in Telegram
2. Click START
3. Try login again

**Check 5: Bot Token Valid**
```bash
curl "https://api.telegram.org/bot<TOKEN>/getMe"
```

**Expected:**
```json
{
  "ok": true,
  "result": {
    "id": 7891234567,
    "is_bot": true,
    "first_name": "System 2FA Bot",
    "username": "system_2fa_bot"
  }
}
```

### Issue: Wrong Chat ID

**Symptoms:**
- Message goes to different person
- "Chat not found" error

**Solution:**
1. Verify chat ID is correct numeric value
2. Ensure admin sent `/start` to bot
3. User chat IDs are positive numbers
4. Channel IDs are negative (don't use channels!)

**Get correct chat ID:**
```bash
curl "https://api.telegram.org/bot<TOKEN>/getUpdates" | jq '.result[-1].message.chat.id'
```

### Issue: Bot Blocked

**Error in logs:**
```
Forbidden: bot was blocked by the user
```

**Solution:**
1. Admin needs to unblock bot
2. Send `/start` again
3. Try login

---

## Security Best Practices

### ? DO:
- Use environment variables for bot token
- Store chat IDs in database only
- Verify admin identity before sending OTP
- Use HTTPS for all API calls
- Rotate bot token periodically
- Monitor failed OTP attempts

### ? DON'T:
- Commit bot tokens to git
- Share bot token publicly
- Use channel IDs for 2FA (use personal chat IDs)
- Store OTP codes in database
- Reuse OTP codes
- Send OTP without rate limiting

---

## Comparison: Old vs New

### Old System (Complex):
```
? Each admin needs separate bot configuration
? Store 5 bots ? token + chat_id for each admin
? Bot 4 dedicated for 2FA
? More config, more complexity
```

### New System (Simple):
```
? One bot for entire system
? One token in .env
? Only chat IDs differ per admin
? Easy to manage
? Less configuration
```

---

## Environment Variables

**Required:**
```bash
# System 2FA Bot (one for all admins)
TELEGRAM_2FA_BOT_TOKEN=7891234567:AAH-XxXxXxXxXxXxXxXxXxXxXxXxXxXx
```

**Optional (for other notifications):**
```bash
# Enable Telegram
TELEGRAM_ENABLED=true

# Other notification bots (if using telegram_bots array)
# ...
```

---

## Testing Checklist

- [ ] Bot created via @BotFather
- [ ] Bot token saved to .env
- [ ] Server restarted
- [ ] Each admin sent /start to bot
- [ ] Chat IDs obtained for all admins
- [ ] Admins created with telegram_2fa_chat_id
- [ ] Test login performed
- [ ] OTP received in personal chat
- [ ] OTP verification successful
- [ ] No messages in wrong chats

---

## FAQ

**Q: Can multiple admins use same bot?**  
A: Yes! That's the whole point. One bot, multiple chat IDs.

**Q: What if admin doesn't have telegram_2fa_chat_id?**  
A: Login will work but OTP won't be sent. Admin can't complete 2FA.

**Q: Can I disable 2FA for some admins?**  
A: Yes, leave telegram_2fa_chat_id empty or set require_2fa=False.

**Q: Is this secure?**  
A: Yes! Each admin gets OTP in their own private chat. Bot can't send to wrong chat.

**Q: Do I need different bots for different admins?**  
A: No! One bot, many chat IDs. Much simpler.

**Q: What about telegram_bots array?**  
A: That's for other notifications (device, SMS, activity). 2FA uses telegram_2fa_chat_id separately.

**Q: Can I change bot token later?**  
A: Yes, update .env and restart. Chat IDs stay the same.

**Q: Old system used Bot 4, what now?**  
A: New system is simpler. Just use telegram_2fa_chat_id field.

---

## Migration from Old System

If you used the old Bot 4 system:

**1. Get current Bot 4 chat IDs:**
```javascript
// MongoDB
db.admins.find({}, {username: 1, telegram_bots: 1}).forEach(doc => {
    let bot4 = doc.telegram_bots?.find(b => b.bot_id === 4);
    if (bot4) {
        print(`${doc.username}: ${bot4.chat_id}`);
    }
});
```

**2. Update to new system:**
```javascript
// MongoDB
db.admins.find({}).forEach(doc => {
    let bot4 = doc.telegram_bots?.find(b => b.bot_id === 4);
    if (bot4) {
        db.admins.updateOne(
            {_id: doc._id},
            {$set: {telegram_2fa_chat_id: bot4.chat_id}}
        );
    }
});
```

**3. Set bot token in .env**

**4. Restart server**

**5. Test!**

---

**Last Updated:** November 2, 2025  
**Version:** 2.1.0  
**Status:** ? Simplified - One bot for all admins
