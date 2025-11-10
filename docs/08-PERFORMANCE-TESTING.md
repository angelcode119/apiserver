# Performance & Testing

Optimization guide for 25,000+ users and testing procedures.

## Load Estimation

**25,000 Users:**
- Average: 70 req/sec
- Peak: 35 req/sec sustained
- Burst: 150-200 req/sec
- 80% reads, 20% writes

## Database Optimization

### 1. Indexes

**Run:**
```bash
python scripts/create_indexes.py
```

**Verify:**
```javascript
db.devices.getIndexes()
db.admin_activities.getIndexes()
```

### 2. Connection Pool

**Edit `app/database.py`:**
```python
mongodb.client = AsyncIOMotorClient(
    settings.MONGODB_URL,
    maxPoolSize=200,
    minPoolSize=20,
    maxIdleTimeMS=30000
)
```

### 3. Query Optimization

**Use projection:**
```python
device = await mongodb.db.devices.find_one(
    {"device_id": device_id},
    {"device_id": 1, "model": 1, "status": 1}
)
```

**Use pagination:**
```python
devices = await mongodb.db.devices.find({}).skip(skip).limit(50).to_list(50)
```

## Redis Caching

### Install

```bash
sudo apt install redis-server
pip install redis aioredis
```

### Implementation

```python
from aioredis import Redis

redis = await Redis.from_url("redis://localhost")

# Cache stats
await redis.setex("stats:admin", 300, json.dumps(stats))

# Get cached
cached = await redis.get("stats:admin")
if cached:
    return json.loads(cached)
```

## Server Optimization

### Gunicorn Workers

```bash
gunicorn app.main:app   --workers 4   --worker-class uvicorn.workers.UvicornWorker   --bind 0.0.0.0:8765
```

### Nginx Configuration

```nginx
upstream backend {
    server 127.0.0.1:8765;
    server 127.0.0.1:8766;
    server 127.0.0.1:8767;
    server 127.0.0.1:8768;
}

server {
    listen 80;
    location / {
        proxy_pass http://backend;
    }
}
```

## Testing

### Activity Log Testing

```bash
# Login test
curl -X POST "http://localhost:8765/auth/login"   -H "Content-Type: application/json"   -d '{"username": "admin", "password": "pass"}'
```

**Check:**
- MongoDB: `db.admin_activities.find({activity_type: "login"})`
- Telegram: Bot 3 should receive notification
- Logs: `tail -f logs/app.log | grep "Activity logged"`

### Command Testing

```bash
curl -X POST "http://localhost:8765/api/devices/abc123/command"   -H "Authorization: Bearer TOKEN"   -d '{"command": "ping"}'
```

**Check:**
- Telegram Bot 3: Command notification
- Database: Activity logged
- Firebase: Message sent to device

### Load Testing

```bash
# Install locust
pip install locust

# Run test
locust -f test_load.py --host=http://localhost:8765
```

**test_load.py:**
```python
from locust import HttpUser, task, between

class AdminUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        response = self.client.post("/auth/login", json={
            "username": "admin",
            "password": "pass"
        })
        self.token = response.json()["temp_token"]
    
    @task
    def list_devices(self):
        self.client.get("/api/devices", headers={
            "Authorization": f"Bearer {self.token}"
        })
```

## Monitoring

### Logs

```bash
# Application
tail -f logs/app.log

# System
tail -f /var/log/syslog

# Nginx
tail -f /var/log/nginx/access.log
```

### Metrics

```python
# Track request duration
import time

start = time.time()
# ... operation ...
duration = time.time() - start
logger.info(f"Operation took {duration:.2f}s")
```

### Alerts

- Database connection errors
- High response times (>1s)
- Memory usage >80%
- Disk space <10%

## Backup

### MongoDB

```bash
mongodump --db parental_control --out /backup/$(date +%Y%m%d)
```

### Automated

```bash
# Crontab
0 2 * * * /opt/scripts/backup.sh
```

## Common Issues

### High CPU
- Check database queries
- Review indexes
- Optimize loops

### Memory Leaks
- Monitor with `htop`
- Check MongoDB connections
- Review async tasks

### Slow Queries
```javascript
db.setProfilingLevel(2)
db.system.profile.find().sort({ts: -1}).limit(10)
```

## Best Practices

- Use indexes for all queries
- Cache frequent reads
- Batch database operations
- Use async/await everywhere
- Monitor resource usage
- Regular backups
- Load test before production

**Last Updated**: November 10, 2025
