# ? Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites

- Python 3.8+
- MongoDB (local or Atlas)
- Telegram account

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Setup MongoDB

### Option A: Local
```bash
# Ubuntu/Debian
sudo apt-get install mongodb
sudo systemctl start mongodb

# macOS
brew install mongodb-community
brew services start mongodb-community
```

### Option B: MongoDB Atlas (Free Cloud)
https://www.mongodb.com/cloud/atlas

## 3. Create 2FA Bot

1. Open @BotFather in Telegram
2. Send `/newbot`
3. Get **token**
4. Start bot and send a message
5. Get **chat_id** from:
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```

## 4. Configure Environment

```bash
cp .env.example .env
nano .env
```

**Update these 4 lines:**

```bash
MONGODB_URL=mongodb://localhost:27017/android_control

SECRET_KEY=change_this_to_very_long_random_string

TELEGRAM_2FA_BOT_TOKEN=your_2fa_bot_token_here

TELEGRAM_2FA_CHAT_ID=-1001234567890
```

## 5. Run Server

```bash
python run.py
```

Or:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8765
```

## 6. Login & Get Device Token

**Open Swagger UI:**
```
http://localhost:8765/docs
```

**Login with default credentials:**
```json
{
  "username": "admin",
  "password": "1234567899"
}
```

**Get your device_token:**
- Call `/auth/me` endpoint
- Save the `device_token`
- Use it in Android app

## 7. Done! ??

Your server is ready!

**Next Steps:**
- Change default password
- Read full setup guide: `SETUP_GUIDE.md`
- Configure telegram bots: `BOT_SYSTEM_GUIDE.md`

---

## Default Admin Credentials

```
Username: admin
Password: 1234567899
Role: super_admin
```

?? **CHANGE THIS PASSWORD IMMEDIATELY!**

---

## Quick Test

```bash
curl -X POST http://localhost:8765/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"1234567899"}'
```

Should return access token!

---

## Troubleshooting

**MongoDB not starting?**
```bash
sudo systemctl start mongodb
```

**Port already in use?**
```bash
lsof -i :8765
kill -9 <PID>
```

**Can't login?**
- Username: `admin` (lowercase)
- Password: `1234567899` (exactly)

---

**For detailed setup, see: SETUP_GUIDE.md**
