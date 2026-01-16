from app.database.redis import get_cache, set_cache, delete_cache  # type: ignore
from typing import Optional
import json

class CacheService:
    @staticmethod
    async def cache_user_data(user_id: int, user_data: dict, expire: int = 1800):
        """Cachear datos de usuario"""
        key = f"user:{user_id}:data"
        await set_cache(key, json.dumps(user_data), expire)
    
    @staticmethod
    async def get_user_data(user_id: int) -> Optional[dict]:
        """Obtener datos de usuario"""
        key = f"user:{user_id}:data"
        data = await get_cache(key)
        if data:
            return json.loads(data)
        return None
    
    @staticmethod
    async def invalidate_user_cache(user_id: int):
        """Eliminar cache de usuario"""
        key = f"user:{user_id}:data"
        await delete_cache(key)
