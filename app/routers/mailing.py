import json

from sqlalchemy.orm import selectinload

from app.config import app_config
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.models.user import UserCourse, User
from sqlalchemy import select, not_, exists
from datetime import time
from .utils import access_for, error_handler
from ..logger import logger
from ..models import Course, CourseItem, Role

router = APIRouter(prefix="/mailing")
templates = app_config.TEMPLATES


@router.get("/")
@access_for(Role.ADMIN, Role.DOCTOR)
async def mailings_list(request: Request, db: AsyncSession = Depends(get_db)):
    stmt = select(UserCourse).options(
        selectinload(UserCourse.course),
        selectinload(UserCourse.user)
    )

    mailings_result = await db.execute(stmt)
    mailings = mailings_result.scalars().all()

    course_result = await db.execute(select(Course))
    courses = course_result.scalars().all()

    return templates.TemplateResponse(
        "mailing/mailing.html",
        {
            "request": request,
            "mailings": mailings,
            "courses": courses
        }
    )


@router.get("/add")
@access_for(Role.ADMIN, Role.DOCTOR)
@error_handler('mailing')
async def create_mailing_page(request: Request, db: AsyncSession = Depends(get_db)):
    users_result = await db.execute(
        select(User).where(
            not_(
                exists().where(
                    (UserCourse.user_id == User.id) &
                    (UserCourse.finished == False)
                )
            )
        )
    )
    users = users_result.scalars().all()

    course_result = await db.execute(select(Course))
    courses = course_result.scalars().all()

    return templates.TemplateResponse(
        "mailing/mailing-add.html", {
            "request": request,
            "users": users,
            "courses": courses
        }
    )


@router.post("/add")
@access_for(Role.ADMIN, Role.DOCTOR)
@error_handler('mailing')
async def add_mailing(
    request: Request,
    users: list[int] = Form(...),
    course_id_str: str = Form(...),
    course_name: str = Form(...),
    items_json: str = Form(None),
    mailing_time: time = Form(...),
    mailing_days: list[int] = Form(...),
    db: AsyncSession = Depends(get_db)
):

    if items := json.loads(items_json or "[]"):
        course = Course(name=course_name if course_name else 'Без Назви')
        db.add(course)
        await db.flush()  # присвоит course.id

        # добавляем упражнения
        progress = ''
        for itm in items:
            kwarg = {f'{itm["type"]}_id': itm["id"]}
            db.add(CourseItem(**kwarg, course_id=course.id, position=int(itm['position'])))
            progress += '0'

        await db.commit()
        course_id = course.id
    else:
        course_id = int(course_id_str)
        course_result = await db.execute(
            select(Course).where(Course.id == course_id).options(selectinload(Course.items))
        )
        course = course_result.scalar_one_or_none()
        progress = '0' * len(course.items)

    for user_id in users:
        # 1. Найти активную рассылку для пользователя (если есть)
        stmt = select(UserCourse).where(
            UserCourse.user_id == user_id,
            UserCourse.finished == False
        )
        result = await db.execute(stmt)
        active_course = result.scalar_one_or_none()

        # 2. Завершить текущую, если она есть
        if active_course:
            active_course.finished = True

        # 3. Добавить новую
        user_course = UserCourse(
            user_id=user_id,
            course_id=course_id,
            progress=progress,
            mailing_time=mailing_time,
            mailing_days=sorted(mailing_days)
        )
        db.add(user_course)
    await db.commit()
    logger.info(f"Added new mailing for users: {users} with course {course_id}")
    return RedirectResponse(url=f"/mailing?success=1", status_code=303)


@router.post("/delete/{mailing_id}")
@access_for(Role.ADMIN, Role.DOCTOR)
@error_handler('mailing')
async def delete_mailing(
    request: Request,
    mailing_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(UserCourse).where(UserCourse.id == mailing_id))
    user_course = result.scalar_one_or_none()
    if user_course:
        await db.delete(user_course)
        await db.commit()
        logger.info(f"Deleted mailing ID {mailing_id}")

        referer = request.headers.get("referer")
        url = referer + '?success=1' if referer else "/mailing?success=1"
        return RedirectResponse(url=url, status_code=303)

    logger.error(f"Mailing not found for delete ID {mailing_id}")
    return RedirectResponse(url="/mailing?error=1", status_code=303)


@router.post("/stop/{mailing_id}")
@access_for(Role.ADMIN, Role.DOCTOR)
@error_handler('mailing')
async def stop_mailing(
    request: Request,
    mailing_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(UserCourse).where(UserCourse.id == mailing_id))
    user_course = result.scalar_one_or_none()
    if user_course:
        user_course.finished = True
        await db.commit()
        logger.info(f"Stopped mailing ID {mailing_id}")

        referer = request.headers.get("referer")
        url = referer + '?success=1' if referer else "/mailing?success=1"
        return RedirectResponse(url=url, status_code=303)

    logger.error(f"Mailing not found for stop ID {mailing_id}")
    return RedirectResponse(url="/mailing?error=1", status_code=303)


@router.post("/start/{mailing_id}")
@access_for(Role.ADMIN, Role.DOCTOR)
@error_handler('mailing')
async def start_mailing(
    request: Request,
    mailing_id: int,
    db: AsyncSession = Depends(get_db)
):
    # 1. Найти рассылку по ID
    result = await db.execute(select(UserCourse).where(UserCourse.id == mailing_id))
    user_course = result.scalar_one_or_none()
    if user_course:
        user_id = user_course.user_id

        # 2. Завершить все другие активные рассылки этого пользователя
        update_stmt = (
            select(UserCourse)
            .where(
                UserCourse.user_id == user_id,
                UserCourse.id != mailing_id,
                UserCourse.finished == False
            )
        )
        result = await db.execute(update_stmt)
        other_active_courses = result.scalars().all()

        for course in other_active_courses:
            course.finished = True
            logger.error(f"Mailing ID {mailing_id} finished")

        # 3. Активировать выбранную
        user_course.finished = False

        await db.commit()
        logger.info(f"Started mailing ID {mailing_id}")

        referer = request.headers.get("referer")
        url = referer + '?success=1' if referer else "/mailing?success=1"
        return RedirectResponse(url=url, status_code=303)

    logger.error(f"Mailing not found for start ID {mailing_id}")
    return RedirectResponse(url="/mailing?success=1", status_code=303)


@router.post("/edit/{mailing_id}")
@access_for(Role.ADMIN, Role.DOCTOR)
@error_handler('mailing')
async def edit_mailing(
    request: Request,
    mailing_id: int,
    mailing_time: time = Form(...),
    mailing_days: list[int] = Form(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(UserCourse).where(UserCourse.id == mailing_id))
    user_course = result.scalar_one_or_none()

    if user_course:
        user_course.mailing_time = mailing_time
        user_course.mailing_days = sorted(mailing_days)
        await db.commit()
        logger.info(f"Edited mailing ID {mailing_id}")

        referer = request.headers.get("referer")
        url = referer + '?success=1' if referer else "/mailing?success=1"
        return RedirectResponse(url=url, status_code=303)

    logger.error(f"Mailing not found for edit ID {mailing_id}")
    return RedirectResponse(url="/mailing?error=1", status_code=303)
