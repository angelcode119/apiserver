import aiohttp
import logging
import ssl
from datetime import datetime
from typing import Optional, Dict, List
from ..config import settings

logger = logging.getLogger(__name__)

class TelegramService:
    """سرویس ارسال نوتیفیکیشن به تلگرام با پشتیبانی از چند ربات"""
    
    def __init__(self):
        self.enabled = settings.TELEGRAM_ENABLED
        self.bots = {}  # {bot_id: {"token": "...", "chat_id": "...", "name": "..."}}
        
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        # بارگذاری تنظیمات ربات‌ها
        self._load_bots()
        
        if not self.enabled or not self.bots:
            logger.warning("⚠️  Telegram notifications disabled or no bots configured")
        else:
            logger.info(f"✅ Loaded {len(self.bots)} Telegram bots")
    
    def _load_bots(self):
        """بارگذاری تنظیمات ربات‌ها از config"""
        for bot_config in settings.TELEGRAM_BOTS:
            bot_id = bot_config.get("bot_id")
            token = bot_config.get("token")
            chat_id = bot_config.get("chat_id")
            name = bot_config.get("bot_name", f"Bot {bot_id}")
            
            # فقط ربات‌هایی که token و chat_id معتبر دارن رو اضافه کن
            if bot_id and token and chat_id and "TOKEN_HERE" not in token:
                self.bots[bot_id] = {
                    "token": token,
                    "chat_id": chat_id,
                    "name": name
                }
                logger.info(f"🤖 Bot {bot_id} loaded: {name}")
    
    def get_bot_info(self, bot_id: int) -> Optional[Dict]:
        """دریافت اطلاعات یک ربات"""
        return self.bots.get(bot_id)
    
    def get_all_bots(self) -> Dict[int, Dict]:
        """دریافت لیست تمام ربات‌ها"""
        return self.bots
    
    def get_available_bot_ids(self) -> List[int]:
        """دریافت لیست ID های ربات‌های فعال"""
        return list(self.bots.keys())
    
    async def send_message(
        self, 
        message: str, 
        bot_id: Optional[int] = None,
        parse_mode: str = "HTML"
    ):
        """
        ارسال پیام به تلگرام
        
        Args:
            message: متن پیام
            bot_id: ID ربات (اگر None باشه، به همه ربات‌ها میفرسته)
            parse_mode: نوع پارس پیام (HTML, Markdown)
        """
        if not self.enabled or not self.bots:
            return False
        
        # اگر bot_id مشخص شده، فقط به اون ربات بفرست
        if bot_id is not None:
            return await self._send_to_bot(bot_id, message, parse_mode)
        
        # اگر bot_id نداریم، به همه ربات‌ها بفرست (broadcast)
        results = []
        for bot_id in self.bots.keys():
            result = await self._send_to_bot(bot_id, message, parse_mode)
            results.append(result)
        
        return any(results)  # True اگه حداقل یکی موفق بود
    
    async def _send_to_bot(self, bot_id: int, message: str, parse_mode: str = "HTML"):
        """ارسال پیام به یک ربات خاص"""
        bot_info = self.bots.get(bot_id)
        
        if not bot_info:
            logger.warning(f"⚠️  Bot {bot_id} not found or not configured")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{bot_info['token']}/sendMessage"
            
            data = {
                "chat_id": bot_info['chat_id'],
                "text": message,
                "parse_mode": parse_mode
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, ssl=self.ssl_context) as response:
                    if response.status == 200:
                        logger.info(f"✅ Message sent via Bot {bot_id} ({bot_info['name']})")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Failed to send via Bot {bot_id}: {error_text}")
                        return False
        
        except Exception as e:
            logger.error(f"❌ Error sending via Bot {bot_id}: {e}")
            return False
    
    async def send_to_multiple_bots(self, bot_ids: List[int], message: str, parse_mode: str = "HTML"):
        """ارسال پیام به چند ربات مشخص"""
        results = {}
        for bot_id in bot_ids:
            result = await self._send_to_bot(bot_id, message, parse_mode)
            results[bot_id] = result
        return results
    
    # ═══════════════════════════════════════════════════════
    # 📱 Device Notifications
    # ═══════════════════════════════════════════════════════
    
    async def notify_device_connected(self, device_id: str, device_info: dict, bot_id: Optional[int] = None):
        message = f"""
🟢 <b>Device Connected</b>

📱 Device ID: <code>{device_id}</code>
📲 Model: {device_info.get('model', 'Unknown')}
🏭 Manufacturer: {device_info.get('manufacturer', 'Unknown')}
⚙️  OS: {device_info.get('osVersion', 'Unknown')}
🕐 Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        await self.send_message(message, bot_id=bot_id)
    
    async def notify_device_disconnected(self, device_id: str, bot_id: Optional[int] = None):
        message = f"""
🔴 <b>Device Disconnected</b>

📱 Device ID: <code>{device_id}</code>
🕐 Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        await self.send_message(message, bot_id=bot_id)
    
    async def notify_device_registered(self, device_id: str, device_info: dict, bot_id: Optional[int] = None):
        bot_name = ""
        if bot_id and bot_id in self.bots:
            bot_name = f"\n🤖 Assigned Bot: {self.bots[bot_id]['name']}"
        
        message = f"""
🆕 <b>New Device Registered</b>

📱 Device ID: <code>{device_id}</code>
📲 Model: {device_info.get('model', 'Unknown')}
🏭 Manufacturer: {device_info.get('manufacturer', 'Unknown')}
⚙️  OS: {device_info.get('osVersion', 'Unknown')}
📅 App Version: {device_info.get('appVersion', 'Unknown')}{bot_name}
🕐 Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

✅ Device is now being monitored!
"""
        await self.send_message(message, bot_id=bot_id)
    
    # ═══════════════════════════════════════════════════════
    # 👤 Admin Notifications
    # ═══════════════════════════════════════════════════════
    
    async def notify_admin_login(self, username: str, ip_address: str = None, success: bool = True, bot_id: Optional[int] = None):
        if success:
            icon = "✅"
            status = "Successful"
        else:
            icon = "❌"
            status = "Failed"
        
        ip_text = f"\n🌐 IP: <code>{ip_address}</code>" if ip_address else ""
        
        message = f"""
{icon} <b>Admin Login {status}</b>

👤 Username: <code>{username}</code>{ip_text}
🕐 Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        # اعلان ادمین به همه ربات‌ها میره (امنیتی)
        await self.send_message(message, bot_id=None)
    
    async def notify_admin_logout(self, username: str):
        message = f"""
🚪 <b>Admin Logout</b>

👤 Username: <code>{username}</code>
🕐 Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        # اعلان logout به همه ربات‌ها
        await self.send_message(message, bot_id=None)
    
    async def notify_command_sent(self, admin_username: str, device_id: str, command: str, bot_id: Optional[int] = None):
        message = f"""
📤 <b>Command Sent</b>

👤 Admin: <code>{admin_username}</code>
📱 Device: <code>{device_id}</code>
⚡ Command: <code>{command}</code>
🕐 Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        await self.send_message(message, bot_id=bot_id)
    
    async def notify_data_deleted(self, admin_username: str, data_type: str, count: int):
        message = f"""
🗑️ <b>Data Deleted</b>

👤 Admin: <code>{admin_username}</code>
📊 Type: {data_type}
🔢 Count: {count}
🕐 Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        # اعلان حذف داده به همه ربات‌ها (امنیتی)
        await self.send_message(message, bot_id=None)
    
    async def notify_admin_created(self, creator_username: str, new_admin_username: str, role: str):
        message = f"""
👥 <b>New Admin Created</b>

👤 Created by: <code>{creator_username}</code>
🆕 New admin: <code>{new_admin_username}</code>
🔐 Role: {role}
🕐 Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        # اعلان ادمین جدید به همه ربات‌ها (امنیتی)
        await self.send_message(message, bot_id=None)
    
    async def notify_settings_changed(self, admin_username: str, device_id: str, changes: dict, bot_id: Optional[int] = None):
        changes_text = "\n".join([f"• {k}: {v}" for k, v in changes.items()])
        
        message = f"""
⚙️ <b>Settings Changed</b>

👤 Admin: <code>{admin_username}</code>
📱 Device: <code>{device_id}</code>

<b>Changes:</b>
{changes_text}

🕐 Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        await self.send_message(message, bot_id=bot_id)
    
    async def notify_new_sms(self, device_id: str, from_number: str, preview: str, bot_id: Optional[int] = None):
        message = f"""
💬 <b>New SMS Received</b>

📱 Device: <code>{device_id}</code>
📞 From: <code>{from_number}</code>
📝 Preview: {preview[:50]}...
🕐 Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        await self.send_message(message, bot_id=bot_id)
    
    async def notify_error(self, error_type: str, error_message: str, details: dict = None):
        details_text = ""
        if details:
            details_text = "\n\n<b>Details:</b>\n" + "\n".join([f"• {k}: {v}" for k, v in details.items()])
        
        message = f"""
⚠️ <b>Error Occurred</b>

🔴 Type: {error_type}
📝 Message: {error_message}{details_text}
🕐 Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""
        # اعلان خطا به همه ربات‌ها
        await self.send_message(message, bot_id=None)

telegram_service = TelegramService()
