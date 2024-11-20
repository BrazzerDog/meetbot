from aiogram import Router
from aiogram.types import ErrorEvent
from aiogram.exceptions import TelegramAPIError
import logging

logger = logging.getLogger(__name__)
error_router = Router()

@error_router.errors()
async def handle_errors(error: ErrorEvent):
    if isinstance(error.exception, TelegramAPIError):
        logger.error(f"Telegram API Error: {error.exception}")
        try:
            await error.update.message.answer(
                "Произошла ошибка при обработке запроса. Попробуйте позже."
            )
        except:
            pass
    else:
        logger.exception(f"Unexpected error: {error.exception}")
        try:
            await error.update.message.answer(
                "Произошла непредвиденная ошибка. Мы уже работаем над её устранением."
            )
        except:
            pass 