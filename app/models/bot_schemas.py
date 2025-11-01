"""
Pydantic schemas for Telegram Bot authentication
"""
from pydantic import BaseModel
from typing import Optional

class BotOTPRequest(BaseModel):
    """Request OTP for bot authentication"""
    username: str
    bot_identifier: str  # Unique identifier for the bot

class BotOTPVerify(BaseModel):
    """Verify OTP and get service token"""
    username: str
    otp_code: str
    bot_identifier: str

class BotOTPResponse(BaseModel):
    """Response after OTP request"""
    success: bool
    message: str
    expires_in: int = 300  # OTP valid for 5 minutes

class BotTokenResponse(BaseModel):
    """Response with service token"""
    success: bool
    message: str
    service_token: str
    token_type: str = "bearer"
    admin_info: dict

class BotStatusResponse(BaseModel):
    """Response for admin status check"""
    active: bool
    admin_username: str
    message: Optional[str] = None
