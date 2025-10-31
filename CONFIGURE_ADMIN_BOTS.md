# ?? Configure Administrator Bots

Quick guide to configure Telegram bots for the Administrator account.

## Prerequisites

- Server running (`python run.py`)
- 5 Telegram bots created via @BotFather
- Bot tokens obtained
- Chat IDs obtained

## Method 1: Using Swagger UI (Easiest)

### Step 1: Access Swagger
```
http://localhost:8765/docs
```

### Step 2: Login
1. Find `/auth/login` endpoint
2. Click "Try it out"
3. Enter:
```json
{
  "username": "admin",
  "password": "1234567899"
}
```
4. Click "Execute"
5. **Copy the `access_token`**

### Step 3: Authorize
1. Click the ?? **Authorize** button at the top
2. Enter: `Bearer <your_access_token>`
3. Click "Authorize"

### Step 4: Update Admin Bots
1. Find `/admin/update/{username}` endpoint
2. Click "Try it out"
3. In `username` field, enter: `admin`
4. In Request body, paste:

```json
{
  "telegram_2fa_chat_id": "-1001234567890",
  
  "telegram_bots": [
    {
      "bot_id": 1,
      "bot_name": "admin_devices",
      "token": "1111111111:AAA_ADMIN_BOT1_TOKEN",
      "chat_id": "-1001111111111"
    },
    {
      "bot_id": 2,
      "bot_name": "admin_sms",
      "token": "2222222222:BBB_ADMIN_BOT2_TOKEN",
      "chat_id": "-1002222222222"
    },
    {
      "bot_id": 3,
      "bot_name": "admin_logs",
      "token": "3333333333:CCC_ADMIN_BOT3_TOKEN",
      "chat_id": "-1003333333333"
    },
    {
      "bot_id": 4,
      "bot_name": "admin_auth",
      "token": "4444444444:DDD_ADMIN_BOT4_TOKEN",
      "chat_id": "-1004444444444"
    },
    {
      "bot_id": 5,
      "bot_name": "admin_builds",
      "token": "5555555555:EEE_ADMIN_BOT5_TOKEN",
      "chat_id": "-1005555555555"
    }
  ]
}
```

5. Click "Execute"

### Step 5: Verify
1. Find `/auth/me` endpoint
2. Click "Try it out"
3. Click "Execute"
4. Should see your bots configuration

---

## Method 2: Using curl (Terminal)

### Complete Script

Save as `configure_admin_bots.sh`:

```bash
#!/bin/bash

# Configuration
SERVER_URL="http://localhost:8765"
ADMIN_USER="admin"
ADMIN_PASS="1234567899"

# Your values (CHANGE THESE!)
TFA_CHAT_ID="-1001234567890"

BOT1_TOKEN="1111111111:AAA_ADMIN_BOT1_TOKEN"
BOT1_CHAT="-1001111111111"

BOT2_TOKEN="2222222222:BBB_ADMIN_BOT2_TOKEN"
BOT2_CHAT="-1002222222222"

BOT3_TOKEN="3333333333:CCC_ADMIN_BOT3_TOKEN"
BOT3_CHAT="-1003333333333"

BOT4_TOKEN="4444444444:DDD_ADMIN_BOT4_TOKEN"
BOT4_CHAT="-1004444444444"

BOT5_TOKEN="5555555555:EEE_ADMIN_BOT5_TOKEN"
BOT5_CHAT="-1005555555555"

# Login and get token
echo "Logging in..."
TOKEN=$(curl -s -X POST "${SERVER_URL}/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"${ADMIN_USER}\",\"password\":\"${ADMIN_PASS}\"}" \
  | jq -r '.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
  echo "Login failed!"
  exit 1
fi

echo "Login successful! Token: ${TOKEN:0:20}..."

# Update admin bots
echo "Configuring bots..."
curl -X PUT "${SERVER_URL}/admin/update/admin" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"telegram_2fa_chat_id\": \"${TFA_CHAT_ID}\",
    \"telegram_bots\": [
      {
        \"bot_id\": 1,
        \"bot_name\": \"admin_devices\",
        \"token\": \"${BOT1_TOKEN}\",
        \"chat_id\": \"${BOT1_CHAT}\"
      },
      {
        \"bot_id\": 2,
        \"bot_name\": \"admin_sms\",
        \"token\": \"${BOT2_TOKEN}\",
        \"chat_id\": \"${BOT2_CHAT}\"
      },
      {
        \"bot_id\": 3,
        \"bot_name\": \"admin_logs\",
        \"token\": \"${BOT3_TOKEN}\",
        \"chat_id\": \"${BOT3_CHAT}\"
      },
      {
        \"bot_id\": 4,
        \"bot_name\": \"admin_auth\",
        \"token\": \"${BOT4_TOKEN}\",
        \"chat_id\": \"${BOT4_CHAT}\"
      },
      {
        \"bot_id\": 5,
        \"bot_name\": \"admin_builds\",
        \"token\": \"${BOT5_TOKEN}\",
        \"chat_id\": \"${BOT5_CHAT}\"
      }
    ]
  }"

echo ""
echo "Done! Verifying configuration..."

# Verify
curl -s -X GET "${SERVER_URL}/auth/me" \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.telegram_bots'

echo ""
echo "Configuration complete!"
```

### Run the script:

```bash
chmod +x configure_admin_bots.sh
./configure_admin_bots.sh
```

---

## Method 3: Using Python Script

Save as `configure_admin_bots.py`:

```python
import requests
import json

# Configuration
SERVER_URL = "http://localhost:8765"
ADMIN_USER = "admin"
ADMIN_PASS = "1234567899"

# Your values (CHANGE THESE!)
config = {
    "telegram_2fa_chat_id": "-1001234567890",
    "telegram_bots": [
        {
            "bot_id": 1,
            "bot_name": "admin_devices",
            "token": "1111111111:AAA_ADMIN_BOT1_TOKEN",
            "chat_id": "-1001111111111"
        },
        {
            "bot_id": 2,
            "bot_name": "admin_sms",
            "token": "2222222222:BBB_ADMIN_BOT2_TOKEN",
            "chat_id": "-1002222222222"
        },
        {
            "bot_id": 3,
            "bot_name": "admin_logs",
            "token": "3333333333:CCC_ADMIN_BOT3_TOKEN",
            "chat_id": "-1003333333333"
        },
        {
            "bot_id": 4,
            "bot_name": "admin_auth",
            "token": "4444444444:DDD_ADMIN_BOT4_TOKEN",
            "chat_id": "-1004444444444"
        },
        {
            "bot_id": 5,
            "bot_name": "admin_builds",
            "token": "5555555555:EEE_ADMIN_BOT5_TOKEN",
            "chat_id": "-1005555555555"
        }
    ]
}

def main():
    # Login
    print("Logging in...")
    login_response = requests.post(
        f"{SERVER_URL}/auth/login",
        json={"username": ADMIN_USER, "password": ADMIN_PASS}
    )
    
    if login_response.status_code != 200:
        print("Login failed!")
        return
    
    token = login_response.json()["access_token"]
    print(f"Login successful! Token: {token[:20]}...")
    
    # Update bots
    print("Configuring bots...")
    headers = {"Authorization": f"Bearer {token}"}
    
    update_response = requests.put(
        f"{SERVER_URL}/admin/update/admin",
        json=config,
        headers=headers
    )
    
    if update_response.status_code == 200:
        print("Bots configured successfully!")
    else:
        print(f"Error: {update_response.text}")
        return
    
    # Verify
    print("\nVerifying configuration...")
    me_response = requests.get(
        f"{SERVER_URL}/auth/me",
        headers=headers
    )
    
    admin_info = me_response.json()
    print(f"\nAdmin: {admin_info['username']}")
    print(f"2FA Chat ID: {admin_info.get('telegram_2fa_chat_id')}")
    print(f"Number of bots: {len(admin_info.get('telegram_bots', []))}")
    print("\nBots:")
    for bot in admin_info.get('telegram_bots', []):
        print(f"  - Bot {bot['bot_id']}: {bot['bot_name']}")
    
    print("\n? Configuration complete!")

if __name__ == "__main__":
    main()
```

### Run the script:

```bash
python configure_admin_bots.py
```

---

## Preparing Values

### 1. Create Telegram Bots

Open @BotFather in Telegram:

```
/newbot
Name: Admin Devices Bot
Username: admin_devices_bot
Token: 1111111111:AAA_ADMIN_BOT1_TOKEN ? Save this!

/newbot
Name: Admin SMS Bot
Username: admin_sms_bot
Token: 2222222222:BBB_ADMIN_BOT2_TOKEN ? Save this!

/newbot
Name: Admin Logs Bot
Username: admin_logs_bot
Token: 3333333333:CCC_ADMIN_BOT3_TOKEN ? Save this!

/newbot
Name: Admin Auth Bot
Username: admin_auth_bot
Token: 4444444444:DDD_ADMIN_BOT4_TOKEN ? Save this!

/newbot
Name: Admin Builds Bot
Username: admin_builds_bot
Token: 5555555555:EEE_ADMIN_BOT5_TOKEN ? Save this!
```

### 2. Get Chat IDs

For each bot:
```
1. Start the bot in Telegram
2. Send any message (e.g., /start)
3. Open: https://api.telegram.org/bot<TOKEN>/getUpdates
4. Find: "chat":{"id":-1001234567890}
5. Save the chat ID
```

**Tip:** You can use the same chat ID for all 5 bots!

### 3. Get 2FA Chat ID

```
1. Start the 2FA bot (from .env)
2. Send a message
3. Get chat ID using getUpdates
```

---

## Verification Checklist

After configuration, verify:

```bash
# Get admin info
curl -X GET "http://localhost:8765/auth/me" \
  -H "Authorization: Bearer <TOKEN>"
```

Check that response includes:
- ? `telegram_2fa_chat_id` is set
- ? `telegram_bots` array has 5 items
- ? Each bot has `bot_id`, `bot_name`, `token`, `chat_id`
- ? `device_token` is present

---

## Testing Notifications

### Test Bot 1 (Devices)
Register a test device and check Bot 1 receives notification

### Test Bot 2 (SMS)
Save SMS data and check Bot 2 receives notification

### Test Bot 3 (Logs)
Send a command and check Bot 3 receives notification

### Test Bot 4 (Auth)
Logout and login again, check Bot 4 receives notification

### Test 2FA Bot
Login and check 2FA bot sends code to your chat

---

## Troubleshooting

### Bots Not Receiving Messages?

**Check:**
1. Bot tokens are correct (no typos)
2. Chat IDs are correct (negative numbers)
3. Bots are started in Telegram
4. Test manually:
```bash
curl https://api.telegram.org/bot<TOKEN>/sendMessage \
  -d chat_id=-1001234567890 \
  -d text="Test message"
```

### Cannot Update Admin?

**Check:**
1. Using correct username: `admin` (lowercase)
2. Token is valid (not expired)
3. All 5 bots provided in array
4. JSON is valid (use JSON validator)

### Token Expired?

Login again:
```bash
POST /auth/login
{
  "username": "admin",
  "password": "1234567899"
}
```

---

## Summary

**Quick Steps:**
1. Create 5 bots via @BotFather
2. Get 5 tokens
3. Get 5 chat IDs (can be same)
4. Get 2FA chat ID
5. Login to system
6. PUT /admin/update/admin with all values
7. Verify with GET /auth/me
8. Test notifications

**That's it!** ?

Your Administrator bots are now configured and ready to receive all notifications from all admins!
