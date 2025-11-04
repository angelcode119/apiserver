from datetime import datetime, timedelta
from typing import Optional, List

from bson import ObjectId

from ..database import mongodb
from ..models.admin_schemas import AdminActivity, ActivityType

class AdminActivityService:

    @staticmethod
    async def log_activity(
        admin_username: str,
        activity_type: ActivityType,
        description: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_id: Optional[str] = None,
        metadata: dict = None,
        success: bool = True,
        error_message: Optional[str] = None,
        send_telegram: bool = True
    ):
        try:
            activity = AdminActivity(
                admin_username=admin_username,
                activity_type=activity_type,
                description=description,
                ip_address=ip_address,
                user_agent=user_agent,
                device_id=device_id,
                metadata=metadata or {},
                success=success,
                error_message=error_message
            )

            await mongodb.db.admin_activities.insert_one(activity.model_dump())

            if send_telegram:
                try:
                    from .telegram_multi_service import telegram_multi_service
                    
                    details = description
                    if device_id:
                        details += f"\n📱 Device: {device_id}"
                    if not success and error_message:
                        details += f"\n❌ Error: {error_message}"
                    
                    await telegram_multi_service.notify_admin_action(
                        admin_username=admin_username,
                        action=activity_type.value,
                        details=details,
                        ip_address=ip_address
                    )

                except Exception as telegram_error:

        except Exception as e:

    @staticmethod
    async def get_activities(
        admin_username: Optional[str] = None,
        activity_type: Optional[ActivityType] = None,
        device_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[dict]:
        try:
            query = {}

            if admin_username:
                query["admin_username"] = admin_username

            if activity_type:
                query["activity_type"] = activity_type

            if device_id:
                query["device_id"] = device_id

            if start_date or end_date:
                query["timestamp"] = {}
                if start_date:
                    query["timestamp"]["$gte"] = start_date
                if end_date:
                    query["timestamp"]["$lte"] = end_date

            cursor = mongodb.db.admin_activities.find(query).sort("timestamp", -1).skip(skip).limit(limit)

            activities = await cursor.to_list(length=limit)

            for activity in activities:
                if "_id" in activity:
                    activity["_id"] = str(activity["_id"])
                for key, value in activity.items():
                    if isinstance(value, ObjectId):
                        activity[key] = str(value)

            return activities

        except Exception as e:

            return []

    @staticmethod
    async def get_activity_stats(admin_username: Optional[str] = None) -> dict:
        try:
            pipeline = []

            if admin_username:
                pipeline.append({"$match": {"admin_username": admin_username}})

            pipeline.extend([
                {
                    "$group": {
                        "_id": "$activity_type",
                        "count": {"$sum": 1}
                    }
                }
            ])

            cursor = mongodb.db.admin_activities.aggregate(pipeline)
            results = await cursor.to_list(length=100)

            stats = {item["_id"]: item["count"] for item in results}

            return stats

        except Exception as e:

            return {}

    @staticmethod
    async def get_recent_logins(limit: int = 10) -> List[dict]:
        try:
            cursor = mongodb.db.admin_activities.find(
                {"activity_type": ActivityType.LOGIN}
            ).sort("timestamp", -1).limit(limit)

            logins = await cursor.to_list(length=limit)

            for login in logins:
                if "_id" in login:
                    login["_id"] = str(login["_id"])

            return logins

        except Exception as e:

            return []

    @staticmethod
    async def cleanup_old_activities(days: int = 90):
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            result = await mongodb.db.admin_activities.delete_many(
                {"timestamp": {"$lt": cutoff_date}}
            )

            return result.deleted_count

        except Exception as e:

            return 0

admin_activity_service = AdminActivityService()