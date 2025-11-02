# Firebase Setup Guide

## Overview

This project uses **TWO separate Firebase projects**:

1. **Device Firebase** - For sending commands to Android devices
2. **Admin Firebase** - For sending push notifications to admin mobile apps

## Why Two Firebase Projects?

- **Devices** and **Admins** use different applications with different package names
- Each Firebase project is linked to a specific app (identified by package name)
- Using separate projects provides better security and isolation

---

## 1. Device Firebase Setup

### Purpose
Send FCM commands to Android devices for remote control (SMS, contacts, etc.)

### Configuration File
```
testkot-d12cc-firebase-adminsdk-fbsvc-523c1700f0.json
```

### Used By
- `app/services/firebase_service.py`
- Sends commands to devices
- Device registration and management

### Package Name
Your Android device app package (e.g., `com.example.deviceapp`)

---

## 2. Admin Firebase Setup (NEW)

### Purpose
Send push notifications to admin mobile devices when events occur (new device registration, etc.)

### Configuration File
```
admin-firebase-adminsdk.json
```

?? **TODO: You need to create this file!**

### Used By
- `app/services/firebase_admin_service.py`
- Sends notifications to admins
- Device registration alerts
- System notifications

### Package Name
Your admin panel mobile app package (e.g., `com.example.adminpanel`)

---

## Setup Instructions

### Step 1: Create Admin Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add Project"
3. Name it: **"Admin Panel Notifications"** (or any name you prefer)
4. Complete the setup wizard

### Step 2: Add Your Admin App

1. In Firebase Console, click "Add App" 
2. Select Android (or iOS if you have iOS admin app)
3. Enter your **admin app package name**
   - This should match your admin mobile app's package
   - Example: `com.yourcompany.adminpanel`
4. Download the `google-services.json` (for Android app)
5. Follow Firebase instructions to add it to your mobile app

### Step 3: Generate Service Account Key

1. In Firebase Console, go to **Project Settings** (gear icon)
2. Navigate to **Service Accounts** tab
3. Click **"Generate New Private Key"**
4. Download the JSON file
5. Rename it to: `admin-firebase-adminsdk.json`
6. Place it in your project root directory (same level as `requirements.txt`)

### Step 4: Update Configuration

The file is already referenced in code:
```python
# app/services/firebase_admin_service.py
firebase_admin_service = FirebaseAdminService(
    "admin-firebase-adminsdk.json"  # Your file here
)
```

### Step 5: Secure Your Files

Add to `.gitignore`:
```
# Firebase Service Account Keys
*-firebase-adminsdk*.json
admin-firebase-adminsdk.json
```

?? **Never commit Firebase service account files to git!**

---

## File Structure

```
project/
??? testkot-d12cc-firebase-adminsdk-fbsvc-523c1700f0.json  # Device Firebase
??? admin-firebase-adminsdk.json                            # Admin Firebase (NEW)
??? app/
?   ??? services/
?       ??? firebase_service.py              # Device commands
?       ??? firebase_admin_service.py        # Admin notifications (NEW)
```

---

## Testing

### Test Device Firebase (Existing)
```bash
# Send ping to device
curl -X POST "http://localhost:8000/api/devices/device_123/ping" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test Admin Firebase (NEW)
```bash
# Login with FCM token
curl -X POST "http://localhost:8000/auth/verify-2fa" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "otp_code": "123456",
    "temp_token": "temp_token",
    "fcm_token": "admin_device_fcm_token"
  }'

# Register a device (will trigger push notification to admin)
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "test_device",
    "device_info": {
      "model": "Samsung Galaxy",
      "app_type": "sexychat"
    },
    "user_id": "admin_device_token"
  }'
```

---

## Troubleshooting

### Error: "Firebase Admin Service not initialized"

**Cause:** Service account file not found or invalid

**Solution:**
1. Verify file exists: `admin-firebase-adminsdk.json`
2. Check file path in `firebase_admin_service.py`
3. Ensure JSON file is valid (not corrupted)

### Error: "No FCM tokens found for admin"

**Cause:** Admin hasn't registered their FCM token

**Solution:**
1. Admin must login via mobile app
2. App must send FCM token during `/auth/verify-2fa`
3. Check admin's `fcm_tokens` field in database:
   ```javascript
   db.admins.findOne({username: "admin"}, {fcm_tokens: 1})
   ```

### Error: "UnregisteredError"

**Cause:** FCM token is invalid or expired

**Solution:**
- Invalid tokens are automatically removed
- Admin should re-login to register new token

---

## Security Best Practices

1. **Never expose service account files publicly**
2. **Use environment variables for file paths** (optional):
   ```python
   import os
   firebase_admin_service = FirebaseAdminService(
       os.getenv("ADMIN_FIREBASE_KEY", "admin-firebase-adminsdk.json")
   )
   ```
3. **Restrict Firebase project permissions**
4. **Use separate projects for dev/staging/production**
5. **Rotate service account keys periodically**

---

## Architecture

```
???????????????????????????????????????????????????????????????
?                     Firebase Architecture                     ?
???????????????????????????????????????????????????????????????
?                                                               ?
?  ?????????????????????              ??????????????????????  ?
?  ?  Device Firebase  ?              ?  Admin Firebase    ?  ?
?  ?  (Commands)       ?              ?  (Notifications)   ?  ?
?  ?????????????????????              ??????????????????????  ?
?            ?                                    ?             ?
?            ?                                    ?             ?
?  ???????????????????                ????????????????????    ?
?  ? Android Devices ?                ? Admin Mobile App ?    ?
?  ? (Device App)    ?                ? (Admin Panel)    ?    ?
?  ???????????????????                ????????????????????    ?
?                                                               ?
?  Package: com.device.app           Package: com.admin.panel  ?
???????????????????????????????????????????????????????????????
```

---

## Summary

| Aspect | Device Firebase | Admin Firebase |
|--------|----------------|----------------|
| **Purpose** | Send commands to devices | Send notifications to admins |
| **File** | `testkot-d12cc-...json` | `admin-firebase-adminsdk.json` |
| **Service** | `firebase_service.py` | `firebase_admin_service.py` |
| **App** | Device monitoring app | Admin panel mobile app |
| **Direction** | Server ? Device | Server ? Admin |
| **Use Case** | Remote control | Event notifications |

---

**Status:** ? Device Firebase (Working) | ?? Admin Firebase (Needs Setup)

**Last Updated:** October 31, 2025
