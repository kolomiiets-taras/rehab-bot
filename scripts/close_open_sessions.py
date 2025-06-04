import os
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Встановлюємо змінну оточення POSTGRES_HOST до будь-яких імпортів
os.environ["POSTGRES_HOST"] = "localhost"

# Налаштування власного логера
log_dir = Path(__file__).parent.parent / "cron_logs"
log_dir.mkdir(exist_ok=True)

logger = logging.getLogger("close_open_sessions")
logger.setLevel(logging.INFO)

handler = logging.FileHandler(log_dir / "close_open_sessions.log")
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Імпортуємо необхідні модулі для роботи з базою даних
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.session_wraper import with_session
from db.models import DailySession, DailySessionState, UserCourse, Course
from telegram_bot.routers.utils import finish_session


@with_session
async def close_open_sessions(session: AsyncSession):
    """Закриває всі відкриті сесії, які були створені до поточної дати."""
    start_time = datetime.now()
    logger.info(f"Початок закриття відкритих сесій: {start_time}")

    try:
        filters = and_(
            DailySession.state.in_([DailySessionState.IN_PROGRESS, DailySessionState.SENT]),
            DailySession.date < datetime.today().date()
        )
        sessions_result = await session.execute(
            select(DailySession)
            .where(filters)
            .options(
                selectinload(DailySession.user_course)
                .selectinload(UserCourse.course)
                .selectinload(Course.items)
            )
        )
        open_sessions = sessions_result.scalars().all()
        logger.info(f"Знайдено {len(open_sessions)} відкритих сесій для закриття")

        for i, daily_session in enumerate(open_sessions, 1):
            try:
                logger.info(
                    f"Закриття сесії {i}/{len(open_sessions)}: ID={daily_session.id}, User={daily_session.user_course.user_id}")
                await finish_session(daily_session, session, skipped=True)
                logger.info(f"Сесія {daily_session.id} успішно закрита")
            except Exception as e:
                logger.error(f"Помилка при закритті сесії {daily_session.id}: {e}")

    except Exception as e:
        logger.error(f"Помилка при закритті відкритих сесій: {e}")

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    logger.info(f"Закриття відкритих сесій завершено: {end_time}. Тривалість: {duration} секунд")


if __name__ == "__main__":
    try:
        logger.info("Початок виконання скрипта закриття сесій")
        asyncio.run(close_open_sessions())
        logger.info("Скрипт закриття сесій успішно завершено")
    except Exception as e:
        logger.error(f"Критична помилка в скрипті закриття сесій: {e}")