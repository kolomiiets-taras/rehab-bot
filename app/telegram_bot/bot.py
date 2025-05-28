from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import app_config

bot = Bot(token=app_config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
