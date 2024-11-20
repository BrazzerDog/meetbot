from aiogram import BaseMiddleware
from aiogram.types import Message
from cachetools import TTLCache
from datetime import datetime
from config import RATE_LIMIT

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self):
        self.cache = TTLCache(maxsize=10000, ttl=RATE_LIMIT)
        super().__init__()

    async def __call__(self, handler, event: Message, data: dict):
        user_id = event.from_user.id
        
        if user_id in self.cache:
            await event.answer("Пожалуйста, подождите перед следующим действием.")
            return
        
        self.cache[user_id] = datetime.now()
        return await handler(event, data) 