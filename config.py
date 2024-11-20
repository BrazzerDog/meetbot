import os
from dotenv import load_dotenv

load_dotenv()

# Основные настройки
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///database.db")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost")

# Ограничения
RATE_LIMIT = 1  # секунд между сообщениями
MAX_PHOTOS = 3
MAX_DAILY_LIKES = 100
MAX_BIO_LENGTH = 500

# Возрастные ограничения
MIN_AGE = 18
MAX_AGE = 100

# Настройки поиска
DEFAULT_SEARCH_RADIUS = 50  # км
CANDIDATES_CACHE_TTL = 300  # 5 минут

# Проверка обязательных переменных
if not BOT_TOKEN:
    raise ValueError("Не указан BOT_TOKEN в .env файле")