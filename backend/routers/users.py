from sqlalchemy.orm import selectinload

from config import app_config
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db
from db.models import Role, Course, CourseItem, User, UserCourse
from sqlalchemy import select, or_, String, func
from datetime import datetime, date, timedelta
from .utils import access_for, error_handler
from backend.constants import WELLBEING_EMOJI_MAP
from logger import get_site_logger

router = APIRouter(prefix="/users")
templates = app_config.TEMPLATES
ITEMS_PER_PAGE = 10

logger = get_site_logger()


@router.get("/")
@access_for(Role.ADMIN, Role.DOCTOR, Role.MANAGER)
async def users_list(request: Request, db: AsyncSession = Depends(get_db)):
    query = request.query_params.get("q")
    page = int(request.query_params.get("page", 1))
    offset = (page - 1) * ITEMS_PER_PAGE

    stmt = select(User)
    count_stmt = select(func.count()).select_from(User)

    if query:
        filters = or_(
            User.first_name.ilike(f"%{query}%"),
            User.last_name.ilike(f"%{query}%"),
            User.phone.ilike(f"%{query}%"),
            User.telegram_id.cast(String).ilike(f"%{query}%")
        )
        stmt = stmt.where(filters)
        count_stmt = count_stmt.where(filters)

    total_result = await db.execute(count_stmt)
    total_count = total_result.scalar()
    total_pages = (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    result = await db.execute(stmt.offset(offset).limit(ITEMS_PER_PAGE))
    users = result.scalars().all()

    return templates.TemplateResponse(
        "user/users.html",
        {
            "request": request,
            "users": users,
            "query": query,
            "page": page,
            "total_pages": total_pages,
        }
    )


@router.get("/{user_id}")
@access_for(Role.ADMIN, Role.DOCTOR, Role.MANAGER)
@error_handler('users')
async def user_detail(request: Request, user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if not user:
        logger.error(f"User not found: {user_id}")
        return RedirectResponse(url="/users?error=1", status_code=303)

    course_result = await db.execute(
        select(UserCourse).order_by(UserCourse.created_at.desc())
        .where(UserCourse.user_id == user_id)
        .options(
            selectinload(UserCourse.course)
            .selectinload(Course.items),  # сначала items
            selectinload(UserCourse.course)
            .selectinload(Course.items)
            .selectinload(CourseItem.complex),
            selectinload(UserCourse.course)
            .selectinload(Course.items)
            .selectinload(CourseItem.exercise),
            selectinload(UserCourse.sessions)
        )
    )
    user_course = course_result.scalars().first()

    if user_course:
        sessions = user_course.sessions
    else:
        sessions = []

    pulse_chart_data = {
        "labels": [s.date.strftime("%d.%m") for s in sessions],
        "before_name": "Пульс до",
        "after_name": "Пульс після",
        "pulse_before": [s.pulse_before for s in sessions if s.pulse_before is not None],
        "pulse_after": [s.pulse_after for s in sessions if s.pulse_after is not None],
        "units": "уд/хв",
    }

    wellbeing_chart_data = {
        "labels": [s.date.strftime("%d.%m") for s in sessions],
        "before_name": "Самопочуття до",
        "after_name": "Самопочуття після",
        "wellbeing_before": [s.wellbeing_before for s in sessions if s.wellbeing_before is not None],
        "wellbeing_after": [s.wellbeing_after for s in sessions if s.wellbeing_after is not None],
        "units": "балів",
    }

    course_days = []
    if user_course and user_course.progress:
        start_date = user_course.created_at.date()
        progress_bits = user_course.progress.strip()
        allowed_weekdays = set(user_course.mailing_days)  # Наприклад: {1, 3, 5}
        calendar_dates = []

        while len(calendar_dates) < len(user_course.progress):
            if start_date.isoweekday() in allowed_weekdays:
                calendar_dates.append(start_date)
            start_date += timedelta(days=1)

        for i, bit in enumerate(progress_bits):
            match bit:
                case "0":
                    status = 'not_sent'
                case "1":
                    status = 'done'
                case "2":
                    status = 'missed'
                case _:
                    status = 'missed'

            pulse_before = '-'
            pulse_after = '-'
            wellbeing_before = '-'
            wellbeing_after = '-'

            if sessions and status in ['done', 'missed']:
                pulse_before = sessions[i].pulse_before or '-'
                pulse_after = sessions[i].pulse_after or '-'
                wellbeing_before = sessions[i].wellbeing_before or '-'
                wellbeing_after = sessions[i].wellbeing_after or '-'

            item_index = i % user_course.course.items_count
            if user_course.course.items[item_index].is_exercise:
                exercise_title = user_course.course.items[item_index].exercise.title
            else:
                exercise_title = user_course.course.items[item_index].complex.name
            course_days.append({
                "date": calendar_dates[i].strftime("%d-%m"),
                "status": status,
                "current": (i == user_course.current_position),
                "exercise": exercise_title,
                "pulse_before": pulse_before,
                "pulse_after": pulse_after,
                "wellbeing_before": WELLBEING_EMOJI_MAP.get(wellbeing_before, '-'),
                "wellbeing_after": WELLBEING_EMOJI_MAP.get(wellbeing_after, '-'),
            })

    return templates.TemplateResponse("user/user-detail.html", {
        "request": request,
        "user": user,
        "pulse_chart_data": pulse_chart_data,
        "wellbeing_chart_data": wellbeing_chart_data,
        "mailing": user_course,
        "course": user_course.course if user_course else None,
        "course_days": course_days
    })


@router.post("/add")
@access_for(Role.ADMIN, Role.DOCTOR, Role.MANAGER)
@error_handler('users')
async def add_user(
        request: Request,
        telegram_id: int = Form(...),
        first_name: str = Form(...),
        last_name: str = Form(...),
        phone: str = Form(None),
        birthday: date = Form(None),
        db: AsyncSession = Depends(get_db),
):
    user = User(
        telegram_id=telegram_id,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        birthday=birthday,
        created_at=datetime.now()
    )
    db.add(user)
    await db.commit()
    logger.info(f"Added new user: {user.telegram_id} - {user.first_name} {user.last_name}")
    return RedirectResponse(url="/users?success=1", status_code=303)


@router.post("/delete/{user_id}")
@access_for(Role.ADMIN, Role.DOCTOR)
@error_handler('users')
async def delete_user(request: Request, user_id: int, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, user_id)
    if user:
        await db.delete(user)
        await db.commit()
        logger.info(f"Deleted user: {user.telegram_id} - {user.first_name} {user.last_name}")
        return RedirectResponse(url="/users?success=1", status_code=303)
    logger.error(f"User not found for delete: {user_id}")
    return RedirectResponse(url="/users?error=1", status_code=303)


@router.post("/edit/{user_id}")
@access_for(Role.ADMIN, Role.DOCTOR, Role.MANAGER)
@error_handler('users')
async def edit_user(
        request: Request,
        user_id: int,
        first_name: str = Form(...),
        last_name: str = Form(...),
        phone: str = Form(None),
        birthday: date = Form(None),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.first_name = first_name
        user.last_name = last_name
        user.phone = phone
        user.birthday = birthday
        await db.commit()
        logger.info(f"Edited user: {user.telegram_id} - {user.first_name} {user.last_name}")
        return RedirectResponse(url=f"/users/{user_id}?success=1", status_code=303)
    logger.error(f"User not found for edit: {user_id}")
    return RedirectResponse(url="/users?error=1", status_code=303)
