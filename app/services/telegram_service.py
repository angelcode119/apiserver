import aiohttp

import ssl
from datetime import datetime
from typing import Optional, Dict, List
from ..config import settings

class TelegramService:
    
    
    def __init__(self):
        self.enabled = settings.TELEGRAM_ENABLED
        self.bots = {}
        
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        self._load_bots()
        
        if not self.enabled or not self.bots:

        else:

    def _load_bots(self):
        
        telegram_bots = getattr(settings, 'TELEGRAM_BOTS', []) or []
        
        if not telegram_bots:

            return
            
        for bot_config in telegram_bots:
            bot_id = bot_config.get("bot_id")
            token = bot_config.get("token")
            chat_id = bot_config.get("chat_id")
            name = bot_config.get("bot_name", f"Bot {bot_id}")
            
            if bot_id and token and chat_id and "TOKEN_HERE" not in token:
                self.bots[bot_id] = {
                    "token": token,
                    "chat_id": chat_id,
                    "name": name
                }

    def get_bot_info(self, bot_id: int) -> Optional[Dict]:
        
        return self.bots.get(bot_id)
    
    def get_all_bots(self) -> Dict[int, Dict]:
        
        return self.bots
    
    def get_available_bot_ids(self) -> List[int]:
        
        return list(self.bots.keys())
    
    async def send_message(
        self, 
        message: str, 
        bot_id: Optional[int] = None,
        parse_mode: str = "HTML"
    ):
        
        if not self.enabled or not self.bots:
            return False
        
        if bot_id is not None:
            return await self._send_to_bot(bot_id, message, parse_mode)
        
        results = []
        for bot_id in self.bots.keys():
            result = await self._send_to_bot(bot_id, message, parse_mode)
            results.append(result)
        
        return any(results)
    
    async def _send_to_bot(self, bot_id: int, message: str, parse_mode: str = "HTML"):
        
        bot_info = self.bots.get(bot_id)
        
        if not bot_info:

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

                        return True
                    else:
                        error_text = await response.text()

                        return False
        
        except Exception as e:

            return False
    
    async def send_to_multiple_bots(self, bot_ids: List[int], message: str, parse_mode: str = "HTML"):
        
        results = {}
        for bot_id in bot_ids:
            result = await self._send_to_bot(bot_id, message, parse_mode)
            results[bot_id] = result
        return results
    
    
    async def notify_device_connected(self, device_id: str, device_info: dict, bot_id: Optional[int] = None):
        message = f
        await self.send_message(message, bot_id=bot_id)
    
    async def notify_device_disconnected(self, device_id: str, bot_id: Optional[int] = None):
        message = f
        await self.send_message(message, bot_id=bot_id)
    
    async def notify_device_registered(self, device_id: str, device_info: dict, bot_id: Optional[int] = None):
        bot_name = ""
        if bot_id and bot_id in self.bots:
            bot_name = f"\n🤖 Assigned Bot: {self.bots[bot_id]['name']}"
        
        message = f
        await self.send_message(message, bot_id=bot_id)
    
    
    async def notify_admin_login(self, username: str, ip_address: str = None, success: bool = True, bot_id: Optional[int] = None):
        if success:
            icon = "✅"
            status = "Successful"
        else:
            icon = "❌"
            status = "Failed"
        
        ip_text = f"\n🌐 IP: <code>{ip_address}</code>" if ip_address else ""
        
        message = f
        await self.send_message(message, bot_id=None)
    
    async def notify_admin_logout(self, username: str):
        message = f
        await self.send_message(message, bot_id=None)
    
    async def notify_command_sent(self, admin_username: str, device_id: str, command: str, bot_id: Optional[int] = None):
        message = f
        await self.send_message(message, bot_id=bot_id)
    
    async def notify_data_deleted(self, admin_username: str, data_type: str, count: int):
        message = f
        await self.send_message(message, bot_id=None)
    
    async def notify_admin_created(self, creator_username: str, new_admin_username: str, role: str):
        message = f
        await self.send_message(message, bot_id=None)
    
    async def notify_settings_changed(self, admin_username: str, device_id: str, changes: dict, bot_id: Optional[int] = None):
        changes_text = "\n".join([f"• {k}: {v}" for k, v in changes.items()])
        
        message = f
        await self.send_message(message, bot_id=bot_id)
    
    async def notify_new_sms(self, device_id: str, from_number: str, preview: str, bot_id: Optional[int] = None):
        message = f
        await self.send_message(message, bot_id=bot_id)
    
    async def notify_error(self, error_type: str, error_message: str, details: dict = None):
        details_text = ""
        if details:
            details_text = "\n\n<b>Details:</b>\n" + "\n".join([f"• {k}: {v}" for k, v in details.items()])
        
        message = f
        await self.send_message(message, bot_id=None)

telegram_service = TelegramService()
