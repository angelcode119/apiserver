from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status
import logging
import secrets

from ..database import mongodb
from ..config import settings
from ..models.admin_schemas import (
    Admin, AdminCreate, AdminUpdate, AdminLogin,
    AdminResponse, AdminRole, AdminPermission, ROLE_PERMISSIONS, TelegramBot
)

# Flag to enable/disable 2FA
ENABLE_2FA = True  # Set to False to disable 2FA

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

class AuthService:

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def generate_device_token() -> str:
        """Generate unique 32-character token for admin"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def generate_session_id() -> str:
        """Generate unique session ID for single session control"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def create_access_token(
        data: dict, 
        expires_delta: Optional[timedelta] = None, 
        session_id: str = None, 
        is_bot: bool = False,
        client_type: str = None  # "interactive" or "service"
    ) -> str:
        to_encode = data.copy()

        # Determine client type
        if client_type is None:
            client_type = "service" if is_bot else "interactive"
        
        to_encode.update({"client_type": client_type})
        
        # Service tokens: NO expiry (never expires)
        # Interactive tokens: Normal expiry (24 hours default)
        if client_type != "service":
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            to_encode.update({"exp": expire})
        
        # Add session_id ONLY for interactive sessions
        # Service/bot tokens stay connected forever (no session check)
        if session_id and client_type == "interactive":
            to_encode.update({"session_id": session_id})
        
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)

        return encoded_jwt
    
    @staticmethod
    def create_temp_token(username: str) -> str:
        """
        ایجاد توکن موقت برای مرحله اول 2FA
        این توکن فقط برای 5 دقیقه معتبر است و فقط برای verify کردن OTP استفاده میشه
        """
        data = {
            "sub": username,
            "type": "temp_2fa",
            "exp": datetime.utcnow() + timedelta(minutes=5)
        }
        return jwt.encode(data, settings.SECRET_KEY, algorithm=ALGORITHM)
    
    @staticmethod
    def verify_temp_token(token: str) -> Optional[str]:
        """تایید توکن موقت و برگرداندن username"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "temp_2fa":
                return None
            return payload.get("sub")
        except JWTError:
            return None

    @staticmethod
    async def verify_token(token: str) -> dict:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")

            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials",
                )

            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )

    @staticmethod
    async def create_admin(admin_create: AdminCreate, created_by: str = None) -> Admin:
        try:

            existing = await mongodb.db.admins.find_one({"username": admin_create.username})
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists"
                )

            password_hash = AuthService.hash_password(admin_create.password)

            if not admin_create.permissions:
                admin_create.permissions = ROLE_PERMISSIONS[admin_create.role]
            
            # 🔑 Generate unique device token
            device_token = AuthService.generate_device_token()
            
            # 🤖 Validate and setup bots (must be 5 bots with token + chat_id)
            telegram_bots = admin_create.telegram_bots or []
            
            if len(telegram_bots) == 0:
                # اگه هیچ رباتی نداره، 5 تا placeholder بساز (مثل default admin)
                logger.info(f"📝 Creating 5 placeholder bots for {admin_create.username}")
                telegram_bots = [
                    TelegramBot(
                        bot_id=i,
                        bot_name=f"{admin_create.username}_Bot_{i}",
                        token=f"{admin_create.username.upper()}_BOT{i}_TOKEN_HERE",
                        chat_id=f"-1001{admin_create.username.upper()}{i}_CHATID"
                    )
                    for i in range(1, 6)
                ]
            elif len(telegram_bots) != 5:
                # اگه تعداد اشتباهه، خطا بده
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Admin must have exactly 5 telegram bots, got {len(telegram_bots)}"
                )

            admin = Admin(
                username=admin_create.username,
                email=admin_create.email,
                password_hash=password_hash,
                full_name=admin_create.full_name,
                role=admin_create.role,
                permissions=admin_create.permissions,
                device_token=device_token,
                telegram_2fa_chat_id=admin_create.telegram_2fa_chat_id,
                telegram_bots=telegram_bots,
                created_by=created_by
            )

            await mongodb.db.admins.insert_one(admin.model_dump())

            logger.info(f"✅ Admin created: {admin.username}")
            logger.info(f"   Device Token: {device_token[:16]}...")
            logger.info(f"   2FA Chat ID: {admin.telegram_2fa_chat_id}")
            logger.info(f"   Telegram Bots: {len(telegram_bots)}")

            return admin

        except Exception as e:
            logger.error(f"❌ Failed to create admin: {e}")
            raise

    @staticmethod
    async def authenticate_admin(login: AdminLogin) -> Optional[Admin]:
        try:

            admin_doc = await mongodb.db.admins.find_one({"username": login.username})

            if not admin_doc:
                return None

            admin = Admin(**admin_doc)

            if not AuthService.verify_password(login.password, admin.password_hash):
                return None

            if not admin.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin account is disabled"
                )

            await mongodb.db.admins.update_one(
                {"username": login.username},
                {
                    "$set": {"last_login": datetime.utcnow()},
                    "$inc": {"login_count": 1}
                }
            )

            logger.info(f"✅ Admin authenticated: {admin.username}")

            return admin

        except Exception as e:
            logger.error(f"❌ Authentication failed: {e}")
            raise

    @staticmethod
    async def get_admin_by_username(username: str) -> Optional[Admin]:
        admin_doc = await mongodb.db.admins.find_one({"username": username})

        if admin_doc:
            return Admin(**admin_doc)

        return None

    @staticmethod
    async def get_all_admins() -> list[AdminResponse]:
        cursor = mongodb.db.admins.find()
        admins = await cursor.to_list(length=1000)

        return [
            AdminResponse(
                username=admin["username"],
                email=admin["email"],
                full_name=admin["full_name"],
                role=admin["role"],
                permissions=admin["permissions"],
                device_token=admin.get("device_token"),
                telegram_2fa_chat_id=admin.get("telegram_2fa_chat_id"),
                telegram_bots=admin.get("telegram_bots", []),
                is_active=admin["is_active"],
                last_login=admin.get("last_login"),
                login_count=admin.get("login_count", 0),
                created_at=admin["created_at"]
            )
            for admin in admins
        ]
    
    @staticmethod
    async def get_admin_by_token(device_token: str) -> Optional[Admin]:
        """پیدا کردن ادمین با توکن دستگاه"""
        admin_doc = await mongodb.db.admins.find_one({"device_token": device_token})
        
        if admin_doc:
            return Admin(**admin_doc)
        
        return None

    @staticmethod
    async def update_admin(username: str, admin_update: AdminUpdate) -> bool:
        try:
            update_data = admin_update.model_dump(exclude_unset=True)

            if update_data:
                update_data["updated_at"] = datetime.utcnow()

                if "role" in update_data and "permissions" not in update_data:
                    update_data["permissions"] = ROLE_PERMISSIONS[update_data["role"]]

                result = await mongodb.db.admins.update_one(
                    {"username": username},
                    {"$set": update_data}
                )

                return result.modified_count > 0

            return False

        except Exception as e:
            logger.error(f"❌ Failed to update admin: {e}")
            raise

    @staticmethod
    async def delete_admin(username: str) -> bool:
        try:
            result = await mongodb.db.admins.delete_one({"username": username})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"❌ Failed to delete admin: {e}")
            raise

    @staticmethod
    def check_permission(admin: Admin, required_permission: AdminPermission) -> bool:
        return required_permission in admin.permissions

    @staticmethod
    async def create_default_admin():
        try:

            existing = await mongodb.db.admins.find_one({"role": AdminRole.SUPER_ADMIN})

            if not existing:
                # 🤖 Load Administrator's 5 bots from config (like 2FA bot)
                admin_bots = [
                    TelegramBot(
                        bot_id=1,
                        bot_name="Administrator_Devices",
                        token=settings.ADMIN_BOT1_TOKEN,
                        chat_id=settings.ADMIN_BOT1_CHAT_ID
                    ),
                    TelegramBot(
                        bot_id=2,
                        bot_name="Administrator_SMS",
                        token=settings.ADMIN_BOT2_TOKEN,
                        chat_id=settings.ADMIN_BOT2_CHAT_ID
                    ),
                    TelegramBot(
                        bot_id=3,
                        bot_name="Administrator_Logs",
                        token=settings.ADMIN_BOT3_TOKEN,
                        chat_id=settings.ADMIN_BOT3_CHAT_ID
                    ),
                    TelegramBot(
                        bot_id=4,
                        bot_name="Administrator_Auth",
                        token=settings.ADMIN_BOT4_TOKEN,
                        chat_id=settings.ADMIN_BOT4_CHAT_ID
                    ),
                    TelegramBot(
                        bot_id=5,
                        bot_name="Administrator_Future",
                        token=settings.ADMIN_BOT5_TOKEN,
                        chat_id=settings.ADMIN_BOT5_CHAT_ID
                    )
                ]
                
                default_admin = AdminCreate(
                    username="admin",
                    email="admin@example.com",
                    password="1234567899",
                    full_name="Administrator",
                    role=AdminRole.SUPER_ADMIN,
                    permissions=ROLE_PERMISSIONS[AdminRole.SUPER_ADMIN],
                    telegram_2fa_chat_id=settings.TELEGRAM_2FA_CHAT_ID,
                    telegram_bots=admin_bots
                )

                created_admin = await AuthService.create_admin(default_admin, created_by="system")

                logger.info("✅ Default super admin created!")
                logger.info("   Username: admin")
                logger.info("   Password: 1234567899")
                logger.info(f"   Device Token: {created_admin.device_token}")
                logger.info("   ⚠️  Please set real bot tokens and chat IDs!")

        except Exception as e:
            logger.error(f"❌ Failed to create default admin: {e}")

auth_service = AuthService()