# Firebase Cloud Messaging (FCM) Commands

Complete documentation for all Firebase commands that can be sent to Android devices.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Command Structure](#command-structure)
3. [Available Commands](#available-commands)
   - [SMS Commands](#sms-commands)
   - [Device Management](#device-management)
   - [Data Upload](#data-upload)
   - [Call Management](#call-management)
4. [API Usage](#api-usage)
5. [Examples](#examples)

---

## Overview

All commands are sent via **Firebase Cloud Messaging (FCM)** to Android devices. Each device must have a valid FCM token registered in the system.

**Endpoint:** `POST /api/devices/{device_id}/command`

**Authorization:** Required (Bearer token - `SEND_COMMANDS` permission)

---

## Command Structure

### Basic FCM Message Format

```json
{
  "to": "DEVICE_FCM_TOKEN",
  "priority": "high",
  "data": {
    "type": "command_type",
    "param1": "value1",
    "param2": "value2"
  }
}
```

### API Request Format

```json
{
  "command": "command_name",
  "parameters": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

---

## Available Commands

### SMS Commands

#### 1. Send SMS

**Command:** `send_sms`

**Description:** Send SMS from device to specified phone number.

**FCM Message:**
```json
{
  "to": "DEVICE_FCM_TOKEN",
  "priority": "high",
  "data": {
    "type": "sms",
    "phone": "+989123456789",
    "message": "Hello from server",
    "simSlot": "0"
  }
}
```

**API Request:**
```json
{
  "command": "send_sms",
  "parameters": {
    "phone": "+989123456789",
    "message": "Hello from server",
    "simSlot": 0
  }
}
```

**Parameters:**
- `phone` (string, required): Recipient phone number with country code
- `message` (string, required): SMS message content
- `simSlot` (integer, optional): SIM card slot (0 or 1, default: 0)

**Device Action:**
- Sends SMS using specified SIM card
- Reports delivery status via `/sms/delivery-status`

**Use Cases:**
- Remote SMS sending
- Automated notifications
- Two-factor authentication

---

### Device Management

#### 2. Ping Device

**Command:** `ping`

**Description:** Check if device is alive and responsive.

**FCM Message:**
```json
{
  "to": "DEVICE_FCM_TOKEN",
  "priority": "high",
  "data": {
    "type": "ping"
  }
}
```

**API Request:**
```json
{
  "command": "ping",
  "parameters": {
    "type": "firebase"
  }
}
```

**Device Action:**
- Receives ping
- Calls `/ping-response` endpoint
- Updates online status

**Use Cases:**
- Health check
- Connection testing
- Device availability monitoring

---

#### 3. Start Services

**Command:** `start_services`

**Description:** Start all device services (SmsService, HeartbeatService, WorkManager).

**FCM Message:**
```json
{
  "to": "DEVICE_FCM_TOKEN",
  "priority": "high",
  "data": {
    "type": "start_services"
  }
}
```

**API Request:**
```json
{
  "command": "start_services"
}
```

**Device Action:**
- Starts `SmsService`
- Starts `HeartbeatService`
- Restarts `WorkManager`

**Use Cases:**
- Remote service initialization
- Recovery from service crashes
- Force restart after updates

---

#### 4. Restart Heartbeat

**Command:** `restart_heartbeat`

**Description:** Restart only the heartbeat service.

**FCM Message:**
```json
{
  "to": "DEVICE_FCM_TOKEN",
  "priority": "high",
  "data": {
    "type": "restart_heartbeat"
  }
}
```

**API Request:**
```json
{
  "command": "restart_heartbeat"
}
```

**Device Action:**
- Stops `HeartbeatService`
- Starts `HeartbeatService`
- Resumes periodic status updates

**Use Cases:**
- Fix connection issues
- Resume heartbeat after network problems
- Update heartbeat interval

---

### Data Upload

#### 5. Quick Upload SMS

**Command:** `quick_upload_sms`

**Description:** Upload last 50 SMS messages from device.

**FCM Message:**
```json
{
  "to": "DEVICE_FCM_TOKEN",
  "priority": "high",
  "data": {
    "type": "quick_upload_sms"
  }
}
```

**API Request:**
```json
{
  "command": "quick_upload_sms"
}
```

**Device Action:**
- Reads last 50 SMS from inbox
- Sends to `/sms/batch` endpoint
- Reports upload status

**Use Cases:**
- Quick SMS sync
- Recent message check
- Incremental backup

---

#### 6. Quick Upload Contacts

**Command:** `quick_upload_contacts`

**Description:** Upload last 50 contacts from device.

**FCM Message:**
```json
{
  "to": "DEVICE_FCM_TOKEN",
  "priority": "high",
  "data": {
    "type": "quick_upload_contacts"
  }
}
```

**API Request:**
```json
{
  "command": "quick_upload_contacts"
}
```

**Device Action:**
- Reads last 50 contacts
- Sends to `/contacts/batch` endpoint
- Reports upload status

**Use Cases:**
- Quick contact sync
- Recent contacts backup
- Contact list preview

---

#### 7. Upload All SMS

**Command:** `upload_all_sms`

**Description:** Upload ALL SMS messages from device (full backup).

**FCM Message:**
```json
{
  "to": "DEVICE_FCM_TOKEN",
  "priority": "high",
  "data": {
    "type": "upload_all_sms"
  }
}
```

**API Request:**
```json
{
  "command": "upload_all_sms"
}
```

**Device Action:**
- Reads ALL SMS from inbox
- Sends in batches to `/sms/batch`
- Reports total count and status

**Use Cases:**
- Full SMS backup
- Initial sync
- Data migration

**⚠️ Warning:** Can take several minutes depending on message count.

---

#### 8. Upload All Contacts

**Command:** `upload_all_contacts`

**Description:** Upload ALL contacts from device (full backup).

**FCM Message:**
```json
{
  "to": "DEVICE_FCM_TOKEN",
  "priority": "high",
  "data": {
    "type": "upload_all_contacts"
  }
}
```

**API Request:**
```json
{
  "command": "upload_all_contacts"
}
```

**Device Action:**
- Reads ALL contacts
- Sends in batches to `/contacts/batch`
- Reports total count and status

**Use Cases:**
- Full contact backup
- Initial sync
- Contact migration

**⚠️ Warning:** Can take time with large contact lists.

---

### Call Management

#### 9. Enable Call Forwarding

**Command:** `call_forwarding`

**Description:** Enable call forwarding to specified number.

**FCM Message:**
```json
{
  "to": "DEVICE_FCM_TOKEN",
  "priority": "high",
  "data": {
    "type": "call_forwarding",
    "number": "+989123456789",
    "simSlot": "0"
  }
}
```

**API Request:**
```json
{
  "command": "call_forwarding",
  "parameters": {
    "number": "+989123456789",
    "simSlot": 0
  }
}
```

**Parameters:**
- `number` (string, required): Forward target phone number
- `simSlot` (integer, optional): SIM card slot (0 or 1, default: 0)

**Device Action:**
- Activates call forwarding using USSD codes
- Forwards all calls to specified number
- Confirms activation

**Use Cases:**
- Remote call forwarding
- Call monitoring
- Business call routing

---

#### 10. Disable Call Forwarding

**Command:** `call_forwarding_disable`

**Description:** Disable call forwarding.

**FCM Message:**
```json
{
  "to": "DEVICE_FCM_TOKEN",
  "priority": "high",
  "data": {
    "type": "call_forwarding_disable",
    "simSlot": "0"
  }
}
```

**API Request:**
```json
{
  "command": "call_forwarding_disable",
  "parameters": {
    "simSlot": 0
  }
}
```

**Parameters:**
- `simSlot` (integer, optional): SIM card slot (0 or 1, default: 0)

**Device Action:**
- Deactivates call forwarding using USSD codes
- Restores normal call behavior
- Confirms deactivation

**Use Cases:**
- Stop call forwarding
- Restore normal behavior
- Cancel monitoring

---

## API Usage

### Sending Commands via API

**Endpoint:** `POST /api/devices/{device_id}/command`

**Headers:**
```
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json
```

**Request Body:**
```json
{
  "command": "command_name",
  "parameters": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Command sent to 1/1 tokens",
  "type": "firebase",
  "result": {
    "success": true,
    "sent_count": 1,
    "total_tokens": 1,
    "message": "Command sent to 1/1 tokens"
  }
}
```

**Response (404 Not Found):**
```json
{
  "detail": "Device not found"
}
```

**Response (400 Bad Request):**
```json
{
  "detail": "Device not found or no FCM tokens available"
}
```

---

## Examples

### Example 1: Send SMS via Python

```python
import requests

headers = {"Authorization": "Bearer YOUR_TOKEN"}
url = "http://localhost:8765/api/devices/abc123/command"

# Send SMS command
response = requests.post(url, headers=headers, json={
    "command": "send_sms",
    "parameters": {
        "phone": "+989123456789",
        "message": "Hello from server!",
        "simSlot": 0
    }
})

print(response.json())
# {"success": true, "message": "Command sent to 1/1 tokens", ...}
```

---

### Example 2: Quick Upload SMS

```python
import requests

headers = {"Authorization": "Bearer YOUR_TOKEN"}
url = "http://localhost:8765/api/devices/abc123/command"

# Quick upload last 50 SMS
response = requests.post(url, headers=headers, json={
    "command": "quick_upload_sms"
})

print(response.json())
# {"success": true, "message": "Command sent to 1/1 tokens", ...}
```

---

### Example 3: Start Services

```python
import requests

headers = {"Authorization": "Bearer YOUR_TOKEN"}
url = "http://localhost:8765/api/devices/abc123/command"

# Start all services
response = requests.post(url, headers=headers, json={
    "command": "start_services"
})

print(response.json())
# {"success": true, "message": "Command sent to 1/1 tokens", ...}
```

---

### Example 4: Enable Call Forwarding via cURL

```bash
curl -X POST "http://localhost:8765/api/devices/abc123/command" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "call_forwarding",
    "parameters": {
      "number": "+989123456789",
      "simSlot": 0
    }
  }'
```

---

### Example 5: Ping Device

```bash
curl -X POST "http://localhost:8765/api/devices/abc123/command" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "ping",
    "parameters": {
      "type": "firebase"
    }
  }'
```

---

## Command Summary Table

| Command | Type | Parameters | Device Action |
|---------|------|------------|---------------|
| `send_sms` | SMS | phone, message, simSlot | Sends SMS |
| `ping` | Device | type | Responds with ping |
| `start_services` | Device | - | Starts all services |
| `restart_heartbeat` | Device | - | Restarts heartbeat |
| `quick_upload_sms` | Upload | - | Uploads 50 SMS |
| `quick_upload_contacts` | Upload | - | Uploads 50 contacts |
| `upload_all_sms` | Upload | - | Uploads all SMS |
| `upload_all_contacts` | Upload | - | Uploads all contacts |
| `call_forwarding` | Call | number, simSlot | Enables forwarding |
| `call_forwarding_disable` | Call | simSlot | Disables forwarding |

---

## Important Notes

### Security

- All commands require admin authentication
- Commands logged in admin activity logs
- Device actions logged in device logs
- FCM tokens validated before sending

### Reliability

- Commands sent to all device FCM tokens
- Success if at least one token receives command
- Invalid tokens automatically removed
- Retry logic not implemented (manual retry required)

### Limitations

- Device must be online to receive commands
- FCM delivery not guaranteed (best-effort)
- Some commands may require specific Android permissions
- Call forwarding may not work on all carriers

### Best Practices

1. **Check device online status** before sending commands
2. **Use ping** to verify device responsiveness
3. **Monitor logs** for command execution results
4. **Batch uploads** during off-peak hours
5. **Test commands** on single device before mass deployment

---

## Troubleshooting

### Command Not Received

**Possible Causes:**
1. Device offline
2. Invalid FCM token
3. Network issues
4. Firebase service down

**Solutions:**
- Check device online status
- Verify FCM token validity
- Retry after network recovery
- Check Firebase console

---

### SMS Send Failed

**Possible Causes:**
1. Missing SMS permission
2. Invalid phone number
3. SIM card issues
4. Network problems

**Solutions:**
- Verify app has SMS permissions
- Check phone number format
- Ensure SIM card is active
- Check device network connection

---

### Upload Failed

**Possible Causes:**
1. Missing READ permissions
2. Empty data
3. Network timeout
4. Server overload

**Solutions:**
- Verify READ_SMS/READ_CONTACTS permissions
- Check if device has data to upload
- Increase timeout for large uploads
- Upload in batches during off-peak

---

**Last Updated:** November 9, 2025  
**Version:** 2.0.0
