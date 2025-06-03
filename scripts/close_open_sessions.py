from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.session_wraper import with_session
from logger import logger
from db.models import DailySession, DailySessionState, UserCourse, Course
from telegram_bot.routers.utils import finish_session


@with_session
async def close_open_sessions(session: AsyncSession):
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
    logger.warning(f"Skipping {len(open_sessions)} open sessions")
    for daily_session in open_sessions:
        await finish_session(daily_session, session, skipped=True)


if __name__ == "__main__":
    import asyncio
    asyncio.run(close_open_sessions())
