# Performance Optimization Guide
## For 25,000+ Users

Complete guide for optimizing the server to handle 25,000+ concurrent users.

---

## ?? Load Estimation

### Current Scale: 25,000 Users

**Assumptions:**
- 25,000 total users (admins + devices)
- Each user: 10 requests/hour average
- Peak hours: 50% users active
- Device sync frequency: every 5-15 minutes

**Calculated Load:**
```
Average: 25,000 ? 10 / 3600 ? 70 req/sec
Peak:    12,500 ? 10 / 3600 ? 35 req/sec (sustained)
Burst:   150-200 req/sec (short peaks)
```

**Database Operations:**
```
Reads:  80% (device lists, SMS, stats)
Writes: 20% (SMS sync, logs, activities)
```

---

## 1?? Database Optimization (CRITICAL)

### Indexing

**Already Implemented:** ?
- All major collections have proper indexes
- Compound indexes for common queries
- TTL indexes for automatic cleanup

**Run Index Creation:**
```bash
python scripts/create_indexes.py
```

**Verify Indexes:**
```javascript
// MongoDB shell
use parental_control

// Check devices indexes
db.devices.getIndexes()

// Check query performance
db.devices.find({admin_username: "john"}).explain("executionStats")
```

### Connection Pooling

**Current Config:** (`app/database.py`)
```python
mongodb.client = AsyncIOMotorClient(
    settings.MONGODB_URL,
    maxPoolSize=100,      # Max connections
    minPoolSize=10,       # Min connections always open
    serverSelectionTimeoutMS=5000
)
```

**For 25K users, increase to:**
```python
maxPoolSize=200,    # More connections for concurrent requests
minPoolSize=20,     # Keep more connections ready
maxIdleTimeMS=30000,  # Connection timeout
waitQueueTimeoutMS=10000  # Max wait for connection
```

### Query Optimization

**Best Practices:**

? **Use Projection** (only fetch needed fields):
```python
# Bad
device = await mongodb.db.devices.find_one({"device_id": device_id})

# Good
device = await mongodb.db.devices.find_one(
    {"device_id": device_id},
    {"device_id": 1, "model": 1, "status": 1}  # Only these fields
)
```

? **Use Pagination:**
```python
# Always use skip and limit
devices = await mongodb.db.devices.find({}).skip(skip).limit(50).to_list(50)
```

? **Use Aggregation for Stats:**
```python
# Better than multiple queries
pipeline = [
    {"$match": {"admin_username": username}},
    {"$group": {"_id": "$status", "count": {"$sum": 1}}}
]
stats = await mongodb.db.devices.aggregate(pipeline).to_list(None)
```

---

## 2?? Caching with Redis (HIGHLY RECOMMENDED)

### Why Redis?

- Stats queries are expensive
- Device lists queried frequently  
- Admin info rarely changes
- 10-100x faster than MongoDB

### Installation

```bash
# Install Redis
sudo apt-get install redis-server

# Start Redis
sudo systemctl start redis
sudo systemctl enable redis

# Install Python client
pip install redis aioredis
```

### Implementation

**Create** `app/cache.py`:

```python
import aioredis
import json
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)

class RedisCache:
    def __init__(self):
        self.redis: Optional[aioredis.Redis] = None
    
    async def connect(self):
        self.redis = await aioredis.create_redis_pool(
            'redis://localhost:6379',
            minsize=5,
            maxsize=20
        )
        logger.info("? Redis connected")
    
    async def get(self, key: str) -> Optional[Any]:
        if not self.redis:
            return None
        
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set(self, key: str, value: Any, expire: int = 300):
        """Set with expiration (default 5 min)"""
        if not self.redis:
            return
        
        await self.redis.setex(
            key,
            expire,
            json.dumps(value)
        )
    
    async def delete(self, key: str):
        if self.redis:
            await self.redis.delete(key)
    
    async def clear_pattern(self, pattern: str):
        """Clear keys matching pattern"""
        if not self.redis:
            return
        
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)

cache = RedisCache()
```

### Usage in Endpoints

**Cache Stats:**
```python
@app.get("/api/devices/stats")
async def get_device_stats(current_admin: Admin = ...):
    # Try cache first
    cache_key = f"stats:{current_admin.username}"
    cached = await cache.get(cache_key)
    if cached:
        return cached
    
    # Calculate stats
    stats = await device_service.get_stats(current_admin.username)
    
    # Cache for 5 minutes
    await cache.set(cache_key, stats, expire=300)
    
    return stats
```

**Cache Device Lists:**
```python
@app.get("/api/devices")
async def get_devices(skip: int = 0, limit: int = 50, ...):
    cache_key = f"devices:{current_admin.username}:{skip}:{limit}"
    cached = await cache.get(cache_key)
    if cached:
        return cached
    
    # Fetch from DB
    devices = await device_service.get_devices(...)
    
    # Cache for 2 minutes
    await cache.set(cache_key, devices, expire=120)
    
    return devices
```

**Invalidate Cache on Update:**
```python
@app.post("/register")
async def register_device(...):
    # Register device
    result = await device_service.register_device(...)
    
    # Invalidate cache
    await cache.clear_pattern(f"devices:{admin_username}:*")
    await cache.clear_pattern(f"stats:{admin_username}")
    
    return result
```

---

## 3?? Rate Limiting (SECURITY)

**Already Implemented:** ? `app/middleware/rate_limit.py`

### Enable in main.py

```python
from app.middleware import RateLimitMiddleware

app = FastAPI()

# Add Rate Limiting
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=100  # Adjust based on needs
)
```

### Configuration for 25K Users

```python
# For 25,000 users
# Peak: ~200 req/sec from all users
# Per user: max 100 req/min (reasonable)

app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=100
)
```

### Custom Limits per Endpoint

Already configured in middleware:
- `/auth/login`: 10 req/min
- `/register`: 50 req/min
- `/sms`: 200 req/min

---

## 4?? Multiple Workers (CRITICAL)

### Current: Single Worker

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Recommended: Multiple Workers

**Option 1: Uvicorn with Workers**
```bash
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info
```

**Option 2: Gunicorn + Uvicorn (Better)**
```bash
pip install gunicorn

gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 60 \
  --keep-alive 5 \
  --log-level info
```

**Calculate Worker Count:**
```
Workers = (2 ? CPU_Cores) + 1

4-core CPU: 4 ? 2 + 1 = 9 workers
8-core CPU: 8 ? 2 + 1 = 17 workers
```

---

## 5?? Nginx Reverse Proxy (RECOMMENDED)

### Why Nginx?

- SSL termination
- Load balancing
- Static file serving
- Connection buffering
- Better performance

### Installation

```bash
sudo apt-get install nginx
```

### Configuration

**Create** `/etc/nginx/sites-available/parental-control`:

```nginx
upstream parental_control {
    # Multiple backend servers
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
    
    # Load balancing method
    least_conn;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL certificates
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    # SSL config
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # Client body size (for file uploads)
    client_max_body_size 10M;
    
    # Timeouts
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
    
    # Proxy to backend
    location / {
        proxy_pass http://parental_control;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Static files (if any)
    location /static {
        alias /path/to/static;
        expires 30d;
    }
    
    # Health check
    location /health {
        access_log off;
        return 200 "OK\n";
    }
}
```

**Enable and Restart:**
```bash
sudo ln -s /etc/nginx/sites-available/parental-control /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 6?? Background Tasks (RECOMMENDED)

### Why Background Tasks?

- Sending Telegram notifications
- Push notifications
- Log processing
- Stats calculation
- Cleanup tasks

### Using Celery + Redis

**Installation:**
```bash
pip install celery redis
```

**Create** `app/tasks.py`:

```python
from celery import Celery
from app.services.telegram_multi_service import telegram_multi_service
from app.services.firebase_admin_service import firebase_admin_service

celery_app = Celery(
    'parental_control',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

@celery_app.task
def send_telegram_notification(admin_username: str, message: str):
    """Send Telegram in background"""
    import asyncio
    asyncio.run(
        telegram_multi_service.send_to_admin(admin_username, message)
    )

@celery_app.task
def send_push_notification(admin_username: str, title: str, body: str):
    """Send push notification in background"""
    import asyncio
    asyncio.run(
        firebase_admin_service.send_notification_to_admin(
            admin_username, title, body
        )
    )
```

**Usage in Endpoints:**
```python
from app.tasks import send_telegram_notification

@app.post("/register")
async def register_device(...):
    # Register device
    result = await device_service.register_device(...)
    
    # Send notification in background (non-blocking)
    send_telegram_notification.delay(admin_username, message)
    
    # Return immediately
    return result
```

**Start Celery Worker:**
```bash
celery -A app.tasks worker --loglevel=info --concurrency=4
```

---

## 7?? Monitoring & Logging

### Response Time Tracking

**Add Middleware:**
```python
import time
from fastapi import Request

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log slow requests
    if process_time > 1.0:
        logger.warning(f"Slow request: {request.url.path} took {process_time:.2f}s")
    
    return response
```

### Structured Logging

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        return json.dumps(log_data)

# Configure
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.root.addHandler(handler)
```

### Log Rotation

```bash
# Install
sudo apt-get install logrotate

# Configure /etc/logrotate.d/parental-control
/var/log/parental-control/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

---

## 8?? Docker Deployment (RECOMMENDED)

### Docker Compose for Production

**Create** `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  # MongoDB
  mongodb:
    image: mongo:6
    restart: always
    volumes:
      - mongodb_data:/data/db
    environment:
      MONGO_INITDB_DATABASE: parental_control
    ports:
      - "27017:27017"
    command: mongod --wiredTigerCacheSizeGB 2
  
  # Redis
  redis:
    image: redis:7-alpine
    restart: always
    ports:
      - "6379:6379"
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
  
  # API Server (multiple instances)
  api:
    build: .
    restart: always
    depends_on:
      - mongodb
      - redis
    environment:
      - MONGODB_URL=mongodb://mongodb:27017
      - REDIS_URL=redis://redis:6379
      - WORKERS=4
    deploy:
      replicas: 2  # 2 containers
      resources:
        limits:
          cpus: '2'
          memory: 2G
    ports:
      - "8000-8001:8000"
  
  # Celery Worker
  celery:
    build: .
    restart: always
    command: celery -A app.tasks worker --loglevel=info --concurrency=4
    depends_on:
      - redis
      - mongodb
    environment:
      - MONGODB_URL=mongodb://mongodb:27017
      - REDIS_URL=redis://redis:6379
  
  # Nginx
  nginx:
    image: nginx:alpine
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - api

volumes:
  mongodb_data:
```

**Build and Run:**
```bash
docker-compose -f docker-compose.prod.yml up -d --scale api=4
```

---

## ?? Implementation Checklist

### Phase 1: Critical (Do First) ?

- [x] Database indexes (already done)
- [x] Connection pooling (already configured)
- [ ] Run index creation script
- [ ] Multiple workers (4-8)
- [ ] Rate limiting middleware

### Phase 2: Important ??

- [ ] Redis caching
- [ ] Nginx reverse proxy
- [ ] Background tasks (Celery)
- [ ] Monitoring middleware

### Phase 3: Optimization ??

- [ ] Query optimization review
- [ ] Log rotation
- [ ] Structured logging
- [ ] Performance metrics

### Phase 4: Scaling ??

- [ ] Docker deployment
- [ ] Load balancing
- [ ] Auto-scaling
- [ ] CDN for static files

---

## ?? Testing Performance

### Load Testing with Locust

```bash
pip install locust
```

**Create** `locustfile.py`:

```python
from locust import HttpUser, task, between

class AdminUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        # Login
        response = self.client.post("/auth/login", json={
            "username": "test",
            "password": "test123"
        })
        # Get token
        # ...
    
    @task(10)
    def get_devices(self):
        self.client.get("/api/devices")
    
    @task(5)
    def get_stats(self):
        self.client.get("/api/devices/stats")
    
    @task(2)
    def get_sms(self):
        self.client.get("/api/devices/device123/sms")
```

**Run Load Test:**
```bash
locust -f locustfile.py --host=http://localhost:8000

# Open: http://localhost:8089
# Start test with 100 users, 10 users/sec spawn rate
```

### Benchmark Results

**Target for 25K users:**
- Average response time: < 100ms
- 95th percentile: < 500ms
- 99th percentile: < 1000ms
- Error rate: < 0.1%
- Throughput: 200+ req/sec

---

## ?? Cost Estimation

### Server Requirements for 25K Users

**Minimum:**
- CPU: 4 cores
- RAM: 8 GB
- Storage: 100 GB SSD
- Bandwidth: 1 TB/month

**Recommended:**
- CPU: 8 cores
- RAM: 16 GB
- Storage: 200 GB SSD
- Bandwidth: 2 TB/month

**Cloud Providers:**
- AWS EC2: t3.xlarge ($120/month)
- DigitalOcean: $96/month
- Hetzner: ?45/month (best value)

---

## ?? Quick Start Commands

```bash
# 1. Create indexes
python scripts/create_indexes.py

# 2. Install Redis
sudo apt-get install redis-server
sudo systemctl start redis

# 3. Start with multiple workers
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000

# 4. Monitor logs
tail -f logs/app.log | grep -E "ERROR|WARNING|Slow"

# 5. Check MongoDB performance
mongo parental_control --eval "db.currentOp(true)"
```

---

**Ready for 25,000+ users! ??**

Last Updated: November 2, 2025
