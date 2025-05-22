from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
import json

from app.config import app_config
from app.db.database import get_db
from app.models.course import Course
from app.models import CourseItem

router = APIRouter(prefix="/courses")
templates = app_config.TEMPLATES


@router.get("/")
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
        "courses.html",
        {"request": request, "courses": courses},
    )


@router.post("/add")
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
    return RedirectResponse(url="/courses?success=1", status_code=303)


@router.get("/{course_id}")
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
        raise HTTPException(404, "Курс не знайдений")

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

    return templates.TemplateResponse("course-detail.html", {
        "request": request,
        "course": course,
        "items_list": items_list,
    })


@router.post("/edit/{course_id}")
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
        raise HTTPException(404, "Курс не знайдений")

    course.name = name
    # удаляем старые связи
    await db.execute(delete(CourseItem).where(CourseItem.course_id == course_id))
    await db.flush()

    items = json.loads(items_json or "[]")

    for itm in items:
        kwarg = {f'{itm["type"]}_id': itm["id"]}
        db.add(CourseItem(**kwarg, course_id=course.id, position=int(itm['position'])))

    await db.commit()
    return RedirectResponse(url=f"/courses/{course_id}?success=1", status_code=303)


@router.post("/delete/{course_id}")
async def delete_course(course_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if course:
        await db.delete(course)
        await db.commit()
    return RedirectResponse(url="/courses?success=1", status_code=303)
