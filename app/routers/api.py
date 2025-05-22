from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Exercise, Complex, User
from app.db.database import get_db


router = APIRouter(prefix="/api")


@router.get("/exercises")
async def get_all_exercises(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Exercise))
    exercises = result.scalars().all()
    return [
        {"id": exercise.id, "title": exercise.title}
        for exercise in exercises
    ]


@router.get("/complexes")
async def get_all_complexes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Complex))
    complexes = result.scalars().all()
    return [
        {"id": comp.id, "name": comp.name}
        for comp in complexes
    ]


@router.get("/users")
async def get_all_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [
        {"id": user.id, "name": f'{user.last_name} {user.first_name}'}
        for user in users
    ]
