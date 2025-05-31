from datetime import date

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session_wraper import with_session
from app.models import UserCourse, Course, CourseItem, DailySession, DailySessionState
from app.telegram_bot.utils import send_session


@with_session
async def send_mailing(session: AsyncSession) -> None:
    filters = and_(
        UserCourse.finished == False
        # func.date_part('hour', UserCourse.mailing_time) == datetime.now().hour,
        # func.date_part('minute', UserCourse.mailing_time) == datetime.now().minute,
        # str(datetime.today().isoweekday()) in UserCourse.mailing_days
    )
    user_course_result = await session.execute(
        select(UserCourse).where(filters).options(
            selectinload(UserCourse.course).selectinload(Course.items).selectinload(CourseItem.exercise),
            selectinload(UserCourse.course).selectinload(Course.items).selectinload(CourseItem.complex),
            selectinload(UserCourse.user)
        )
    )
    user_courses = user_course_result.scalars().all()
    for user_course in user_courses:
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


if __name__ == "__main__":
    import asyncio
    asyncio.run(send_mailing())
