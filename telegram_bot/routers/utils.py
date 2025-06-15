from datetime import datetime
from functools import wraps
from sqlalchemy.ext.asyncio import AsyncSession
from logger import get_bot_logger
from db.models import DailySession, DailySessionState

logger = get_bot_logger()


def validate_pulse(pulse: str) -> bool:
    """Validate if the pulse is an integer between 30 and 220."""
    try:
        pulse_value = int(pulse)
        return 30 <= pulse_value <= 220
    except ValueError:
        return False


async def finish_session(daily_session: DailySession, session: AsyncSession, skipped: bool):
    finished = False
    daily_session.state = DailySessionState.SKIPPED if skipped else DailySessionState.FINISHED

    daily_session.user_course.current_position += 1
    current_position = daily_session.user_course.current_position
    if daily_session.user_course.end_date == datetime.today().date():
        daily_session.user_course.finished = True
        finished = True

    session.add(daily_session.user_course)
    session.add(daily_session)
    await session.commit()
    logger.info(
        f"Session finished for user {daily_session.user_course.user_id} "
        f"({daily_session.id}), position: {current_position}, skipped: {skipped}"
    )
    return finished


def error_logger(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in Telegram Bot {func.__name__}: {e}")
            raise e

    return wrapper
