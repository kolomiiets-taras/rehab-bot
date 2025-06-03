from os import getenv
from pathlib import Path
from typing import Final
from dotenv import load_dotenv
from fastapi.templating import Jinja2Templates


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    BOT_TOKEN: Final[str] = getenv('BOT_TOKEN')

    API_VERSION: Final[str] = getenv('API_VERSION', 'v1')

    ALGORITHM: Final[str] = getenv("ALGORITHM")
    SECRET_KEY: Final[str] = getenv("SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: Final[int] = int(getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
    REFRESH_TOKEN_EXPIRE_MINUTES: Final[int] = int(getenv("REFRESH_TOKEN_EXPIRE_MINUTES"))

    POSTGRES_USER: Final[str] = getenv('POSTGRES_USER', 'test')
    POSTGRES_PASSWORD: Final[str] = getenv('POSTGRES_PASSWORD', 'test')
    POSTGRES_HOST: Final[str] = getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT: Final[str] = getenv('POSTGRES_PORT', '5432')
    POSTGRES_DB: Final[str] = getenv('POSTGRES_DB', 'test_db')
    SQLALCHEMY_DATABASE_URL: Final[str] = f'postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'

    TEMPLATES = Jinja2Templates(directory=BASE_DIR / 'backend' / 'templates')

    MEDIA_PATH = BASE_DIR / 'backend' / 'static' / 'exercises_media'
    LOGS_PATH = BASE_DIR / 'logs'
    LOCALES_PATH = BASE_DIR / 'backend' / 'telegram_bot' / 'locales'
    STATIC_PATH = BASE_DIR / 'backend' / 'static'

    SUPPORTED_LANGUAGES = ['uk']
    DEFAULT_LANGUAGE = 'uk'

    SUPPORT_TAG: Final[str] = '@spinatop'

    def __init__(self):
        if not self.MEDIA_PATH.exists():
            self.MEDIA_PATH.mkdir(parents=True, exist_ok=True)
        if not self.LOGS_PATH.exists():
            self.LOGS_PATH.mkdir(parents=True, exist_ok=True)
        if not self.LOCALES_PATH.exists():
            self.LOCALES_PATH.mkdir(parents=True, exist_ok=True)


app_config = Config()
