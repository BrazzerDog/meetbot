from datetime import datetime
from .cache import RedisCache
from typing import Optional

class SecurityService:
    def __init__(self):
        self.cache = RedisCache()
        
    async def check_rate_limit(self, user_id: int, action: str, limit: int, period: int) -> bool:
        key = f"rate_limit:{action}:{user_id}"
        count = await self.cache.get(key) or 0
        
        if count >= limit:
            return False
            
        await self.cache.set(key, count + 1, ttl=period)
        return True

    async def block_user(self, user_id: int, duration: int):
        key = f"blocked_user:{user_id}"
        await self.cache.set(key, True, ttl=duration)

    async def is_blocked(self, user_id: int) -> bool:
        key = f"blocked_user:{user_id}"
        return bool(await self.cache.get(key))
