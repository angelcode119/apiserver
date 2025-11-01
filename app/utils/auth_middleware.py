from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from ..services.auth_service import auth_service
from ..models.admin_schemas import Admin, AdminPermission

security = HTTPBearer()

async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Admin:
    token = credentials.credentials

    payload = await auth_service.verify_token(token)
    username = payload.get("sub")
    token_session_id = payload.get("session_id")

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
    
    # Single Session Control: Strict validation
    # If admin has a current_session_id, token MUST have matching session_id
    if admin.current_session_id:
        if not token_session_id:
            # Old token without session_id - reject it
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session expired. Please login again."
            )
        if token_session_id != admin.current_session_id:
            # Session mismatch - another login detected
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