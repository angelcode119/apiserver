# 📚 مستندات سیستم مدیریت دستگاه

مستندات کامل و مرتب شده برای Device Management System

## 📑 فهرست مستندات

| شماره | فایل | موضوع | خطوط |
|-------|------|-------|------|
| 1️⃣ | [01-GETTING-STARTED.md](./01-GETTING-STARTED.md) | راهنمای شروع و نصب | ~200 |
| 2️⃣ | [02-AUTHENTICATION.md](./02-AUTHENTICATION.md) | احراز هویت و 2FA | ~150 |
| 3️⃣ | [03-ADMIN-API.md](./03-ADMIN-API.md) | API های مدیریت ادمین | ~150 |
| 4️⃣ | [04-DEVICE-API.md](./04-DEVICE-API.md) | API های مدیریت دستگاه | ~200 |
| 5️⃣ | [05-FIREBASE.md](./05-FIREBASE.md) | Firebase و دستورات | ~300 |
| 6️⃣ | [06-TELEGRAM-BOTS.md](./06-TELEGRAM-BOTS.md) | ربات‌های تلگرام | ~250 |
| 7️⃣ | [07-DEPLOYMENT.md](./07-DEPLOYMENT.md) | دیپلوی Production | ~300 |
| 8️⃣ | [08-PERFORMANCE-TESTING.md](./08-PERFORMANCE-TESTING.md) | بهینه‌سازی و تست | ~270 |

**📊 مجموع:** 8 فایل، ~1,720 خط

---

## 🎯 شروع سریع

### برای توسعه‌دهندگان جدید:
1. [01-GETTING-STARTED.md](./01-GETTING-STARTED.md) - نصب و راه‌اندازی
2. [02-AUTHENTICATION.md](./02-AUTHENTICATION.md) - فهم سیستم احراز هویت
3. [04-DEVICE-API.md](./04-DEVICE-API.md) - کار با API دستگاه‌ها

### برای توسعه‌دهندگان Android:
1. [05-FIREBASE.md](./05-FIREBASE.md) - پیاده‌سازی Firebase
2. [04-DEVICE-API.md](./04-DEVICE-API.md) - API های دستگاه

### برای DevOps:
1. [07-DEPLOYMENT.md](./07-DEPLOYMENT.md) - راه‌اندازی Production
2. [08-PERFORMANCE-TESTING.md](./08-PERFORMANCE-TESTING.md) - بهینه‌سازی

---

## ⚡ تغییرات نسخه 3.0.0

### ✅ مرتب‌سازی مستندات:
- 17 فایل قدیمی → 8 فایل مرتب
- 13,466 خط → 1,720 خط (87% کاهش!)
- دسته‌بندی منطقی موضوعات
- حذف تکرار و اضافات

### 🆕 ویژگی‌های جدید:
- مستندات خلاصه و کاربردی
- فهرست واضح و منظم
- مثال‌های عملی بیشتر
- راهنمای سریع برای هر نقش

---

## 📖 توضیحات مستندات

### 1️⃣ Getting Started
نصب، پیکربندی، و شروع کار با سیستم. شامل:
- نصب Dependencies
- تنظیم Environment
- اولین Admin
- Docker Deployment

### 2️⃣ Authentication
سیستم احراز هویت کامل. شامل:
- Admin Login (JWT + 2FA)
- Bot Authentication (Service Tokens)
- Telegram 2FA Setup
- Single Session Control

### 3️⃣ Admin API
مدیریت ادمین‌ها و Push Notifications. شامل:
- CRUD عملیات ادمین
- Activity Logs
- Push Notifications
- Permissions

### 4️⃣ Device API
مدیریت دستگاه‌ها و داده‌ها. شامل:
- Device Registration
- Commands
- SMS/Contacts/Call Logs
- Heartbeat & Status

### 5️⃣ Firebase
Firebase برای دستگاه‌ها و ادمین‌ها. شامل:
- Device Firebase Setup
- Admin Firebase Setup
- Commands
- Topic Messaging
- Call Forwarding

### 6️⃣ Telegram Bots
5 ربات تلگرام و Routing. شامل:
- Bot 1: Device Management
- Bot 2: SMS Only
- Bot 3: Admin Activities
- Bot 4: Authentication
- Bot 5: System Monitoring

### 7️⃣ Deployment
دیپلوی Production و Security. شامل:
- Server Setup
- Nginx Configuration
- SSL Certificate
- MongoDB Security
- Systemd Service

### 8️⃣ Performance & Testing
بهینه‌سازی برای 25K+ کاربر. شامل:
- Database Optimization
- Redis Caching
- Load Testing
- Monitoring
- Backup

---

## 🔗 لینک‌های مفید

- **GitHub**: <repository-url>
- **API Docs**: http://localhost:8765/docs
- **Support**: <support-email>

---

**آخرین به‌روزرسانی:** 10 نوامبر 2025  
**نسخه:** 3.0.0  
**وضعیت:** ✅ تکمیل شده و تمیز
