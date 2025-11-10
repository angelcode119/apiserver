# Device Online/Offline Status Logic

Complete documentation for device status monitoring and heartbeat mechanism.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Heartbeat Mechanism](#heartbeat-mechanism)
3. [Status Logic](#status-logic)
4. [Background Monitoring](#background-monitoring)
5. [API Endpoints](#api-endpoints)
6. [Status Transitions](#status-transitions)
7. [Best Practices](#best-practices)

---

## Overview

The system monitors device availability using a **heartbeat mechanism**. Devices send periodic heartbeats to indicate they are online and responsive.

### Key Parameters

- **Heartbeat Interval:** 3 minutes (device sends heartbeat every 3 min)
- **Timeout Period:** 6 minutes (no heartbeat = offline)
- **Background Check:** Every 5 minutes (automatic cleanup)

---

## Heartbeat Mechanism

### How It Works

```
Device (Android App)
    ↓
    | Every 3 minutes
    ↓
POST /devices/heartbeat
    ↓
Server marks device as ONLINE
    ↓
Updates last_ping timestamp
```

### Heartbeat Endpoint

**Endpoint:** `POST /devices/heartbeat`

**Request Body:**
```json
{
  "deviceId": "abc123xyz"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Heartbeat received"
}
```

**Server Actions:**
1. Updates `last_ping` to current time
2. Sets `status = "online"`
3. Sets `is_online = true`
4. Updates `last_online_update`

---

## Status Logic

### Device Status Values

| Status | Description | Condition |
|--------|-------------|-----------|
| `online` | Device is active and responsive | Heartbeat within last 6 minutes |
| `offline` | Device is inactive or disconnected | No heartbeat for 6+ minutes |
| `pending` | Device just registered | Initial state before first heartbeat |

### Status Determination

```python
if last_ping > (now - 6 minutes):
    status = "online"
else:
    status = "offline"
```

### Database Fields

```json
{
  "device_id": "abc123xyz",
  "status": "online",           // Current status
  "is_online": true,            // Boolean flag
  "last_ping": "2025-11-09T10:00:00",  // Last heartbeat time
  "last_online_update": "2025-11-09T10:00:00"  // Last status change
}
```

---

## Background Monitoring

### Automatic Offline Detection

A **background task** runs continuously to detect offline devices:

**Task Name:** `check_offline_devices_bg`

**Execution:** Every 5 minutes

**Logic:**
```python
# Find devices that haven't sent heartbeat in 6+ minutes
six_minutes_ago = now - timedelta(minutes=6)

devices_to_mark_offline = devices.find({
    "last_ping": {"$lt": six_minutes_ago},
    "status": "online"
})

# Mark them as offline
devices.update_many({...}, {
    "$set": {
        "status": "offline",
        "is_online": False,
        "last_online_update": now
    }
})
```

**Benefits:**
- Automatic cleanup (no manual intervention)
- Periodic status updates
- Consistent state across all API calls

---

## API Endpoints

### 1. Send Heartbeat

**Endpoint:** `POST /devices/heartbeat`

**Description:** Device sends periodic heartbeat.

**Frequency:** Every 3 minutes (from device)

**Request:**
```json
{
  "deviceId": "abc123xyz"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Heartbeat received"
}
```

---

### 2. Get Device Status

**Endpoint:** `GET /api/devices/{device_id}`

**Description:** Get device details including current status.

**Authorization:** Required

**Response:**
```json
{
  "device_id": "abc123xyz",
  "status": "online",
  "is_online": true,
  "last_ping": "2025-11-09T10:00:00",
  "last_online_update": "2025-11-09T10:00:00",
  ...
}
```

**Note:** Status is automatically calculated based on `last_ping`.

---

### 3. Get Device Statistics

**Endpoint:** `GET /api/devices/stats`

**Description:** Get aggregated device statistics.

**Response:**
```json
{
  "total_devices": 100,
  "active_devices": 85,
  "pending_devices": 5,
  "online_devices": 70,
  "offline_devices": 30
}
```

**Note:** Automatically updates offline devices before counting.

---

### 4. List Devices

**Endpoint:** `GET /api/devices`

**Description:** List all devices with current status.

**Response:**
```json
{
  "devices": [
    {
      "device_id": "abc123",
      "status": "online",
      "last_ping": "2025-11-09T10:00:00"
    },
    {
      "device_id": "xyz789",
      "status": "offline",
      "last_ping": "2025-11-09T09:50:00"
    }
  ],
  "total": 2
}
```

**Note:** Offline devices are updated before listing.

---

## Status Transitions

### State Diagram

```
     REGISTER
        ↓
    [PENDING]
        ↓
   First Heartbeat
        ↓
     [ONLINE] ←→ Heartbeat every 3 min
        ↓
  No heartbeat for 6+ min
        ↓
    [OFFLINE]
        ↓
  Heartbeat received
        ↓
     [ONLINE]
```

### Transition Examples

#### Example 1: Device Comes Online

```
T=0:00   Device registers → status = "pending"
T=0:05   First heartbeat → status = "online"
T=3:05   Heartbeat #2 → status = "online" (still)
T=6:05   Heartbeat #3 → status = "online" (still)
```

#### Example 2: Device Goes Offline

```
T=0:00   Last heartbeat → status = "online"
T=3:00   (no heartbeat)
T=6:00   (no heartbeat)
T=6:01   Background task → status = "offline" ❌
```

#### Example 3: Device Reconnects

```
T=0:00   Device offline → status = "offline"
T=1:00   Heartbeat received → status = "online" ✅
```

---

## Best Practices

### For Device (Android App)

1. **Send heartbeat every 3 minutes**
   - Use WorkManager or similar for reliability
   - Handle network errors gracefully
   - Retry failed heartbeats

2. **Handle offline state**
   - Cache data when offline
   - Sync when connection restored
   - Show offline indicator to user

3. **Battery optimization**
   - Use efficient scheduling
   - Batch operations
   - Wake lock management

### For Server (Backend)

1. **Monitor heartbeat frequency**
   - Log missed heartbeats
   - Alert on high offline rates
   - Track device health metrics

2. **Graceful degradation**
   - Don't send commands to offline devices
   - Queue commands for later delivery
   - Notify admin of offline status

3. **Database optimization**
   - Index on `last_ping` field
   - Regular cleanup of old data
   - Efficient queries

### For Admin (Frontend)

1. **Real-time updates**
   - Poll device status periodically
   - Show last seen timestamp
   - Visual indicators (green/red dots)

2. **Status filtering**
   - Filter by online/offline
   - Sort by last seen
   - Search by status

3. **Alerts**
   - Notify when device goes offline
   - Track offline duration
   - Automatic recovery detection

---

## Troubleshooting

### Device Shows Offline But Is Active

**Possible Causes:**
1. Network connectivity issues
2. Heartbeat service stopped
3. WorkManager not running
4. Server timeout too aggressive

**Solutions:**
- Check device network connection
- Restart device services (`start_services` command)
- Verify WorkManager is active
- Check server logs for heartbeat reception

---

### Device Shows Online But Not Responding

**Possible Causes:**
1. Heartbeat working but other services failed
2. FCM token expired
3. App in background/killed
4. Partial connectivity

**Solutions:**
- Send ping command to verify
- Check FCM token validity
- Ensure app has background permissions
- Restart all services

---

### Status Flapping (Online/Offline/Online)

**Possible Causes:**
1. Intermittent network
2. Device battery saver mode
3. Background restrictions
4. Network latency

**Solutions:**
- Check network stability
- Disable battery optimization for app
- Request unrestricted background access
- Increase timeout period (if needed)

---

## Monitoring & Alerts

### Key Metrics to Monitor

1. **Heartbeat Success Rate**
   - % of expected heartbeats received
   - Track per device and globally

2. **Offline Duration**
   - Average time devices stay offline
   - Alert on prolonged offline

3. **Reconnection Time**
   - Time to recover from offline state
   - Identify devices with issues

4. **Background Task Health**
   - Verify task is running
   - Check execution logs
   - Monitor error rates

### Logging

**Heartbeat Received:**
```
💓 Heartbeat received from device: abc123xyz
```

**Devices Marked Offline:**
```
🔴 Marked 5 devices as offline (heartbeat timeout)
```

**Background Task Started:**
```
🔄 Background task started: Offline devices checker (every 5 min)
```

---

## Configuration

### Adjustable Parameters

Located in `app/services/device_service.py`:

```python
# Heartbeat timeout (default: 6 minutes)
six_minutes_ago = datetime.utcnow() - timedelta(minutes=6)
```

Located in `app/background_tasks.py`:

```python
# Background check interval (default: 5 minutes)
await asyncio.sleep(300)  # 5 minutes
```

### Recommended Values

| Environment | Heartbeat Interval | Timeout | Background Check |
|-------------|-------------------|---------|------------------|
| Production | 3 minutes | 6 minutes | 5 minutes |
| Development | 1 minute | 2 minutes | 1 minute |
| Testing | 30 seconds | 1 minute | 30 seconds |

---

## Technical Implementation

### Code Locations

**Heartbeat Endpoint:**
- `app/main.py` → `POST /devices/heartbeat`

**Status Logic:**
- `app/services/device_service.py` → `get_device()`
- `app/services/device_service.py` → `get_devices_for_admin()`
- `app/services/device_service.py` → `get_stats()`

**Background Task:**
- `app/background_tasks.py` → `check_offline_devices_bg()`
- `app/main.py` → `startup_event()` (task starter)

**Database Indexes:**
- `app/database.py` → `create_indexes()`
  - Index on `last_ping`
  - Index on `status`
  - Index on `is_online`

---

## Examples

### Example 1: Check Device Status (Python)

```python
import requests

headers = {"Authorization": "Bearer YOUR_TOKEN"}
response = requests.get(
    "http://localhost:8765/api/devices/abc123",
    headers=headers
)

device = response.json()
print(f"Device Status: {device['status']}")
print(f"Last Seen: {device['last_ping']}")
print(f"Online: {device['is_online']}")
```

---

### Example 2: Monitor Online Devices

```python
import requests

headers = {"Authorization": "Bearer YOUR_TOKEN"}
response = requests.get(
    "http://localhost:8765/api/devices/stats",
    headers=headers
)

stats = response.json()
print(f"Online Devices: {stats['online_devices']}")
print(f"Offline Devices: {stats['offline_devices']}")
print(f"Total: {stats['total_devices']}")
```

---

### Example 3: Filter Online Devices

```python
import requests

headers = {"Authorization": "Bearer YOUR_TOKEN"}
response = requests.get(
    "http://localhost:8765/api/devices",
    headers=headers
)

devices = response.json()['devices']
online_devices = [d for d in devices if d['status'] == 'online']

print(f"Found {len(online_devices)} online devices")
for device in online_devices:
    print(f"- {device['device_id']} ({device['model']})")
```

---

**Last Updated:** November 9, 2025  
**Version:** 2.0.0
