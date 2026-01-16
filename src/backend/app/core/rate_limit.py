"""
Rate Limiting Middleware for FastAPI using Redis
"""
import logging
import time
from typing import Optional

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.database.redis import get_redis

logger = logging.getLogger(__name__)

# Default rate limits
DEFAULT_RATE_LIMIT = 100  # requests per window
DEFAULT_WINDOW = 60  # seconds


class RateLimitConfig:
    """Rate limit configuration"""
    def __init__(
        self,
        requests: int = DEFAULT_RATE_LIMIT,
        window: int = DEFAULT_WINDOW,
        identifier: Optional[str] = None
    ):
        self.requests = requests
        self.window = window
        self.identifier = identifier  # "ip", "user", or "api_key"


def get_client_identifier(request: Request, config: RateLimitConfig) -> str:
    """
    Get client identifier for rate limiting.
    
    Options:
    - IP address (default)
    - User ID (if authenticated)
    - API key (if provided)
    
    Args:
        request: FastAPI Request object
        config: Rate limit configuration
        
    Returns:
        Client identifier string
    """
    identifier = config.identifier or "ip"
    
    if identifier == "user" and hasattr(request.state, "user"):
        user_id = getattr(request.state.user, "id", None)
        if user_id:
            return f"user:{user_id}"
    
    if identifier == "api_key":
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key}"
    
    # Default: IP address
    if request.client:
        # Use X-Forwarded-For if behind proxy/ALB
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take first IP in chain (original client)
            ip = forwarded_for.split(",")[0].strip()
        else:
            ip = request.client.host
        return f"ip:{ip}"
    
    return "ip:unknown"


async def check_rate_limit(
    identifier: str,
    requests: int = DEFAULT_RATE_LIMIT,
    window: int = DEFAULT_WINDOW
) -> tuple[bool, dict]:
    """
    Check if request is within rate limit using sliding window log algorithm.
    
    Args:
        identifier: Client identifier
        requests: Maximum requests per window
        window: Time window in seconds
        
    Returns:
        Tuple of (allowed: bool, info: dict)
    """
    try:
        redis_client = await get_redis()
        key = f"rate_limit:{identifier}"
        now = int(time.time())
        
        # Remove old entries outside window
        cutoff = now - window
        await redis_client.zremrangebyscore(key, 0, cutoff)
        
        # Count current requests in window
        current_count = await redis_client.zcard(key)
        
        if current_count >= requests:
            # Rate limit exceeded
            oldest_request = await redis_client.zrange(key, 0, 0, withscores=True)
            if oldest_request:
                oldest_time = int(oldest_request[0][1])
                reset_time = oldest_time + window
                retry_after = reset_time - now
            else:
                retry_after = window
            
            return False, {
                "limit": requests,
                "remaining": 0,
                "reset": now + retry_after,
                "retry_after": retry_after
            }
        
        # Add current request
        await redis_client.zadd(key, {str(now): now})
        await redis_client.expire(key, window)
        
        return True, {
            "limit": requests,
            "remaining": requests - current_count - 1,
            "reset": now + window
        }
    except Exception as e:
        logger.warning(f"Rate limit check failed: {e}, allowing request")
        # Fail open - allow request if Redis is unavailable
        return True, {
            "limit": requests,
            "remaining": requests,
            "reset": int(time.time()) + window
        }


async def rate_limit_middleware(request: Request, call_next) -> Response:
    """
    Rate limiting middleware using Redis sliding window.
    
    Features:
    - IP-based rate limiting (default)
    - User-based rate limiting (if authenticated)
    - API key-based rate limiting
    - Configurable limits per endpoint
    - Graceful degradation if Redis unavailable
    
    Args:
        request: FastAPI Request object
        call_next: Next middleware/endpoint
        
    Returns:
        Response with rate limit headers
    """
    # Skip rate limiting for certain paths
    skip_paths = ["/", "/health", "/docs", "/openapi.json", "/scalar", "/redoc"]
    if any(request.url.path.startswith(path) for path in skip_paths):
        return await call_next(request)
    
    # Configure rate limits per endpoint
    path = request.url.path
    
    # Stricter limits for authentication endpoints
    if "/seller/token" in path or "/partner/token" in path:
        config = RateLimitConfig(requests=10, window=60, identifier="ip")  # 10 req/min
    # Stricter limits for signup endpoints
    elif "/seller/signup" in path or "/partner/signup" in path:
        config = RateLimitConfig(requests=5, window=300, identifier="ip")  # 5 req/5min
    # Default limits for other endpoints
    else:
        config = RateLimitConfig(requests=100, window=60, identifier="ip")  # 100 req/min
    
    # Get client identifier
    identifier = get_client_identifier(request, config)
    
    # Check rate limit
    allowed, limit_info = await check_rate_limit(
        identifier,
        config.requests,
        config.window
    )
    
    if not allowed:
        logger.warning(f"Rate limit exceeded for {identifier} on {path}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Limit: {limit_info['limit']} per {config.window}s",
                "retry_after": limit_info["retry_after"]
            },
            headers={
                "X-RateLimit-Limit": str(limit_info["limit"]),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(limit_info["reset"]),
                "Retry-After": str(limit_info["retry_after"])
            }
        )
    
    # Process request
    response = await call_next(request)
    
    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = str(limit_info["limit"])
    response.headers["X-RateLimit-Remaining"] = str(limit_info["remaining"])
    response.headers["X-RateLimit-Reset"] = str(limit_info["reset"])
    
    return response
