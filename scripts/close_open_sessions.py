#!/usr/bin/env python3
import os
import asyncio
from datetime import datetime

# Встановлюємо змінну оточення POSTGRES_HOST для підключення до локальної бази
if 'POSTGRES_HOST' not in os.environ:
    os.environ['POSTGRES_HOST'] = 'localhost'

# Імпортуємо логер для скрипта
from logger import get_script_logger
logger = get_script_logger('close_open_sessions')

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
        exit(1)