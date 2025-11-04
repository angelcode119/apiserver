from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from datetime import datetime

from ..services.auth_service import auth_service
from ..models.admin_schemas import Admin, AdminPermission
from ..database import mongodb

security = HTTPBearer()

async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Admin:
    token = credentials.credentials

    payload = await auth_service.verify_token(token)
    username = payload.get("sub")
    token_session_id = payload.get("session_id")
    client_type = payload.get("client_type", "interactive")

    admin = await auth_service.get_admin_by_username(username)

    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin not found"
        )

    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is disabled"
        )
    
    if admin.expires_at:
        now = datetime.utcnow()
        if now > admin.expires_at:

            await mongodb.db.admins.update_one(
                {"username": username},
                {"$set": {"is_active": False}}
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account expired on {admin.expires_at.strftime('%Y-%m-%d')}. Please contact administrator."
            )
    
    if client_type == "service":

        return admin
    
    
    admin_session_id = getattr(admin, 'current_session_id', None)

    if admin_session_id is None:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No active session. Please login again."
        )
    
    if not token_session_id:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format. Please login again."
        )
    
    if token_session_id != admin_session_id:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Another login detected from different location."
        )

    return admin

async def get_optional_admin(
    request: Request
) -> Optional[Admin]:
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None

        token = auth_header.split(" ")[1]
        payload = await auth_service.verify_token(token)
        username = payload.get("sub")

        admin = await auth_service.get_admin_by_username(username)
        return admin if admin and admin.is_active else None

    except:
        return None

def require_permission(required_permission: AdminPermission):
    async def permission_checker(
        current_admin: Admin = Depends(get_current_admin)
    ) -> Admin:
        if not auth_service.check_permission(current_admin, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {required_permission.value} required"
            )
        return current_admin

    return permission_checker

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"

def get_user_agent(request: Request) -> str:
    return request.headers.get("User-Agent", "unknown")
