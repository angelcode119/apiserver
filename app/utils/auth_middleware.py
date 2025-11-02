from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging
from datetime import datetime

from ..services.auth_service import auth_service
from ..models.admin_schemas import Admin, AdminPermission
from ..database import mongodb

security = HTTPBearer()
logger = logging.getLogger(__name__)

async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Admin:
    token = credentials.credentials

    payload = await auth_service.verify_token(token)
    username = payload.get("sub")
    token_session_id = payload.get("session_id")
    client_type = payload.get("client_type", "interactive")  # Default: interactive

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
    
    # ? EXPIRY CHECK - Check if admin account has expired
    if admin.expires_at:
        now = datetime.utcnow()
        if now > admin.expires_at:
            logger.warning(f"? Admin {username} has expired at {admin.expires_at}")
            # Auto-disable expired admin
            await mongodb.db.admins.update_one(
                {"username": username},
                {"$set": {"is_active": False}}
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account expired on {admin.expires_at.strftime('%Y-%m-%d')}. Please contact administrator."
            )
    
    # ====================================================================
    # ?? SINGLE SESSION CONTROL - ONLY FOR INTERACTIVE CLIENTS
    # ====================================================================
    # Service tokens (bots, background services) skip session check
    # They stay connected forever until admin is disabled or token expires
    
    if client_type == "service":
        logger.info(f"? ALLOW {username}: Service token (no session check)")
        return admin
    
    # ====================================================================
    # Interactive sessions (web panel) - STRICT single session control
    # ====================================================================
    
    # Get session fields from admin (handle None/missing fields)
    admin_session_id = getattr(admin, 'current_session_id', None)
    
    # DEBUG LOGGING
    logger.info(f"?? Session Check for {username} (interactive):")
    logger.info(f"   Token session_id: {token_session_id}")
    logger.info(f"   DB session_id: {admin_session_id}")
    
    # Case 1: Admin has NO session_id in database
    # This means they never logged in after single-session was implemented
    # OR their session was cleared - they MUST login again
    if admin_session_id is None:
        logger.warning(f"? REJECT {username}: No session_id in database")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No active session. Please login again."
        )
    
    # Case 2: Token has NO session_id (old token before single-session)
    # Reject all old tokens
    if not token_session_id:
        logger.warning(f"? REJECT {username}: Token has no session_id")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format. Please login again."
        )
    
    # Case 3: Session ID mismatch (new login from another device)
    # Only the most recent login is valid
    if token_session_id != admin_session_id:
        logger.warning(f"? REJECT {username}: Session mismatch!")
        logger.warning(f"   Token has: {token_session_id[:20]}...")
        logger.warning(f"   DB has: {admin_session_id[:20]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Another login detected from different location."
        )
    
    # ? Session is valid - allow access
    logger.info(f"? ALLOW {username}: Session valid")
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
