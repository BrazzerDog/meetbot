import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from src.handlers.registration import router as registration_router
from src.handlers.matching import router as matching_router
from src.handlers.profile import router as profile_router
from src.middlewares.throttling import ThrottlingMiddleware
from src.database.core import init_db, close_db_connections
from config import BOT_TOKEN

async def main():
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Инициализация базы данных
    await init_db()
    
    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Подключаем middleware
    dp.message.middleware(ThrottlingMiddleware())
    
    # Регистрируем роутеры
    dp.include_router(registration_router)
    dp.include_router(matching_router)
    dp.include_router(profile_router)
    
    # Запуск бота
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await close_db_connections()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен") 