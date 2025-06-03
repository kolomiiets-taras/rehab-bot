from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
import json

from config import app_config
from db.database import get_db
from logger import logger
from db.models.course import Course
from db.models import CourseItem, Role
from backend.routers.utils import error_handler, access_for

router = APIRouter(prefix="/courses")
templates = app_config.TEMPLATES


@router.get("/")
@access_for(Role.ADMIN, Role.DOCTOR)
async def list_courses(request: Request, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Course)
        .options(
            selectinload(Course.items)
            .selectinload(CourseItem.exercise),
            selectinload(Course.items)
            .selectinload(CourseItem.complex)
        )
    )
    result = await db.execute(stmt)
    courses = result.scalars().all()
    return templates.TemplateResponse(
        "course/courses.html",
        {"request": request, "courses": courses},
    )


@router.get("/{course_id}")
@access_for(Role.ADMIN, Role.DOCTOR)
async def course_detail(request: Request, course_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Course)
        .where(Course.id == course_id)
        .options(
            selectinload(Course.items)
            .selectinload(CourseItem.exercise),
            selectinload(Course.items)
            .selectinload(CourseItem.complex)
        )
    )
    course = result.scalar_one_or_none()
    if not course:
        logger.error(f"Course not found: {course_id}")
        return RedirectResponse(url="/courses?error=1", status_code=303)

    # pre-build your JSON-serializable list in Python
    items_list = []
    for ci in course.items:
        if ci.exercise_id:
            items_list.append({
                "type": "exercise",
                "id": ci.exercise.id,
                "title": ci.exercise.title,
                "position": ci.position,
            })
        else:
            items_list.append({
                "type": "complex",
                "id": ci.complex.id,
                "title": ci.complex.name,
                "position": ci.position,
            })

    return templates.TemplateResponse("course/course-detail.html", {
        "request": request,
        "course": course,
        "items_list": items_list,
    })


@router.post("/add")
@access_for(Role.ADMIN)
@error_handler('courses')
async def add_course(
    request: Request,
    name: str = Form(...),
    items_json: str = Form(None),
    db: AsyncSession = Depends(get_db),
):
    items = json.loads(items_json or "[]")

    if items:
        course = Course(name=name)
        db.add(course)
        await db.flush()  # присвоит course.id

        # добавляем упражнения
        for itm in items:
            kwarg = {f'{itm["type"]}_id': itm["id"]}
            db.add(CourseItem(**kwarg, course_id=course.id, position=int(itm['position'])))

        await db.commit()
        logger.info(f"Added new course: {course.name} (ID: {course.id})")

    return RedirectResponse(url="/courses?success=1", status_code=303)


@router.post("/edit/{course_id}")
@access_for(Role.ADMIN)
@error_handler('courses')
async def edit_course(
    request: Request,
    course_id: int,
    name: str = Form(...),
    items_json: str = Form(None),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        logger.error(f"Course not found for edit: {course_id}")
        return RedirectResponse(url="/courses?error=1", status_code=303)

    course.name = name
    # удаляем старые связи
    await db.execute(delete(CourseItem).where(CourseItem.course_id == course_id))
    await db.flush()

    items = json.loads(items_json or "[]")

    for itm in items:
        kwarg = {f'{itm["type"]}_id': itm["id"]}
        db.add(CourseItem(**kwarg, course_id=course.id, position=int(itm['position'])))

    await db.commit()
    logger.info(f"Updated course: {course.name} (ID: {course.id})")
    return RedirectResponse(url=f"/courses/{course_id}?success=1", status_code=303)


@router.post("/delete/{course_id}")
@access_for(Role.ADMIN)
@error_handler('courses')
async def delete_course(request: Request, course_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if course:
        await db.delete(course)
        await db.commit()
        logger.info(f"Deleted course: {course.name} (ID: {course.id})")
        return RedirectResponse(url="/courses?success=1", status_code=303)

    logger.error(f"Course not found for delete: {course_id}")
    return RedirectResponse(url="/courses?error=1", status_code=303)
