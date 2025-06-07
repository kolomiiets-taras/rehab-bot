from fastapi import APIRouter, Request, Form, Depends, UploadFile, File
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from config import app_config
from db.database import get_db
from logger import get_site_logger
from db.models import Role
from db.models.exercise import Exercise
from fastapi.background import BackgroundTasks

from backend.routers.utils import save_exercise_media, access_for, error_handler

router = APIRouter(prefix="/exercises")
templates = app_config.TEMPLATES

logger = get_site_logger()


@router.get("/")
@access_for(Role.ADMIN, Role.DOCTOR)
async def exercises_list(request: Request, db: AsyncSession = Depends(get_db)):
    query = request.query_params.get("q")

    stmt = select(Exercise)
    if query:
        stmt = stmt.where(
            or_(
                Exercise.title.ilike(f"%{query}%"),
                Exercise.text.ilike(f"%{query}%"),
                Exercise.media.ilike(f"%{query}%")
            )
        )

    exercises_result = await db.execute(stmt)
    exercises = exercises_result.scalars().all()

    return templates.TemplateResponse(
        "exercise/exercises.html", {
            "request": request,
            "exercises": exercises,
            "query": query
        }
    )


@router.get("/{exercise_id}")
@error_handler('exercises')
@access_for(Role.ADMIN, Role.DOCTOR)
async def exercise_detail(
        request: Request,
        exercise_id: int,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Exercise).where(Exercise.id == exercise_id))
    exercise = result.scalar_one_or_none()
    if not exercise:
        logger.error(f"Exercise with id {exercise_id} not found")
        return RedirectResponse(url="/exercises?error=1", status_code=303)

    return templates.TemplateResponse(
        "exercise/exercise-detail.html", {
            "request": request,
            "exercise": exercise,
        }
    )


@router.post("/add")
@access_for(Role.ADMIN)
@error_handler('exercises')
async def add_exercise(
        request: Request,
        background_tasks: BackgroundTasks,
        title: str = Form(...),
        media: UploadFile = Form(...),
        text: str = Form(...),
        db: AsyncSession = Depends(get_db)
):
    exercise = Exercise(title=title, text=text)
    db.add(exercise)
    await db.commit()

    file_content = await media.read()
    background_tasks.add_task(save_exercise_media, media.filename, file_content, exercise.id)

    logger.info(f"Added new exercise: {exercise.id} - {exercise.title}")
    return RedirectResponse(url=f"/exercises/{exercise.id}?success=1", status_code=303)


@router.post("/delete/{exercise_id}")
@access_for(Role.ADMIN)
@error_handler('exercises')
async def delete_exercise(request: Request, exercise_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Exercise).where(Exercise.id == exercise_id))
    exercise = result.scalar_one_or_none()
    if exercise:
        # Удаляем файл, если он существует
        media_path = app_config.MEDIA_PATH / exercise.media
        try:
            if media_path.exists():
                media_path.unlink()
        except Exception as e:
            logger.error(f"Can't delete file: {e}")

        await db.delete(exercise)
        await db.commit()
        logger.info(f"Deleted exercise: {exercise.id} - {exercise.title}")

    return RedirectResponse(url="/exercises?success=1", status_code=303)


@router.post("/edit/{exercise_id}")
@access_for(Role.ADMIN)
@error_handler('exercises')
async def edit_exercise(
        request: Request,
        exercise_id: int,
        background_tasks: BackgroundTasks,
        title: str = Form(...),
        text: str = Form(...),
        media: UploadFile = File(None),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Exercise).where(Exercise.id == exercise_id))
    exercise = result.scalar_one_or_none()

    if not exercise:
        logger.error(f"Exercise with id {exercise_id} not found")
        return RedirectResponse(url="/exercises?error=1", status_code=303)

    exercise.title = title
    exercise.text = text

    # обработка медиа
    if media and media.filename:
        content = await media.read()

        # Пропускаем пустые файлы
        if content:
            background_tasks.add_task(
                save_exercise_media,
                media.filename,
                content,
                exercise.id
            )

    await db.commit()
    logger.info(f"Edited exercise: {exercise.id} - {exercise.title}")
    return RedirectResponse(url=f"/exercises/{exercise_id}?success=1", status_code=303)
