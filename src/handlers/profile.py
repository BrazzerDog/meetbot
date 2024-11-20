from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from ..models.models import User, Gender, Photo
from ..services.user_service import UserService
from ..keyboards.keyboards import get_profile_settings_keyboard, get_main_keyboard
from ..states.states import ProfileStates
from geopy.geocoders import Nominatim
from sqlalchemy import delete
from typing import Optional
import logging
from aiogram.exceptions import TelegramBadRequest

router = Router()
logger = logging.getLogger(__name__)

def format_profile_text(user: User) -> str:
    """Форматирование текста профиля"""
    def format_gender(gender: Gender) -> str:
        return "Мужской" if gender == Gender.MALE else "Женский"

    profile_text = [
        f"👤 {user.name}, {user.age}",
        f"👥 Пол: {format_gender(user.gender)}",
        f"📍 {user.city}" if user.city else "",
        f"📝 {user.bio}" if user.bio else "",
        f"{'😴 Спящий' if not user.is_visible else '👀 Активный'} профиль",
    ]

    return "\n".join(line for line in profile_text if line)

async def show_profile(message: Message, user_service: UserService):
    """Показать профиль пользователя"""
    try:
        user = await user_service.get_user_by_tg_id(message.from_user.id)
        if not user:
            await message.answer("Пользователь не найден")
            return

        profile_text = format_profile_text(user)
        
        if user.photos:
            await message.answer_photo(
                photo=user.photos[0].file_id,
                caption=profile_text,
                reply_markup=get_profile_settings_keyboard(user.is_visible)
            )
        else:
            await message.answer(
                profile_text,
                reply_markup=get_profile_settings_keyboard(user.is_visible)
            )
    except Exception as e:
        logger.error(f"Ошибка при отображении профиля: {str(e)}")
        await message.answer("❌ Произошла ошибка при отображении профиля. Попробуйте позже.")

@router.message(Command("profile"))
@router.message(F.text == "👤 Мой профиль")
async def cmd_profile(message: Message):
    user_service = UserService()
    await show_profile(message, user_service)

@router.callback_query(lambda c: c.data == "edit_photo")
async def edit_photo(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("📸 Отправьте новое фото для анкеты:")
    await state.set_state(ProfileStates.waiting_new_photo)
    await callback.answer()

@router.callback_query(lambda c: c.data == "edit_name")
async def edit_name(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("📝 Введите новое имя:")
    await state.set_state(ProfileStates.waiting_new_name)
    await callback.answer()

@router.callback_query(lambda c: c.data == "edit_age")
async def edit_age(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🔢 Введите новый возраст (от 18 до 100):")
    await state.set_state(ProfileStates.waiting_new_age)
    await callback.answer()

@router.callback_query(lambda c: c.data == "edit_bio")
async def edit_bio(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("📋 Введите новое описание:")
    await state.set_state(ProfileStates.waiting_new_bio)
    await callback.answer()

@router.callback_query(lambda c: c.data == "edit_city")
async def edit_city(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        "🌆 Введите название вашего города:\n"
        "Например: Москва, Санкт-Петербург, Казань"
    )
    await state.set_state(ProfileStates.waiting_new_city)
    await callback.answer()

@router.callback_query(lambda c: c.data == "toggle_visibility_sleep")
async def handle_sleep(callback: CallbackQuery):
    await callback.message.answer(
        "💫 Статус профиля изменён!\n"
        "🌙 Теперь ты отдыхаешь, но всё ещё можешь смотреть анкеты других"
    )
    # Обновляем клавиатуру на "Проснуться"
    new_keyboard = get_profile_settings_keyboard(is_visible=False)
    await callback.message.edit_reply_markup(reply_markup=new_keyboard)
    await callback.answer()

@router.callback_query(lambda c: c.data == "toggle_visibility_wake")
async def handle_wake(callback: CallbackQuery):
    await callback.message.answer(
        "🌟 С возвращением в активный поиск! ✨\n"
        "💝 Пусть этот день принесёт тебе новые интересные знакомства! 🥰"
    )
    # Обновляем клавиатуру на "Спать"
    new_keyboard = get_profile_settings_keyboard(is_visible=True)
    await callback.message.edit_reply_markup(reply_markup=new_keyboard)
    await callback.answer()

@router.message(ProfileStates.waiting_new_photo, F.photo)
async def process_new_photo(message: Message, state: FSMContext):
    try:
        user_service = UserService()
        user = await user_service.get_user_by_tg_id(message.from_user.id)
        if not user:
            await message.answer("Пользователь не найден")
            await state.clear()
            return

        photo = message.photo[-1]
        success = await user_service.update_photo(user.id, photo.file_id)
        
        if success:
            await message.answer("✅ Фото успешно обновлено!")
            await show_profile(message, user_service)
        else:
            raise Exception("Не удалось обновить фото")
            
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении фото: {str(e)}")
        await message.answer("❌ Произошла ошибка при обновлении фото. Попробуйте позже.")
        await state.clear()

@router.message(ProfileStates.waiting_new_name)
async def process_new_name(message: Message, state: FSMContext):
    try:
        name = message.text.strip()
        if len(name) < 2 or len(name) > 50:
            await message.answer("❌ Имя должно быть от 2 до 50 символов. Попробуйте еще раз:")
            return

        user_service = UserService()
        user = await user_service.get_user_by_tg_id(message.from_user.id)
        if not user:
            await message.answer("Пользователь не найден")
            await state.clear()
            return

        updated_user = await user_service.update_user(user.id, {"name": name})
        if updated_user:
            await message.answer("✅ Имя успешно обновлено!")
            await show_profile(message, user_service)
        else:
            raise Exception("Не удалось обновить имя")
            
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении имени: {str(e)}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")
        await state.clear()

@router.message(ProfileStates.waiting_new_age)
async def process_new_age(message: Message, state: FSMContext):
    try:
        age = int(message.text)
        if age < 18 or age > 100:
            await message.answer("❌ Возраст должен быть от 18 до 100 лет. Попробуйте еще раз:")
            return

        user_service = UserService()
        user = await user_service.get_user_by_tg_id(message.from_user.id)
        if not user:
            await message.answer("Пользователь не найден")
            await state.clear()
            return

        updated_user = await user_service.update_user(user.id, {"age": age})
        if updated_user:
            await message.answer("✅ Возраст успешно обновлен!")
            await show_profile(message, user_service)
        else:
            raise Exception("Не удалось обновить возраст")
            
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректный возраст числом:")
    except Exception as e:
        logger.error(f"Ошибка при обновлении возраста: {str(e)}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")
        await state.clear()

@router.message(ProfileStates.waiting_new_bio)
async def process_new_bio(message: Message, state: FSMContext):
    try:
        bio = message.text.strip()
        if len(bio) > 500:
            await message.answer("❌ Описание слишком длинное. Максимум 500 символов. Попробуйте еще раз:")
            return

        user_service = UserService()
        user = await user_service.get_user_by_tg_id(message.from_user.id)
        if not user:
            await message.answer("Пользователь не найден")
            await state.clear()
            return

        updated_user = await user_service.update_user(user.id, {"bio": bio})
        if updated_user:
            await message.answer("✅ Описание успешно обновлено!")
            await show_profile(message, user_service)
        else:
            raise Exception("Не удалось обновить описание")
            
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении описания: {str(e)}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")
        await state.clear()

@router.message(ProfileStates.waiting_new_city)
async def process_new_city(message: Message, state: FSMContext):
    try:
        city_name = message.text.strip()
        
        # Получаем координаты гоода
        search_query = f"{city_name}, Россия"
        geolocator = Nominatim(user_agent="meetbot", timeout=10)
        location = geolocator.geocode(search_query, language='ru')
        
        if location:
            user_service = UserService()
            user = await user_service.get_user_by_tg_id(message.from_user.id)
            if not user:
                await message.answer("Пользователь не найден")
                await state.clear()
                return

            updated_user = await user_service.update_user(user.id, {
                "city": city_name,
                "location_lat": location.latitude,
                "location_lon": location.longitude
            })
            
            if updated_user:
                await message.answer("✅ Город успешно обновлен!")
                await show_profile(message, user_service)
            else:
                raise Exception("Не удалось обновить город")
        else:
            await message.answer(
                "❌ Город не найден. Проверьте название и попробуйте еще раз.\n"
                "Например: Москва, Санкт-Петербург, Казань"
            )
            
        await state.clear()
            
    except Exception as e:
        logger.error(f"Ошибка при обновлении города: {str(e)}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")
        await state.clear()
