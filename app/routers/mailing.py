import json

from sqlalchemy.orm import selectinload

from app.config import app_config
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.models.user import UserCourse, User
from sqlalchemy import select
from datetime import time
from .utils import access_for
from ..models import Course, CourseItem

router = APIRouter(prefix="/mailing")
templates = app_config.TEMPLATES


@router.get("/")
async def mailings_list(request: Request, db: AsyncSession = Depends(get_db)):
    stmt = select(UserCourse).options(
        selectinload(UserCourse.course),
        selectinload(UserCourse.user)
    )

    mailings_result = await db.execute(stmt)
    mailings = mailings_result.scalars().all()

    return templates.TemplateResponse(
        "mailing.html",
        {
            "request": request,
            "mailings": mailings,
        }
    )


@router.get("/add")
async def create_mailing_page(request: Request, db: AsyncSession = Depends(get_db)):
    users_result = await db.execute(select(User))
    users = users_result.scalars().all()

    course_result = await db.execute(select(Course))
    courses = course_result.scalars().all()

    return templates.TemplateResponse(
        "mailing-add.html", {
            "request": request,
            "users": users,
            "courses": courses
        }
    )


@router.post("/add")
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
        user_course = UserCourse(
            user_id=user_id,
            course_id=course_id,
            progress=progress,
            mailing_time=mailing_time,
            mailing_days=",".join(str(d) for d in sorted(mailing_days))
        )
        db.add(user_course)
    await db.commit()

    return RedirectResponse(url=f"/mailing?success=1", status_code=303)
