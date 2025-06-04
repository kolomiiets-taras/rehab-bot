from functools import wraps

from sqlalchemy.ext.asyncio import AsyncSession

from logger import logger
from db.models import DailySession, DailySessionState


def validate_pulse(pulse: str) -> bool:
    """Validate if the pulse is an integer between 30 and 220."""
    try:
        pulse_value = int(pulse)
        return 30 <= pulse_value <= 220
    except ValueError:
        return False


async def finish_session(daily_session: DailySession, session: AsyncSession, skipped: bool):
    finished = False
    progress = daily_session.user_course.progress
    position = daily_session.position
    state = '2' if skipped else '1'

    daily_session.user_course.progress = progress[:position] + state + progress[position + 1:]
    daily_session.state = DailySessionState.SKIPPED if skipped else DailySessionState.FINISHED

    daily_session.user_course.current_position += 1
    current_position = daily_session.user_course.current_position
    current_iteration = daily_session.user_course.current_iteration
    if daily_session.user_course.course.items_count == current_position / current_iteration:
        if daily_session.user_course.current_iteration == daily_session.user_course.iterations:
            daily_session.user_course.finished = True
            finished = True
        daily_session.user_course.current_iteration += 1

    session.add(daily_session.user_course)
    session.add(daily_session)
    await session.commit()
    logger.info(
        f"Session finished for user {daily_session.user_course.user_id} "
        f"({daily_session.id}), position: {position}, skipped: {skipped}"
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

