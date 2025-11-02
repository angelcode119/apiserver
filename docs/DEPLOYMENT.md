# Deployment Guide

Complete guide for deploying to production.

---

## Table of Contents

1. [Production Checklist](#production-checklist)
2. [Environment Configuration](#environment-configuration)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Security Hardening](#security-hardening)
6. [Monitoring & Logging](#monitoring--logging)
7. [Backup & Recovery](#backup--recovery)

---

## Production Checklist

### Pre-Deployment

- [ ] Change `SECRET_KEY` to strong random value
- [ ] Use production MongoDB instance
- [ ] Configure SSL/TLS certificates
- [ ] Setup Firebase for production
- [ ] Configure all 5 Telegram bots
- [ ] Setup monitoring & logging
- [ ] Configure backup system
- [ ] Review security settings
- [ ] Test authentication flow
- [ ] Verify Firebase notifications work
- [ ] Test device registration
- [ ] Load test API endpoints

### Security

- [ ] Enable HTTPS only
- [ ] Configure firewall rules
- [ ] Restrict MongoDB access
- [ ] Secure Firebase credentials
- [ ] Setup rate limiting
- [ ] Enable CORS properly
- [ ] Review admin permissions
- [ ] Setup intrusion detection
- [ ] Configure security headers
- [ ] Enable audit logging

### Infrastructure

- [ ] Setup load balancer
- [ ] Configure auto-scaling
- [ ] Setup CDN (if needed)
- [ ] Configure DNS
- [ ] Setup health checks
- [ ] Configure backup storage
- [ ] Setup monitoring alerts
- [ ] Configure log aggregation

---

## Environment Configuration

### Production Environment Variables

```env
# ============================================
# SERVER CONFIGURATION
# ============================================
HOST=0.0.0.0
PORT=8000
DEBUG=false
ENVIRONMENT=production

# ============================================
# DATABASE
# ============================================
MONGODB_URL=mongodb://mongodb-user:password@mongodb-host:27017/
DATABASE_NAME=parental_control
MONGODB_MAX_POOL_SIZE=100
MONGODB_MIN_POOL_SIZE=10

# ============================================
# SECURITY
# ============================================
SECRET_KEY=generate-super-strong-random-key-here-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24

# ============================================
# TELEGRAM
# ============================================
TELEGRAM_ENABLED=true
TELEGRAM_2FA_BOT_TOKEN=production-bot-token
TELEGRAM_2FA_CHAT_ID=production-chat-id

# ============================================
# FIREBASE
# ============================================
DEVICE_FIREBASE_CREDENTIALS=/secure/path/device-firebase-adminsdk.json
ADMIN_FIREBASE_CREDENTIALS=/secure/path/admin-firebase-adminsdk.json

# ============================================
# CORS
# ============================================
CORS_ORIGINS=https://admin.yourdomain.com,https://app.yourdomain.com
CORS_CREDENTIALS=true

# ============================================
# RATE LIMITING
# ============================================
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60

# ============================================
# LOGGING
# ============================================
LOG_LEVEL=INFO
LOG_FILE=/var/log/app/backend.log
LOG_MAX_SIZE=100MB
LOG_BACKUP_COUNT=10

# ============================================
# MONITORING
# ============================================
SENTRY_DSN=https://your-sentry-dsn
PROMETHEUS_PORT=9090
```

### Generating SECRET_KEY

```python
import secrets

# Generate secure secret key
secret_key = secrets.token_urlsafe(32)
print(f"SECRET_KEY={secret_key}")
```

---

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY run.py .

# Create directories
RUN mkdir -p /app/logs /app/firebase-credentials

# Copy Firebase credentials (securely)
COPY device-firebase-adminsdk.json /app/firebase-credentials/
COPY admin-firebase-adminsdk.json /app/firebase-credentials/

# Set permissions
RUN chmod 600 /app/firebase-credentials/*.json

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["python", "run.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:6.0
    container_name: mongodb
    restart: always
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}
    volumes:
      - mongodb_data:/data/db
      - mongodb_config:/data/configdb
    ports:
      - "27017:27017"
    networks:
      - backend
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/test --quiet
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: .
    container_name: backend
    restart: always
    depends_on:
      mongodb:
        condition: service_healthy
    environment:
      - MONGODB_URL=mongodb://admin:${MONGO_PASSWORD}@mongodb:27017/
      - DATABASE_NAME=parental_control
      - SECRET_KEY=${SECRET_KEY}
      - TELEGRAM_2FA_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - TELEGRAM_2FA_CHAT_ID=${TELEGRAM_CHAT_ID}
      - DEVICE_FIREBASE_CREDENTIALS=/app/firebase-credentials/device-firebase-adminsdk.json
      - ADMIN_FIREBASE_CREDENTIALS=/app/firebase-credentials/admin-firebase-adminsdk.json
    volumes:
      - ./logs:/app/logs
      - firebase_credentials:/app/firebase-credentials:ro
    ports:
      - "8000:8000"
    networks:
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    container_name: nginx
    restart: always
    depends_on:
      - backend
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    ports:
      - "80:80"
      - "443:443"
    networks:
      - backend

volumes:
  mongodb_data:
  mongodb_config:
  firebase_credentials:

networks:
  backend:
    driver: bridge
```

### nginx.conf

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    server {
        listen 80;
        server_name api.yourdomain.com;
        return 301 https://$host$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name api.yourdomain.com;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Security Headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "DENY" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # Rate Limiting
        limit_req zone=api_limit burst=20 nodelay;

        # Proxy Settings
        location / {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Health Check
        location /health {
            proxy_pass http://backend/health;
            access_log off;
        }
    }
}
```

### Deploy with Docker Compose

```bash
# Create .env file
cat > .env << EOF
MONGO_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
EOF

# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Check status
docker-compose ps
```

---

## Kubernetes Deployment

### Namespace

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: device-management
```

### Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: device-management
type: Opaque
stringData:
  secret-key: "your-secret-key-here"
  mongodb-password: "mongodb-password"
  telegram-bot-token: "telegram-bot-token"
  telegram-chat-id: "telegram-chat-id"
---
apiVersion: v1
kind: Secret
metadata:
  name: firebase-credentials
  namespace: device-management
type: Opaque
data:
  device-firebase-adminsdk.json: <base64-encoded-json>
  admin-firebase-adminsdk.json: <base64-encoded-json>
```

### MongoDB

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mongodb
  namespace: device-management
spec:
  serviceName: mongodb
  replicas: 1
  selector:
    matchLabels:
      app: mongodb
  template:
    metadata:
      labels:
        app: mongodb
    spec:
      containers:
      - name: mongodb
        image: mongo:6.0
        ports:
        - containerPort: 27017
        env:
        - name: MONGO_INITDB_ROOT_USERNAME
          value: admin
        - name: MONGO_INITDB_ROOT_PASSWORD
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: mongodb-password
        volumeMounts:
        - name: mongodb-data
          mountPath: /data/db
  volumeClaimTemplates:
  - metadata:
      name: mongodb-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 20Gi
---
apiVersion: v1
kind: Service
metadata:
  name: mongodb
  namespace: device-management
spec:
  selector:
    app: mongodb
  ports:
  - port: 27017
    targetPort: 27017
  clusterIP: None
```

### Backend Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: device-management
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: your-registry/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: MONGODB_URL
          value: mongodb://admin:$(MONGO_PASSWORD)@mongodb:27017/
        - name: DATABASE_NAME
          value: parental_control
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: secret-key
        - name: TELEGRAM_2FA_BOT_TOKEN
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: telegram-bot-token
        - name: TELEGRAM_2FA_CHAT_ID
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: telegram-chat-id
        - name: DEVICE_FIREBASE_CREDENTIALS
          value: /app/firebase/device-firebase-adminsdk.json
        - name: ADMIN_FIREBASE_CREDENTIALS
          value: /app/firebase/admin-firebase-adminsdk.json
        volumeMounts:
        - name: firebase-creds
          mountPath: /app/firebase
          readOnly: true
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: firebase-creds
        secret:
          secretName: firebase-credentials
---
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: device-management
spec:
  selector:
    app: backend
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP
```

### Ingress

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: backend-ingress
  namespace: device-management
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: backend-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 8000
```

### Deploy to Kubernetes

```bash
# Apply all manifests
kubectl apply -f k8s/

# Check deployments
kubectl get all -n device-management

# View logs
kubectl logs -f deployment/backend -n device-management

# Scale deployment
kubectl scale deployment/backend --replicas=5 -n device-management
```

---

## Security Hardening

### 1. Use HTTPS Only

```python
# In main.py
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

if not DEBUG:
    app.add_middleware(HTTPSRedirectMiddleware)
```

### 2. Security Headers

```python
from starlette.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["api.yourdomain.com", "*.yourdomain.com"]
)
```

### 3. Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/auth/login")
@limiter.limit("5/minute")
async def login(request: Request):
    ...
```

### 4. Database Security

```bash
# MongoDB configuration
security:
  authorization: enabled

# Create application user
use parental_control
db.createUser({
  user: "app_user",
  pwd: "strong_password",
  roles: [
    { role: "readWrite", db: "parental_control" }
  ]
})
```

### 5. Firebase Security

```bash
# Restrict file permissions
chmod 600 *-firebase-adminsdk.json
chown backend-user:backend-group *-firebase-adminsdk.json
```

---

## Monitoring & Logging

### Prometheus Metrics

```python
# In main.py
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

# Add instrumentation
Instrumentator().instrument(app).expose(app)

# Custom metrics
login_counter = Counter('login_attempts_total', 'Total login attempts')
request_duration = Histogram('request_duration_seconds', 'Request duration')
```

### Logging Configuration

```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            'logs/app.log',
            maxBytes=100*1024*1024,  # 100MB
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
```

### Sentry Integration

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

if not DEBUG:
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        integrations=[FastApiIntegration()],
        traces_sample_rate=0.1
    )
```

---

## Backup & Recovery

### MongoDB Backup

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="mongodb_backup_$DATE"

# Create backup
mongodump \
  --host=localhost \
  --port=27017 \
  --username=admin \
  --password=$MONGO_PASSWORD \
  --authenticationDatabase=admin \
  --db=parental_control \
  --out=$BACKUP_DIR/$BACKUP_NAME

# Compress backup
tar -czf $BACKUP_DIR/$BACKUP_NAME.tar.gz -C $BACKUP_DIR $BACKUP_NAME
rm -rf $BACKUP_DIR/$BACKUP_NAME

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/$BACKUP_NAME.tar.gz s3://your-bucket/backups/

# Keep only last 7 days
find $BACKUP_DIR -name "mongodb_backup_*.tar.gz" -mtime +7 -delete
```

### Automated Backup (Cron)

```bash
# Add to crontab
0 2 * * * /path/to/backup.sh >> /var/log/backup.log 2>&1
```

### Restore from Backup

```bash
# Extract backup
tar -xzf mongodb_backup_20251102_020000.tar.gz

# Restore
mongorestore \
  --host=localhost \
  --port=27017 \
  --username=admin \
  --password=$MONGO_PASSWORD \
  --authenticationDatabase=admin \
  --db=parental_control \
  --drop \
  mongodb_backup_20251102_020000/parental_control
```

---

## Health Checks

### Add Health Endpoint

```python
@app.get("/health")
async def health_check():
    try:
        # Check MongoDB
        await mongodb.db.command("ping")
        mongo_status = "healthy"
    except:
        mongo_status = "unhealthy"
    
    return {
        "status": "healthy" if mongo_status == "healthy" else "unhealthy",
        "mongodb": mongo_status,
        "timestamp": datetime.utcnow().isoformat()
    }
```

---

## Performance Optimization

### 1. Database Indexes

```python
# In database.py
async def create_indexes():
    # Devices
    await mongodb.db.devices.create_index("device_id", unique=True)
    await mongodb.db.devices.create_index("admin_username")
    await mongodb.db.devices.create_index([("app_type", 1), ("status", 1)])
    
    # Admins
    await mongodb.db.admins.create_index("username", unique=True)
    await mongodb.db.admins.create_index("device_token")
    
    # SMS
    await mongodb.db.sms_messages.create_index([("device_id", 1), ("timestamp", -1)])
```

### 2. Connection Pooling

```python
# MongoDB connection pool
mongodb_client = AsyncIOMotorClient(
    MONGODB_URL,
    maxPoolSize=100,
    minPoolSize=10
)
```

### 3. Caching

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_admin_permissions(username: str):
    # Cache admin permissions
    pass
```

---

**Version:** 2.0.0  
**Last Updated:** November 2, 2025
