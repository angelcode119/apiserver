"""
Rate Limiting Middleware
????? ???? ????? request ???? ??????? ?? abuse
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
from collections import defaultdict
from typing import Dict, Tuple
import asyncio
import logging

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate Limiting Middleware
    
    ??????????:
    - Per IP: ?????? 100 request ?? ?????
    - Per Endpoint: ??????????? ??? ???? endpoint ??? ?????
    """
    
    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # 60 seconds
        
        # ????? request history: {ip: [(timestamp1, endpoint1), ...]}
        self.request_history: Dict[str, list] = defaultdict(list)
        
        # ??????????? ??? ???? endpoint ??? ?????
        self.endpoint_limits = {
            "/auth/login": 10,  # 10 request per minute
            "/auth/verify-2fa": 10,
            "/register": 50,  # Device registration
            "/sms": 200,  # SMS sync
            "/contacts": 100,  # Contacts sync
            "/call-logs": 100,  # Call logs sync
        }
        
        # Whitelist IPs (no rate limiting)
        self.whitelist_ips = [
            "127.0.0.1",
            "localhost",
        ]
        
        # Background task ???? cleanup
        asyncio.create_task(self.cleanup_old_entries())
    
    def get_client_ip(self, request: Request) -> str:
        """?????? IP ??????"""
        # Check X-Forwarded-For header (behind proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct IP
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def get_endpoint_key(self, path: str) -> str:
        """
        ??????? endpoint key ?? path
        ?????: /api/devices/123/sms ? /sms
        """
        # Common patterns
        if "/sms" in path:
            return "/sms"
        elif "/contacts" in path:
            return "/contacts"
        elif "/call-logs" in path:
            return "/call-logs"
        elif "/auth/login" in path:
            return "/auth/login"
        elif "/auth/verify-2fa" in path:
            return "/auth/verify-2fa"
        elif path == "/register":
            return "/register"
        
        return path
    
    def is_rate_limited(self, ip: str, endpoint: str) -> Tuple[bool, int]:
        """
        ?? ???? ????? IP rate limited ??? ?? ??
        
        Returns:
            (is_limited, remaining_requests)
        """
        current_time = time.time()
        window_start = current_time - self.window_size
        
        # ??? ???? request ??? ?????
        self.request_history[ip] = [
            (ts, ep) for ts, ep in self.request_history[ip]
            if ts > window_start
        ]
        
        # ?????? ????? request ?? ?? window ????
        recent_requests = self.request_history[ip]
        total_requests = len(recent_requests)
        
        # ?? ???? ??????? ???
        if total_requests >= self.requests_per_minute:
            return True, 0
        
        # ?? ???? ??????? ??? endpoint
        endpoint_limit = self.endpoint_limits.get(endpoint)
        if endpoint_limit:
            endpoint_requests = sum(1 for _, ep in recent_requests if ep == endpoint)
            if endpoint_requests >= endpoint_limit:
                return True, 0
        
        # ?????? remaining requests
        remaining = self.requests_per_minute - total_requests
        return False, remaining
    
    def add_request(self, ip: str, endpoint: str):
        """????? ???? request ?? history"""
        current_time = time.time()
        self.request_history[ip].append((current_time, endpoint))
    
    async def dispatch(self, request: Request, call_next):
        """Process request ?? rate limiting"""
        
        # ?????? IP ??????
        client_ip = self.get_client_ip(request)
        
        # Whitelist check
        if client_ip in self.whitelist_ips:
            return await call_next(request)
        
        # ?????? endpoint
        endpoint = self.get_endpoint_key(request.url.path)
        
        # ?? ???? rate limit
        is_limited, remaining = self.is_rate_limited(client_ip, endpoint)
        
        if is_limited:
            logger.warning(f"??  Rate limit exceeded: {client_ip} ? {endpoint}")
            
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please try again later.",
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "retry_after": 60
                },
                headers={
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + self.window_size),
                    "Retry-After": "60"
                }
            )
        
        # ????? ???? request ?? history
        self.add_request(client_ip, endpoint)
        
        # ????? request
        response = await call_next(request)
        
        # ????? ???? rate limit headers ?? response
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining - 1)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + self.window_size)
        
        return response
    
    async def cleanup_old_entries(self):
        """Background task ???? ??? ???? entry ??? ?????"""
        while True:
            try:
                await asyncio.sleep(300)  # ?? 5 ?????
                
                current_time = time.time()
                window_start = current_time - self.window_size
                
                # ??? ???? IP ???? ?? request ??????
                ips_to_remove = []
                for ip, requests in self.request_history.items():
                    # ??? ???? request ??? ?????
                    self.request_history[ip] = [
                        (ts, ep) for ts, ep in requests
                        if ts > window_start
                    ]
                    
                    # ??? IP ???? request ?????? ???? ??
                    if not self.request_history[ip]:
                        ips_to_remove.append(ip)
                
                for ip in ips_to_remove:
                    del self.request_history[ip]
                
                if ips_to_remove:
                    logger.info(f"?? Cleaned up {len(ips_to_remove)} inactive IPs from rate limiter")
                
            except Exception as e:
                logger.error(f"? Error in rate limiter cleanup: {e}")


# ???????????????????????????????????????????????????????????????
# Configurable Rate Limiter for Production
# ???????????????????????????????????????????????????????????????

class ConfigurableRateLimiter:
    """
    Rate Limiter ?? ??????? ???? ?????
    """
    
    def __init__(
        self,
        default_rpm: int = 100,  # requests per minute
        auth_rpm: int = 10,
        register_rpm: int = 50,
        sync_rpm: int = 200,
    ):
        self.default_rpm = default_rpm
        self.auth_rpm = auth_rpm
        self.register_rpm = register_rpm
        self.sync_rpm = sync_rpm
    
    def get_middleware(self):
        """?????? middleware instance"""
        return RateLimitMiddleware(
            app=None,  # Will be set by FastAPI
            requests_per_minute=self.default_rpm
        )


# ???????????????????????????????????????????????????????????????
# Usage Example
# ???????????????????????????????????????????????????????????????

"""
# ?? main.py:

from app.middleware.rate_limit import RateLimitMiddleware

app = FastAPI()

# ????? ???? Rate Limiting Middleware
app.add_middleware(RateLimitMiddleware, requests_per_minute=100)

# ???? production ?? 25,000 users:
# app.add_middleware(RateLimitMiddleware, requests_per_minute=200)
"""
