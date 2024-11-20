import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from ..keyboards.keyboards import get_gender_keyboard, get_location_keyboard, get_profile_settings_keyboard, get_main_keyboard
from ..services.user_service import UserService
from ..models.models import Gender
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import asyncio
import json
import os

router = Router()
logger = logging.getLogger(__name__)

# Загружаем список городов
with open(os.path.join('src', 'database', 'russian-cities.json'), 'r', encoding='utf-8') as f:
    RUSSIAN_CITIES = json.load(f)
    # Создаем словарь для быстрого поиска
    CITIES_DICT = {city['name'].lower(): city for city in RUSSIAN_CITIES}

class RegistrationStates(StatesGroup):
    waiting_name = State()
    waiting_age = State()
    waiting_gender = State()
    waiting_preferred_gender = State()
    waiting_photo = State()
    waiting_bio = State()
    waiting_location = State()
    waiting_city = State()
    waiting_preferences = State()

def get_skip_location_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📍 Отправить локацию", request_location=True),
                KeyboardButton(text="✍️ Ввести город вручную")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard

# Создаем клавиатуры для выбора пола
gender_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="👨 Мужской"),
            KeyboardButton(text="👩 Женский")
        ]
    ],
    resize_keyboard=True
)

# Клавиатура для выбора предпочитаемого пола
preferred_gender_kb = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🔍 Ищу мужчину"),
            KeyboardButton(text="🔍 Ищу женщину")
        ],
        [
            KeyboardButton(text="🔍 Ищу всех")
        ]
    ],
    resize_keyboard=True
)

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    logger.info(f"Команда /start от пользователя {message.from_user.id}")
    
    user_service = UserService()
    user = await user_service.get_user_by_tg_id(message.from_user.id)
    
    if user:
        # Если пользователь уже зарегистрирован, показываем его профиль
        profile_text = [
            f"👤 {user.name}, {user.age}",
            f"📍 {user.city}" if user.city else "",
            f"📝 {user.bio}" if user.bio else "",
            f"👀 {'Видимый' if user.is_visible else 'Скрытый'} профиль",
            "",
            "🎯 Предпочтения:",
            f"👥 Пол: {user.preferred_gender.value if user.preferred_gender else 'Не указан'}",
            f"📏 Возраст: {user.min_age}-{user.max_age}",
            f"📍 Макс. расстояние: {user.max_distance}км"
        ]

        profile_text = "\n".join(line for line in profile_text if line)

        if user.photos:
            await message.answer_photo(
                photo=user.photos[0].file_id,
                caption=profile_text,
                reply_markup=get_profile_settings_keyboard()
            )
        else:
            await message.answer(
                profile_text,
                reply_markup=get_profile_settings_keyboard()
            )
        return

    # Если пользователь не зарегистрирован, начинаем регистрацию
    await state.clear()  # На всякий случай очищаем состояние
    await state.set_state(RegistrationStates.waiting_name)
    await message.answer(
        "💖 Привееет! Как же здорово, что ты к нам заглянул(а)! 🤗\n\n"
        "🌸 Мы создали это уютное местечко, чтобы помочь таким классным людям как ты "
        "найти свою любовь или просто приятных собеседников 💫\n\n"
        "❤️ Давай познакомимся поближе! Как тебя зовут? 🥰"
    )

@router.callback_query(lambda c: c.data == "restart_registration")
async def restart_registration(callback: CallbackQuery, state: FSMContext):
    user_service = UserService()
    # Удаляем старые данные пользователя
    await user_service.delete_user_by_tg_id(callback.from_user.id)
    
    # Начинаем регистрацию заново
    await state.set_state(RegistrationStates.waiting_name)
    await callback.message.answer("👋 Давайте создадим вашу анкету заново.\nКак вас зовут?")
    await callback.answer()

@router.callback_query(lambda c: c.data == "cancel_restart")
async def cancel_restart(callback: CallbackQuery):
    await callback.message.answer("Хорошо, ваша регистрация сохранена. Используйте /search для поиска или /profile для редактирования анкеты.")
    await callback.answer()

@router.message(RegistrationStates.waiting_name)
async def process_name(message: Message, state: FSMContext):
    logger.info(f"Обработка имени для пользователя {message.from_user.id}")
    if len(message.text) < 2:
        await message.answer("Имя должно содержать хотя бы 2 символа. Попробуйте еще раз:")
        return

    await state.update_data(name=message.text)
    await state.set_state(RegistrationStates.waiting_age)
    await message.answer("🎈 Прекрасное имя! А сколько тебе лет?\n"
        "💫 Это поможет найти людей твоего возраста")

@router.message(RegistrationStates.waiting_age)
async def process_age(message: Message, state: FSMContext):
    try:
        age = int(message.text)
        if age < 18 or age > 100:
            await message.answer("Возраст должен быть от 18 до 100 лет. Попробуйте еще раз:")
            return
            
        await state.update_data(age=age)
        await state.set_state(RegistrationStates.waiting_gender)
        await message.answer(
            "🌺 Укажи, пожалуйста, свой пол:\n"
            "💫 Это важно для правильного поиска",
            reply_markup=gender_kb
        )
        
    except ValueError:
        await message.answer("Пожалуйста, введите корректный возраст числом:")

@router.message(RegistrationStates.waiting_gender)
async def process_gender(message: Message, state: FSMContext):
    gender_text = message.text.lower()
    
    if "мужской" in gender_text:
        gender = Gender.MALE
    elif "женский" in gender_text:
        gender = Gender.FEMALE
    else:
        await message.answer("Пожалуйста, выберите ваш пол:", reply_markup=gender_kb)
        return
        
    await state.update_data(gender=gender)
    await state.set_state(RegistrationStates.waiting_preferred_gender)
    await message.answer(
        "🔍 Кого вы хотите найти?",
        reply_markup=preferred_gender_kb
    )

@router.message(RegistrationStates.waiting_preferred_gender)
async def process_preferred_gender(message: Message, state: FSMContext):
    gender_text = message.text.lower()
    
    if "ищу мужчину" in gender_text:
        preferred_gender = Gender.MALE
    elif "ищу женщину" in gender_text:
        preferred_gender = Gender.FEMALE
    elif "ищу всех" in gender_text:
        preferred_gender = None  # Если пользователь хочет искать всех
    else:
        await message.answer(
            "Пожалуйста, выберите кого вы хотите найти:",
            reply_markup=preferred_gender_kb
        )
        return
        
    await state.update_data(preferred_gender=preferred_gender)
    await state.set_state(RegistrationStates.waiting_photo)
    await message.answer(
        "✨ А теперь самый творческий момент! 🎨\n\n"
        "📸 Отправь нам свою самую классную фотографию!\n"
        "💫 Пусть все увидят твою искреннюю улыбку и особенную энергетику 🌟\n"
        "💝 П.С. Мы уверены, что у тебя получится отличный снимок! 🤗",
        reply_markup=ReplyKeyboardRemove()
    )

@router.message(RegistrationStates.waiting_photo)
async def process_photo(message: Message, state: FSMContext):
    if not message.photo:
        await message.answer("Пожалуйста, отправьте фотографию:")
        return

    photo = message.photo[-1]
    await state.update_data(photo=photo.file_id)
    
    await state.set_state(RegistrationStates.waiting_bio)
    await message.answer(
        "🌈 Расскажи немного о себе, мы с удовольствием познакомимся поближе! 💫\n\n"
        "💭 Чем увлекаешься? О чём мечтаешь?\n"
        "🎯 Кого хочешь встретить?\n"
        "✨ Поделись всем, что считаешь важным! 💝"
    )

@router.message(RegistrationStates.waiting_bio)
async def process_bio(message: Message, state: FSMContext):
    try:
        bio_text = message.text.strip()
        
        if len(bio_text) > 500:
            await message.answer("Описание слишком длинное. Максимум 500 символов. Попробуйте еще раз:")
            return

        # Сохраняем био в состояние
        await state.update_data(bio=bio_text)
        
        # Переходим к вводу города
        await state.set_state(RegistrationStates.waiting_city)
        await message.answer(
            "🏙️ В каком городе ты живёшь? 💫\n\n"
            "💝 Это поможет нам найти для тебя самые интересные знакомства поблизости!\n"
            "🌟 Например: Москва, Санкт-Петербург или Казань 🤗"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при обработке био: {str(e)}")
        await message.answer("Произошла ошибка. Попробуйте ввести описание еще раз:")

@router.message(RegistrationStates.waiting_city)
async def process_city(message: Message, state: FSMContext):
    try:
        city_name = message.text.strip()
        logger.info(f"Обработка города: {city_name}")
        
        # Получаем сохраненные данные пользователя
        user_data = await state.get_data()
        logger.info(f"Полученные данные из состояния: {user_data}")
        
        if not user_data:
            logger.error("Данные пользователя не найдены в состоянии")
            await message.answer(
                "❌ Произошла ошибка. Пожалуйста, начните регистрацию заново с помощью /start"
            )
            await state.clear()
            return

        # Пробуем получить координаты через геокодер
        try:
            search_query = f"{city_name}, Россия"
            geolocator = Nominatim(user_agent="meetbot", timeout=10)
            location = geolocator.geocode(search_query, language='ru')
            
            if location:
                lat, lon = location.latitude, location.longitude
                logger.info(f"Координаты получены через геокодер: {lat}, {lon}")
                
                # Обновляем данные пользователя
                user_data.update({
                    'tg_id': message.from_user.id,
                    'username': message.from_user.username,
                    'location_lat': lat,
                    'location_lon': lon,
                    'city': city_name,
                    'is_visible': True
                })
                
                # Создаем пользователя
                user_service = UserService()
                user = await user_service.create_user(user_data)
                
                if user:
                    await state.clear()
                    await message.answer(
                        f"✅ Регистрация успешно завершена!\n"
                        f"Ваш город: {city_name}",
                        reply_markup=get_main_keyboard()
                    )
                    logger.info(f"Пользователь {message.from_user.id} успешно зарегистрирован")
                else:
                    raise Exception("Не удалось создать пользователя")
                
            else:
                # Если геокодер не нашел город
                await message.answer(
                    "🏙 Город не найден. Проверьте название и попробуйте еще раз.\n"
                    "Например: Москва, Санкт-Петербург, Казань"
                )
                
        except Exception as e:
            logger.error(f"Ошибка при создании пользователя: {str(e)}")
            await message.answer(
                "❌ Произошла ошибка при регистрации.\n"
                "Пожалуйста, попробуйте еще раз или используйте /start для начала регистрации заново"
            )
            await state.clear()
            
    except Exception as e:
        logger.error(f"Критическая ошибка при обработке города: {str(e)}")
        await message.answer(
            "❌ Произошла ошибка.\n"
            "Пожалуйста, попробуйте еще раз или используйте /start для начала регистрации заново"
        )
        await state.clear()

# Добавляем команду отмены регистрации
@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is not None:
        await state.clear()
        await message.answer(
            "❌ Регистрация отменена.\n"
            "Используйте /start, когда захотите зарегистрироваться."
        )
