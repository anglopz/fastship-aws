"""
Redis client and token blacklist management
"""
from uuid import UUID

from redis.asyncio import Redis

from app.config import db_settings


# Token blacklist Redis client (separate from cache) - lazy initialization
_token_blacklist = None

# Cache Redis client (for backward compatibility)
_cache_client = None


async def get_redis():
    """Get Redis client for cache (backward compatibility)"""
    global _cache_client
    if _cache_client is None:
        from redis.asyncio import Redis as AsyncRedis
        from redis.asyncio.connection import ConnectionPool
        
        # Get connection params (supports both REDIS_URL and individual settings)
        params = db_settings.get_redis_connection_params()
        
        # Use URL if available, otherwise use host/port
        if "url" in params:
            # Parse URL and create connection pool
            pool = ConnectionPool.from_url(
                params["url"],
                db=params.get("db", 1),
                decode_responses=True,
            )
            _cache_client = AsyncRedis(connection_pool=pool)
        else:
            _cache_client = AsyncRedis(
                host=params["host"],
                port=params["port"],
                db=params.get("db", 1),
                decode_responses=True,
            )
        try:
            await _cache_client.ping()
            print("✅ Connected to Redis (cache)")
        except Exception as e:
            print(f"❌ Error connecting to Redis: {e}")
            raise
    return _cache_client


async def get_token_blacklist() -> Redis:
    """Get Redis client for token blacklist (lazy initialization)"""
    global _token_blacklist
    if _token_blacklist is None:
        from redis.asyncio.connection import ConnectionPool
        
        # Get connection params (supports both REDIS_URL and individual settings)
        params = db_settings.get_redis_connection_params()
        
        # Use URL if available, otherwise use host/port
        if "url" in params:
            # Parse URL and create connection pool (use db=0 for blacklist)
            pool = ConnectionPool.from_url(
                params["url"],
                db=0,  # Token blacklist uses db=0
                decode_responses=True,
            )
            _token_blacklist = Redis(connection_pool=pool)
        else:
            _token_blacklist = Redis(
                host=params["host"],
                port=params["port"],
                db=0,  # Token blacklist uses db=0
                decode_responses=True,
            )
        try:
            await _token_blacklist.ping()
        except Exception as e:
            # In test environment, Redis might not be available
            # Allow graceful degradation
            import os
            if os.getenv("TESTING") != "true":
                raise
    return _token_blacklist


async def close_redis():
    """Close Redis connections"""
    global _cache_client, _token_blacklist
    if _cache_client:
        # Handle both aclose() (redis 5.x) and close() (redis 4.x)
        if hasattr(_cache_client, 'aclose'):
            await _cache_client.aclose()
        elif hasattr(_cache_client, 'close'):
            await _cache_client.close()
        _cache_client = None
    if _token_blacklist:
        # Handle both aclose() (redis 5.x) and close() (redis 4.x)
        if hasattr(_token_blacklist, 'aclose'):
            await _token_blacklist.aclose()
        elif hasattr(_token_blacklist, 'close'):
            await _token_blacklist.close()
        _token_blacklist = None


# Cache functions (backward compatibility)
async def set_cache(key: str, value: str, expire_seconds: int = 3600):
    """Save to cache"""
    client = await get_redis()
    await client.setex(key, expire_seconds, value)


async def get_cache(key: str) -> str | None:
    """Get from cache"""
    client = await get_redis()
    return await client.get(key)


async def delete_cache(key: str):
    """Delete from cache"""
    client = await get_redis()
    await client.delete(key)


# Token blacklist functions (new API from Section 16)
async def add_jti_to_blacklist(jti: str) -> None:
    """Add a JTI to the blacklist to invalidate token (logout)"""
    try:
        blacklist = await get_token_blacklist()
        await blacklist.set(jti, "blacklisted")
    except Exception as e:
        # In test environment, allow graceful degradation
        import os
        if os.getenv("TESTING") == "true":
            # In tests, just log the error but don't fail
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Redis not available in test environment: {e}")
        else:
            raise


async def is_jti_blacklisted(jti: str) -> bool:
    """Check if a JTI is in the blacklist"""
    try:
        blacklist = await get_token_blacklist()
        return await blacklist.exists(jti) > 0
    except Exception as e:
        # In test environment, allow graceful degradation
        import os
        if os.getenv("TESTING") == "true":
            # In tests, if Redis is not available, assume token is not blacklisted
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Redis not available in test environment: {e}")
            return False
        else:
            raise


# Backward compatibility aliases (deprecated)
async def add_to_blacklist(jti: str, expires_in: int = 86400) -> None:
    """Deprecated: Use add_jti_to_blacklist instead"""
    await add_jti_to_blacklist(jti)


async def is_blacklisted(jti: str) -> bool:
    """Deprecated: Use is_jti_blacklisted instead"""
    return await is_jti_blacklisted(jti)


# Shipment verification code functions (Section 22)
async def add_shipment_verification_code(shipment_id: UUID, code: int) -> None:
    """
    Store verification code for a shipment.
    
    Codes expire after 24 hours (86400 seconds).
    Uses same Redis client as cache (db=1) but with different key prefix.
    
    Args:
        shipment_id: UUID of the shipment
        code: 6-digit verification code
    """
    try:
        client = await get_redis()  # Use existing cache client (db=1)
        key = f"verification_code:{shipment_id}"
        await client.setex(key, 86400, str(code))  # 24 hour expiration
    except Exception as e:
        # In test environment, allow graceful degradation
        import os
        if os.getenv("TESTING") == "true":
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Redis not available for verification code storage: {e}")
        else:
            raise


async def get_shipment_verification_code(shipment_id: UUID) -> str | None:
    """
    Get verification code for a shipment.
    
    Args:
        shipment_id: UUID of the shipment
        
    Returns:
        Verification code as string, or None if not found/expired
    """
    try:
        client = await get_redis()  # Use existing cache client (db=1)
        key = f"verification_code:{shipment_id}"
        code = await client.get(key)
        return code
    except Exception as e:
        # In test environment, allow graceful degradation
        import os
        if os.getenv("TESTING") == "true":
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Redis not available for verification code retrieval: {e}")
            return None
        else:
            raise
