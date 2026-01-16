"""
Response Caching Middleware for FastAPI using Redis
"""
import hashlib
import json
import logging
from typing import Optional, Callable, Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.database.redis import get_redis

logger = logging.getLogger(__name__)

# Default cache TTL (5 minutes)
DEFAULT_CACHE_TTL = 300


def generate_cache_key(request: Request) -> str:
    """
    Generate a cache key from request.
    
    Includes:
    - Method (GET only)
    - Path
    - Query parameters
    - User ID (if authenticated) for personalized responses
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Cache key string
    """
    # Only cache GET requests
    if request.method != "GET":
        return None
    
    # Get path and query params
    path = str(request.url.path)
    query_string = str(request.url.query)
    
    # Get user ID if authenticated (for personalized caching)
    user_id = None
    if hasattr(request.state, "user"):
        user_id = getattr(request.state.user, "id", None)
    
    # Build cache key
    key_parts = [request.method, path]
    if query_string:
        key_parts.append(query_string)
    if user_id:
        key_parts.append(f"user:{user_id}")
    
    # Hash to keep keys reasonable length
    key_string = ":".join(key_parts)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()
    
    return f"fastapi:cache:response:{key_hash}"


async def get_cached_response(cache_key: str) -> Optional[dict]:
    """
    Get cached response from Redis.
    
    Args:
        cache_key: Cache key
        
    Returns:
        Cached response dict or None
    """
    try:
        redis_client = await get_redis()
        cached_data = await redis_client.get(cache_key)
        
        if cached_data:
            return json.loads(cached_data)
    except Exception as e:
        logger.warning(f"Failed to get cached response: {e}")
    return None


async def set_cached_response(cache_key: str, response_data: dict, ttl: int = DEFAULT_CACHE_TTL) -> None:
    """
    Cache response in Redis.
    
    Args:
        cache_key: Cache key
        response_data: Response data to cache (body, status_code, headers)
        ttl: Time to live in seconds
    """
    try:
        redis_client = await get_redis()
        await redis_client.setex(
            cache_key,
            ttl,
            json.dumps(response_data)
        )
    except Exception as e:
        logger.warning(f"Failed to cache response: {e}")


async def cache_response_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware to cache GET responses in Redis.
    
    Features:
    - Only caches GET requests
    - Skips caching for authenticated endpoints that require user context
    - Configurable TTL per endpoint
    - Cache invalidation support
    
    Args:
        request: FastAPI Request object
        call_next: Next middleware/endpoint
        
    Returns:
        Response: Cached or fresh response
    """
    # Only cache GET requests
    if request.method != "GET":
        return await call_next(request)
    
    # Skip caching for certain paths (e.g., health checks, metrics)
    skip_paths = ["/", "/health", "/test-redis", "/metrics", "/docs", "/openapi.json", "/scalar", "/redoc"]
    if any(request.url.path.startswith(path) for path in skip_paths):
        return await call_next(request)
    
    # Generate cache key
    cache_key = generate_cache_key(request)
    if not cache_key:
        return await call_next(request)
    
    # Try to get cached response
    cached = await get_cached_response(cache_key)
    if cached:
        # Build response headers (exclude cache-specific headers)
        response_headers = {
            k: v for k, v in cached.get("headers", {}).items()
            if k.lower() not in ["x-cache", "x-cache-key", "content-length"]
        }
        response_headers["X-Cache"] = "HIT"
        response_headers["X-Cache-Key"] = cache_key
        
        # Return cached response
        response = JSONResponse(
            content=cached["body"],
            status_code=cached["status_code"],
            headers=response_headers
        )
        logger.debug(f"Cache HIT: {request.url.path}")
        return response
    
    # No cache hit - process request
    response: Response = await call_next(request)
    
    # Only cache successful JSON responses (2xx)
    if 200 <= response.status_code < 300 and isinstance(response, JSONResponse):
        try:
            # Get response body from JSONResponse
            response_body = response.body
            if isinstance(response_body, bytes):
                try:
                    response_body = json.loads(response_body.decode())
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Not valid JSON - don't cache
                    return response
            
            # Cache response
            cache_data = {
                "body": response_body,
                "status_code": response.status_code,
                "headers": {k: v for k, v in response.headers.items() 
                           if k.lower() not in ["content-length", "transfer-encoding"]}
            }
            
            # Determine TTL (can be customized per endpoint)
            ttl = DEFAULT_CACHE_TTL
            
            # Longer TTL for certain endpoints (e.g., public data)
            if "/api/v1/shipment/track" in request.url.path:
                ttl = 600  # 10 minutes for tracking pages
            
            await set_cached_response(cache_key, cache_data, ttl)
            
            # Add cache headers to response
            response.headers["X-Cache"] = "MISS"
            response.headers["X-Cache-Key"] = cache_key
            
            logger.debug(f"Cache MISS: {request.url.path} (cached for {ttl}s)")
        except Exception as e:
            logger.warning(f"Failed to cache response: {e}")
            # Return original response if caching fails
    
    return response


async def invalidate_cache_pattern(pattern: str) -> int:
    """
    Invalidate cache entries matching a pattern.
    
    Useful for cache invalidation when data changes (e.g., shipment updates).
    
    Args:
        pattern: Redis pattern (e.g., "fastapi:cache:response:*shipment*")
        
    Returns:
        Number of keys deleted
    """
    try:
        redis_client = await get_redis()
        keys = []
        async for key in redis_client.scan_iter(match=pattern):
            keys.append(key)
        
        if keys:
            deleted = await redis_client.delete(*keys)
            logger.info(f"Invalidated {deleted} cache entries matching pattern: {pattern}")
            return deleted
        return 0
    except Exception as e:
        logger.error(f"Failed to invalidate cache: {e}")
        return 0
