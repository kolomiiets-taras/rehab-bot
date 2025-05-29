from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session_wraper import with_session
from app.models import DailySession


def validate_pulse(pulse: str) -> bool:
    """Validate if the pulse is an integer between 30 and 220."""
    try:
        pulse_value = int(pulse)
        return 30 <= pulse_value <= 220
    except ValueError:
        return False


async def finish_session(daily_session: DailySession, session: AsyncSession, skipped: bool):
    progress = daily_session.user_course.progress
    position = daily_session.position
    state = '2' if skipped else '1'

    daily_session.user_course.progress = progress[:position] + state + progress[position + 1:]

    daily_session.user_course.current_position += 1
    if daily_session.user_course.current_position == len(daily_session.user_course.course.items):
        daily_session.user_course.finished = True

    session.add(daily_session.user_course)
    session.add(daily_session)
    await session.commit()
