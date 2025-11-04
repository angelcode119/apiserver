# Quick Start

## Installation

### 1. Clone & Setup
```bash
git clone <repository>
cd <project>
cp .env.example .env
```

### 2. Run with Docker
```bash
docker-compose up -d
```

### 3. Access
- API: http://localhost:8765
- Docs: http://localhost:8765/docs

## Default Login
```
Username: admin
Password: admin123
```

## Basic Usage

### 1. Login
```bash
curl -X POST http://localhost:8765/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### 2. Get Devices
```bash
curl http://localhost:8765/api/devices \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Register Device
```bash
curl -X POST http://localhost:8765/register \
  -H "Content-Type: application/json" \
  -d '{"device_id":"test123","admin_token":"ADMIN_TOKEN"}'
```

## API Endpoints

### Authentication
- `POST /auth/login` - Login
- `POST /auth/verify-2fa` - Verify OTP
- `POST /auth/logout` - Logout

### Devices
- `GET /api/devices` - List devices
- `GET /api/devices/{id}` - Get device
- `DELETE /api/devices/{id}` - Delete device

### Admin
- `POST /api/admins` - Create admin
- `GET /api/admins` - List admins
- `PUT /api/admins/{username}` - Update admin

## Configuration

Edit `.env`:
```env
MONGODB_URL=mongodb://localhost:27017
SECRET_KEY=change-this-secret
DEBUG=True
```

## Next Steps

1. Change default password
2. Configure Telegram bots (optional)
3. Setup Firebase (optional)
4. Read DEPLOYMENT.md for production
