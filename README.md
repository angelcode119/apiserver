# Device Control Server

FastAPI-based server for device monitoring and control with admin panel, real-time WebSocket communication, and multi-admin support.

## Features

- 🔐 **Authentication**: JWT + 2FA (Telegram OTP)
- 👥 **Multi-Admin**: Role-based access control (Super Admin, Admin, Viewer)
- 📱 **Device Management**: Real-time monitoring, SMS/contacts sync
- 🔔 **Notifications**: Telegram bots + Firebase push notifications
- 💾 **Database**: MongoDB with automatic data retention
- 🚀 **Production Ready**: Docker + Nginx + Redis

## Quick Start

```bash
# Clone and setup
git clone <repository>
cd <project>
cp .env.example .env

# Run with Docker
docker-compose up -d

# Access
# API: http://localhost:8765
# Docs: http://localhost:8765/docs
```

**Default Login:**
- Username: `admin`
- Password: `admin123`

## Tech Stack

- **Framework**: FastAPI
- **Database**: MongoDB
- **Cache**: Redis
- **Auth**: JWT + OTP
- **Notifications**: Telegram + Firebase
- **Deployment**: Docker + Docker Compose

## Project Structure

```
app/
├── main.py              # FastAPI app & endpoints
├── config.py            # Configuration
├── database.py          # MongoDB setup
├── models/              # Pydantic schemas
├── services/            # Business logic
├── middleware/          # Rate limiting, etc.
└── utils/               # Auth middleware
```

## API Endpoints

### Authentication
- `POST /auth/login` - Admin login
- `POST /auth/verify-2fa` - Verify OTP code
- `POST /auth/logout` - Logout

### Devices
- `GET /api/devices` - List devices
- `GET /api/devices/{id}` - Get device details
- `POST /api/devices/{id}/command` - Send command
- `DELETE /api/devices/{id}` - Delete device

### Admin Management
- `POST /api/admins` - Create admin
- `GET /api/admins` - List admins
- `PUT /api/admins/{username}` - Update admin
- `DELETE /api/admins/{username}` - Delete admin

### Statistics
- `GET /api/stats` - Get statistics
- `GET /api/admin-activities` - Admin activity logs

## Configuration

Key environment variables:

```env
MONGODB_URL=mongodb://localhost:27017
SECRET_KEY=your-secret-key
TELEGRAM_2FA_BOT_TOKEN=your-bot-token
DEBUG=False
```

See `.env.example` for all options.

## Documentation

- [Quick Start Guide](docs/QUICKSTART.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

## Security

- JWT token authentication
- 2FA with Telegram OTP
- Role-based permissions
- Single session control
- Rate limiting
- Password hashing (bcrypt)

## Production Deployment

```bash
docker-compose -f docker-compose.prod.yml up -d
```

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for details.

## Requirements

- Python 3.8+
- MongoDB 4.4+
- Redis (optional, for production)
- Docker & Docker Compose

## License

Proprietary

## Support

For issues and questions, contact the development team.
