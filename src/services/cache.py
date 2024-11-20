import redis
from typing import Optional, Any
import json
from config import REDIS_URL

class RedisCache:
    def __init__(self):
        self.redis = redis.from_url(REDIS_URL)
        self.default_ttl = 3600

    async def set(self, key: str, value: Any, ttl: int = None):
        if ttl is None:
            ttl = self.default_ttl
        serialized = json.dumps(value)
        await self.redis.set(key, serialized, ex=ttl)

    async def get(self, key: str) -> Optional[Any]:
        value = await self.redis.get(key)
        return json.loads(value) if value else None

    async def delete(self, key: str):
        await self.redis.delete(key)

    async def set_user_candidates(self, user_id: int, candidates: list, ttl: int = 300):
        """Кэширование списка кандидатов для пользователя"""
        key = f"candidates:{user_id}"
        await self.set(key, candidates, ttl)

    async def get_user_candidates(self, user_id: int) -> Optional[list]:
        """Получение списка кандидатов из кэша"""
        key = f"candidates:{user_id}"
        return await self.get(key) 