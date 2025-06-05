import uuid
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from config import app_config
from db import async_session
from logger import logger
from db.models import Exercise
from db.models.employee import Role
import subprocess
from pathlib import Path
from functools import wraps


def access_for(*allowed_roles):
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            user = request.state.user

            if not user:
                return RedirectResponse(url="/login", status_code=303)

            if user.role == Role.OWNER or user.role in allowed_roles:
                return await func(request, *args, **kwargs)
            else:
                raise HTTPException(status_code=403, detail="Access denied")
        return wrapper
    return decorator


def convert_to_mp4(source_path: Path) -> Path:
    target_path = source_path.with_suffix('.mp4')
    subprocess.run([
        'ffmpeg',
        '-i', str(source_path),
        '-vcodec', 'libx264',
        '-acodec', 'aac',
        '-strict', 'experimental',
        str(target_path)
    ], check=True)
    source_path.unlink()  # Видаляємо оригінальний файл
    return target_path


async def save_exercise_media(filename: str, content: bytes, exercise_id: int):
    ext = Path(filename).suffix
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = app_config.MEDIA_PATH / unique_name

    # Сохраняем файл
    with file_path.open("wb") as buffer:
        buffer.write(content)

    allowed_formats = [".jpg", ".jpeg", ".png", ".gif", ".mp4"]
    allowed_formats += [fmt.upper() for fmt in allowed_formats]  # Добавляем верхний регистр

    # Конвертация если нужно
    if file_path.suffix not in allowed_formats:
        try:
            file_path = convert_to_mp4(file_path)
        except Exception as e:
            logger.error(f"⚠️ Media convert error (exercise ID {exercise_id}): {e}")

    # Обновляем имя файла в базе
    async with async_session() as session:
        result = await session.execute(select(Exercise).where(Exercise.id == exercise_id))
        exercise = result.scalar_one_or_none()
        if exercise:
            exercise.media = file_path.name
            logger.info(f"Media saved for exercise ID {exercise_id}: {file_path.name}")
            await session.commit()


def error_handler(path: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {path}: {e}")
                return RedirectResponse(url=f"/{path}?error=1", status_code=303)
        return wrapper
    return decorator
