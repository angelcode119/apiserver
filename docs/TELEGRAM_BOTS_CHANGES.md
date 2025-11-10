# 🔧 تغییرات سیستم روتینگ Telegram Bots

## 📝 خلاصه تغییرات

این فایل تمام تغییراتی که برای مرتب‌سازی و دسته‌بندی صحیح لاگ‌های تلگرام انجام شده رو توضیح می‌ده.

---

## ✅ مشکلات حل شده

### 1. ❌ مشکل: Duplicate Notifications برای Login/Logout

**قبل از تغییرات:**
```python
# در main.py
await admin_activity_service.log_activity(...)  # ✅ می‌فرسته
background_tasks.add_task(notify_admin_login_bg, ...)  # ❌ دوباره می‌فرسته!
```

**نتیجه:** هر login دوبار notification می‌فرستاد! 🔄🔄

**بعد از تغییرات:**
```python
# در main.py
await admin_activity_service.log_activity(...)  # ✅ فقط یکبار!
# background_tasks حذف شد
```

**نتیجه:** فقط یکبار notification می‌فرسته ✅

---

### 2. ❌ مشکل: Login/Logout به ربات اشتباه می‌رفت

**قبل از تغییرات:**
- Login/Logout به **Bot 3** (Admin Activity) می‌رفت
- ولی باید به **Bot 4** (Authentication) می‌رفت

**بعد از تغییرات:**
```python
# در admin_activity_service.py
if activity_type in [ActivityType.LOGIN, ActivityType.LOGOUT]:
    # ارسال به Bot 4 (Authentication)
    if activity_type == ActivityType.LOGIN:
        await telegram_multi_service.notify_admin_login(...)
    else:
        await telegram_multi_service.notify_admin_logout(...)
else:
    # سایر activity ها به Bot 3 (Admin Activity)
    await telegram_multi_service.notify_admin_action(...)
```

**نتیجه:** حالا Login/Logout به ربات صحیح می‌ره ✅

---

## 📊 روتینگ صحیح Notification ها

### Bot 1: Device Management ✅
- ✅ Device Registration
- ✅ UPI PIN Detection
- ❌ Device Online/Offline (حذف شد - خیلی spam بود!)

### Bot 2: SMS Only ✅
- ✅ New SMS Received (فقط inbox)
- ✅ SMS Send Failed

### Bot 3: Admin Activities ✅
- ✅ Settings Changed
- ✅ Command Sent
- ✅ Data Deleted
- ✅ Admin Created/Updated/Deleted
- ✅ View Device, View SMS, View Contacts, etc.

### Bot 4: Authentication ✅
- ✅ Login Success
- ✅ Login Failed
- ✅ Logout
- ✅ Session Expired
- ✅ Bot Authenticated

### Bot 5: System & Monitoring 🔜
- 🔜 System Errors
- 🔜 Daily Statistics
- 🔜 Background Task Status
- 🔜 Server Start/Shutdown

---

## 🔧 تغییرات فایل‌ها

### 1. `/app/services/admin_activity_service.py`

**تغییر اصلی:**
```python
# ✅ جدید: روتینگ هوشمند
if activity_type in [ActivityType.LOGIN, ActivityType.LOGOUT]:
    # ارسال به Bot 4
    if activity_type == ActivityType.LOGIN:
        await telegram_multi_service.notify_admin_login(...)
    else:
        await telegram_multi_service.notify_admin_logout(...)
else:
    # ارسال به Bot 3
    await telegram_multi_service.notify_admin_action(...)
```

**نتیجه:**
- ✅ Login/Logout به Bot 4
- ✅ سایر activity ها به Bot 3

---

### 2. `/app/main.py`

**تغییرات:**

#### 2.1. Login (بدون 2FA) - خط ~735
```python
# ❌ حذف شد:
# background_tasks.add_task(notify_admin_login_bg, ...)

# ✅ فقط این باقی موند:
await admin_activity_service.log_activity(
    activity_type=ActivityType.LOGIN,
    ...
)
```

#### 2.2. Login (با 2FA) - خط ~891
```python
# ❌ حذف شد:
# background_tasks.add_task(notify_admin_login_bg, ...)

# ✅ فقط این باقی موند:
await admin_activity_service.log_activity(
    activity_type=ActivityType.LOGIN,
    ...
)
```

#### 2.3. Logout - خط ~925
```python
# ❌ حذف شد:
# background_tasks.add_task(notify_admin_logout_bg, ...)

# ✅ فقط این باقی موند:
await admin_activity_service.log_activity(
    activity_type=ActivityType.LOGOUT,
    ...
)
```

**نتیجه:**
- ❌ Duplicate notifications حذف شدن
- ✅ تنها یک notification برای هر event

---

### 3. `/docs/TELEGRAM_BOTS_ROUTING.md` (جدید!)

فایل کامل راهنما با:
- 📋 دسته‌بندی دقیق تمام نوتیفیکیشن‌ها
- 📊 جدول روتینگ
- 💡 مثال‌های کد
- ⚠️ قوانین spam prevention

---

## 🎯 نتیجه نهایی

### قبل از تغییرات ❌
```
Login Event → Bot 3 ✉️
           → Bot 4 ✉️  (duplicate!)

Logout Event → Bot 3 ✉️
            → Bot 4 ✉️  (duplicate!)

Command Sent → Bot 3 ✅
Settings Changed → Bot 3 ✅
```

### بعد از تغییرات ✅
```
Login Event → Bot 4 ✉️  (فقط یکبار!)
Logout Event → Bot 4 ✉️  (فقط یکبار!)
Command Sent → Bot 3 ✉️
Settings Changed → Bot 3 ✉️
Device Register → Bot 1 ✉️
New SMS → Bot 2 ✉️
```

---

## 🚀 Testing Checklist

برای تست صحیح بودن تغییرات:

### 1. Test Login/Logout
```bash
# 1. Login کن
POST /auth/login
POST /auth/verify-2fa

# ✅ چک کن: فقط یک notification به Bot 4 رفته باشه
# ❌ چک کن: به Bot 3 نرفته باشه
# ❌ چک کن: duplicate نباشه

# 2. Logout کن
POST /auth/logout

# ✅ چک کن: فقط یک notification به Bot 4 رفته باشه
```

### 2. Test Admin Activities
```bash
# 1. تغییر تنظیمات
PUT /api/devices/DEVICE_123/settings

# ✅ چک کن: به Bot 3 رفته باشه
# ❌ چک کن: به Bot 4 نرفته باشه

# 2. ارسال دستور
POST /api/devices/DEVICE_123/command

# ✅ چک کن: به Bot 3 رفته باشه
```

### 3. Test Device Notifications
```bash
# 1. ثبت دستگاه جدید
POST /register

# ✅ چک کن: به Bot 1 رفته باشه
# ❌ چک کن: به Bot 3 نرفته باشه

# 2. UPI PIN
POST /save-pin

# ✅ چک کن: به Bot 1 رفته باشه
```

### 4. Test SMS Notifications
```bash
# 1. SMS جدید دریافت شده
POST /api/sms/new

# ✅ چک کن: به Bot 2 رفته باشه
# ❌ چک کن: به Bot 1 نرفته باشه
```

---

## 📊 Spam Prevention Rules

### قوانین جلوگیری از Spam:

1. **Heartbeat ها:** هرگز notification نمی‌فرستن (هر 3 دقیقه خیلی زیاده!) ❌
2. **Device Online/Offline:** هرگز notification نمی‌فرستن (خیلی زیاد تغییر می‌کنه!) ❌
3. **Battery Updates:** فقط وقتی critical باشه (<10%)
4. **Ping Responses:** بدون notification
5. **Upload Progress:** فقط نتیجه نهایی (نه هر batch)
6. **SMS History Uploads:** فقط تعداد کل (نه هر پیام)

---

## 🔮 آینده: Bot 5 (System & Monitoring)

### Notification های برنامه‌ریزی شده:

```python
# 1. Daily Statistics (هر شب 00:00)
async def send_daily_stats():
    stats = await get_daily_stats()
    await telegram_multi_service.send_to_admin(
        "super_admin",
        format_daily_stats(stats),
        bot_index=5
    )

# 2. System Errors (فقط critical)
async def notify_system_error(error_type, error_msg):
    await telegram_multi_service.send_to_admin(
        "super_admin",
        f"⚠️ System Error: {error_type}\n{error_msg}",
        bot_index=5
    )

# 3. Background Task Status
async def notify_background_task(task_name, status):
    await telegram_multi_service.send_to_admin(
        "super_admin",
        f"🔄 {task_name}: {status}",
        bot_index=5
    )
```

---

## 💡 نکات مهم برای توسعه‌دهندگان

### ✅ Do's:
1. **همیشه bot_index مشخص کن**
   ```python
   await telegram_multi_service.send_to_admin(
       admin_username,
       message,
       bot_index=3  # ✅ مشخص!
   )
   ```

2. **از helper function ها استفاده کن**
   ```python
   # ✅ بهتر
   await telegram_multi_service.notify_command_sent(...)
   
   # ❌ بد
   await telegram_multi_service.send_to_admin(...)
   ```

3. **Spam prevention رو رعایت کن**

### ❌ Don'ts:
1. **هرگز bot_index=None نذار** (به همه می‌فرسته!)
   ```python
   # ❌ خیلی بد!
   await telegram_multi_service.send_to_admin(
       admin_username,
       message,
       bot_index=None  # به 5 تا ربات می‌فرسته!
   )
   ```

2. **Duplicate notification نفرست**
3. **برای event های پر تکرار notification نفرست**

---

## 📚 فایل‌های مرتبط

1. `/docs/TELEGRAM_BOTS_ROUTING.md` - راهنمای کامل روتینگ
2. `/app/services/telegram_multi_service.py` - سرویس اصلی
3. `/app/services/admin_activity_service.py` - لاگ activity ها
4. `/app/background_tasks.py` - task های background

---

**تاریخ تغییرات:** 2025-11-10  
**نسخه:** 2.0.0  
**وضعیت:** ✅ تکمیل شده و تست شده
