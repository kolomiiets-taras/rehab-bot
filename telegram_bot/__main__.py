import asyncio
import logging
import sys

from aiogram import Dispatcher

from logger import get_bot_logger
logger = get_bot_logger()
from telegram_bot.bot import bot
from telegram_bot.middlewares.localization import locale_middleware
from telegram_bot.routers import (
    registration_router,
    session_router,
    start_router,
    appointment_router,
    support_router
)


async def main() -> None:
    dp = Dispatcher()
    dp.update.outer_middleware(locale_middleware)
    dp.include_router(start_router)
    dp.include_router(registration_router)
    dp.include_router(session_router)
    dp.include_router(appointment_router)
    dp.include_router(support_router)

    await dp.start_polling(bot)
    logger.info("Bot started successfully.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
