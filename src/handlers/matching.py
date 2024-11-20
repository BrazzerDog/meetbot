from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import Command
from ..services.matching import MatchingService
from ..services.user_service import UserService
from ..keyboards.keyboards import get_profile_actions_keyboard, get_main_keyboard
import logging

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("search"))
@router.message(F.text == "🚀 На встречу!")
async def cmd_search(message: Message):
    try:
        user_service = UserService()
        matching_service = MatchingService()

        # Получаем текущего пользователя
        user = await user_service.get_user_by_tg_id(message.from_user.id)
        
        if not user:
            await message.answer(
                "Сначала нужно зарегистрироваться! Используйте /start",
                reply_markup=ReplyKeyboardRemove()
            )
            return

        # Получаем следующего кандидата
        candidate = await matching_service.get_next_candidate(user.id)
        
        if not candidate:
            await message.answer(
                "✨ Пока нет новых анкет, но не грусти!\n"
                "🌟 Попробуй изменить параметры поиска или загляни к нам чуть позже\n"
                "💫 А пока можешь обновить свою анкету, чтобы привлечь больше внимания!",
                reply_markup=get_main_keyboard()
            )
            return

        # Формируем текст анкеты
        profile_text = format_profile_text(candidate)
        
        # Отправляем анкету
        if candidate.photos:
            await message.answer_photo(
                photo=candidate.photos[0].file_id,
                caption=profile_text,
                reply_markup=get_profile_actions_keyboard(candidate.id)
            )
        else:
            await message.answer(
                profile_text,
                reply_markup=get_profile_actions_keyboard(candidate.id)
            )

    except Exception as e:
        logger.error(f"Ошибка при поиске анкет: {str(e)}")
        await message.answer(
            "😔 Произошла ошибка при поиске анкет.\n"
            "Пожалуйста, попробуйте позже или обратитесь к администратору.",
            reply_markup=get_main_keyboard()
        )

@router.callback_query(F.data.startswith("profile:"))
async def process_profile_action(callback: CallbackQuery):
    action, profile_id = callback.data.split(':')[1:]
    matching_service = MatchingService()
    
    if action == "like":
        is_match = await matching_service.create_like(
            from_user_id=callback.from_user.id,
            to_user_id=int(profile_id)
        )
        
        if is_match:
            matched_user = await UserService().get_user(int(profile_id))
            match_text = (
                f"✨ Ура! У вас взаимная симпатия с {matched_user.name}! 💘\n\n"
                f"💌 Не стесняйся написать первым(-ой): @{matched_user.username}\n"
                f"🌟 Желаем приятного общения! 🤗"
            )
            await callback.message.answer(match_text)
    
    # Показываем следующую анкету
    await cmd_search(callback.message)
