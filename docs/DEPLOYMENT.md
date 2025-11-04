# Deployment Guide

## Quick Deploy

### 1. Environment Setup
```bash
cp .env.example .env
# Edit .env with your settings
```

### 2. Docker Compose Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 3. Services
- **API**: http://localhost:8765
- **MongoDB**: localhost:27017
- **Redis**: localhost:6379

### 4. Default Admin
- Username: `admin`
- Password: `admin123`

⚠️ **Change default credentials immediately!**

## Environment Variables

### Required
```env
MONGODB_URL=mongodb://localhost:27017
SECRET_KEY=your-secret-key-here
TELEGRAM_2FA_BOT_TOKEN=your-bot-token
```

### Optional
```env
DEBUG=False
SERVER_PORT=8765
SMS_RETENTION_DAYS=180
```

## Production Checklist

- [ ] Change SECRET_KEY
- [ ] Change default admin password
- [ ] Configure Telegram bots
- [ ] Setup Firebase (if using)
- [ ] Configure SSL/TLS
- [ ] Setup backup strategy
- [ ] Monitor logs

## Backup

```bash
# Backup MongoDB
mongodump --uri="mongodb://localhost:27017/parental_control" --out=/backup

# Restore
mongorestore --uri="mongodb://localhost:27017" /backup
```
