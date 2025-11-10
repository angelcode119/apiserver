# Production Deployment

Complete guide for deploying to production.

## Prerequisites

- Ubuntu 20.04+ server
- 4GB+ RAM
- 2+ CPU cores
- MongoDB 4.4+
- Python 3.10+
- Domain with SSL

## Environment Setup

### 1. Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install Dependencies

```bash
# Python
sudo apt install python3.10 python3-pip -y

# MongoDB
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt update
sudo apt install mongodb-org -y
sudo systemctl start mongod
sudo systemctl enable mongod
```

## Application Setup

### 1. Clone Repository

```bash
cd /opt
git clone <repository-url> device-management
cd device-management
```

### 2. Install Python Packages

```bash
pip3 install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
nano .env
```

**Production .env:**
```env
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=parental_control

SECRET_KEY=<generate-strong-key>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

TELEGRAM_ENABLED=true
TELEGRAM_2FA_BOT_TOKEN=<your-bot-token>

SERVER_HOST=0.0.0.0
SERVER_PORT=8765
DEBUG=false
```

### 4. Setup Firebase

```bash
# Place Firebase credentials
cp device-firebase-adminsdk.json /opt/device-management/
cp admin-firebase-adminsdk.json /opt/device-management/
chmod 600 *.json
```

## Systemd Service

### Create Service File

```bash
sudo nano /etc/systemd/system/device-management.service
```

**Content:**
```ini
[Unit]
Description=Device Management API
After=network.target mongodb.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/device-management
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl start device-management
sudo systemctl enable device-management
sudo systemctl status device-management
```

## Nginx Setup

### Install Nginx

```bash
sudo apt install nginx -y
```

### Configure Reverse Proxy

```bash
sudo nano /etc/nginx/sites-available/device-management
```

**Content:**
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8765;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/device-management /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## SSL Certificate

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d api.yourdomain.com
```

## MongoDB Security

```bash
mongo
use admin
db.createUser({
  user: "admin",
  pwd: "strong_password",
  roles: ["root"]
})
exit

# Edit MongoDB config
sudo nano /etc/mongod.conf
```

Add:
```yaml
security:
  authorization: enabled
```

```bash
sudo systemctl restart mongod
```

## Monitoring

### Logs

```bash
# Application logs
sudo journalctl -u device-management -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Health Check

```bash
curl http://localhost:8765/health
```

## Backup

### MongoDB Backup Script

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
mongodump --db parental_control --out /backups/mongodb_$DATE
tar -czf /backups/mongodb_$DATE.tar.gz /backups/mongodb_$DATE
rm -rf /backups/mongodb_$DATE
```

### Cron Job

```bash
crontab -e
```

Add:
```
0 2 * * * /opt/scripts/backup.sh
```

## Security

### Firewall

```bash
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

### Fail2ban

```bash
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
```

## Optimization

### Database Indexes

```bash
python3 scripts/create_indexes.py
```

### MongoDB Configuration

Edit `/etc/mongod.conf`:
```yaml
net:
  maxIncomingConnections: 500

storage:
  wiredTiger:
    engineConfig:
      cacheSizeGB: 2
```

## Updates

```bash
cd /opt/device-management
git pull
pip3 install -r requirements.txt
sudo systemctl restart device-management
```

**Last Updated**: November 10, 2025
