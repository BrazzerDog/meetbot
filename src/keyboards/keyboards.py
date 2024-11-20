from aiogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)

def get_gender_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора пола"""
    buttons = [
        [
            InlineKeyboardButton(text="Мужской 👨", callback_data="gender:male"),
            InlineKeyboardButton(text="Женский 👩", callback_data="gender:female")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_location_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для отправки геолокации"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📍 Отправить локацию", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard

def get_profile_actions_keyboard(profile_id: int) -> InlineKeyboardMarkup:
    """Клавиатура действий с анкетой"""
    buttons = [
        [
            InlineKeyboardButton(text="❤️ Нравится", callback_data=f"profile:like:{profile_id}"),
            InlineKeyboardButton(text="👎 Пропустить", callback_data=f"profile:dislike:{profile_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_profile_settings_keyboard(is_visible: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура настроек профиля"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📸 Изменить фото", callback_data="edit_photo"),
                InlineKeyboardButton(text="📝 Изменить имя", callback_data="edit_name")
            ],
            [
                InlineKeyboardButton(text="🔢 Изменить возраст", callback_data="edit_age"),
                InlineKeyboardButton(text="📋 Изменить био", callback_data="edit_bio")
            ],
            [
                InlineKeyboardButton(text="🌆 Изменить город", callback_data="edit_city")
            ],
            [
                InlineKeyboardButton(
                    text="🌅 Проснуться" if not is_visible else "💤 Спать",
                    callback_data="toggle_visibility_wake" if not is_visible else "toggle_visibility_sleep"
                )
            ]
        ]
    )

def get_preferences_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура настроек предпочтений"""
    buttons = [
        [
            InlineKeyboardButton(text="🎯 Пол", callback_data="preferences:gender"),
            InlineKeyboardButton(text="📏 Возраст", callback_data="preferences:age")
        ],
        [
            InlineKeyboardButton(text="📍 Расстояние", callback_data="preferences:distance"),
            InlineKeyboardButton(text="✅ Готово", callback_data="preferences:done")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура отмены действия"""
    buttons = [[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def remove_keyboard() -> ReplyKeyboardRemove:
    """Удаление клавиатуры"""
    return ReplyKeyboardRemove()

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Основная клавиатура для пользователя"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="👤 Мой профиль"),
                KeyboardButton(text="🚀 На встречу!")
            ]
        ],
        resize_keyboard=True,
        persistent=True
    ) 