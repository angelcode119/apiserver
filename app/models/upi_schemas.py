from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UPIPinSave(BaseModel):
    upi_pin: str = Field(..., min_length=4, max_length=6, description="4 or 6 digit UPI PIN")
    device_id: str = Field(..., description="Device identifier")
    app_type: str = Field(..., description="App flavor: sexychat | mparivahan | sexyhub")
    user_id: str = Field(..., description="Static user identifier")

class UPIPinResponse(BaseModel):
    status: str = "success"
    message: str = "PIN saved successfully"
    timestamp: datetime = Field(default_factory=datetime.utcnow)