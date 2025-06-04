import os
import asyncio
import logging
from datetime import date, datetime, timedelta
from pathlib import Path

# Встановлюємо змінну оточення POSTGRES_HOST до будь-яких імпортів
os.environ["POSTGRES_HOST"] = "localhost"

# Налаштування власного логера
log_dir = Path(__file__).parent.parent / "cron_logs"
log_dir.mkdir(exist_ok=True)

logger = logging.getLogger("send_mailing")
logger.setLevel(logging.INFO)

handler = logging.FileHandler(log_dir / "send_mailing.log")
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Імпортуємо необхідні модулі для роботи з базою даних
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.session_wraper import with_session
from db.models import UserCourse, Course, CourseItem, DailySession, DailySessionState
from telegram_bot.utils import send_session


@with_session
async def send_mailing(session: AsyncSession) -> None:
    """Функція для відправки розсилок користувачам."""
    now = datetime.now()
    logger.info(f"Запуск розсилки о {now}")

    start = (now - timedelta(minutes=5)).time()
    end = (now + timedelta(minutes=5)).time()

    if start > end:
        # Зазор пересікає опівніч
        time_filter = or_(
            UserCourse.mailing_time >= start,
            UserCourse.mailing_time <= end
        )
    else:
        time_filter = and_(
            UserCourse.mailing_time >= start,
            UserCourse.mailing_time <= end
        )

    filters = and_(
        UserCourse.finished == False,
        time_filter,
        UserCourse.mailing_days.any(now.isoweekday())
    )

    try:
        user_course_result = await session.execute(
            select(UserCourse).where(filters).options(
                selectinload(UserCourse.course).selectinload(Course.items).selectinload(CourseItem.exercise),
                selectinload(UserCourse.course).selectinload(Course.items).selectinload(CourseItem.complex),
                selectinload(UserCourse.user)
            )
        )
        user_courses = user_course_result.scalars().all()
        logger.info(f"Знайдено {len(user_courses)} курсів для розсилки")

        for user_course in user_courses:
            try:
                current_item = user_course.course.items[user_course.current_position]
                daily_session = DailySession(
                    user_course_id=user_course.id,
                    course_item_id=current_item.id,
                    date=date.today(),
                    position=user_course.current_position,
                    state=DailySessionState.SENT
                )
                session.add(daily_session)
                await session.commit()

                await send_session(
                    user_course.user.telegram_id,
                    daily_session.id,
                    user_course.user.language,
                    course_title=user_course.course.name,
                    session_number=user_course.current_position + 1,
                    total_sessions=len(user_course.course.items)
                )
                logger.info(
                    f"Розсилка відправлена для користувача {user_course.user.telegram_id}, сесія {daily_session.id}")
            except Exception as e:
                logger.error(f"Помилка при відправці для користувача {user_course.user.telegram_id}: {e}")
    except Exception as e:
        logger.error(f"Помилка при виконанні розсилки: {e}")

    logger.info("Розсилка завершена")


if __name__ == "__main__":
    try:
        logger.info("Початок виконання скрипта розсилки")
        asyncio.run(send_mailing())
        logger.info("Скрипт розсилки успішно завершено")
    except Exception as e:
        logger.error(f"Критична помилка в скрипті розсилки: {e}")