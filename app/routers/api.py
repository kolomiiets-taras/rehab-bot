from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import Exercise, Complex, User, Appointment, AppointmentStatus
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


@router.get("/appointments")
async def get_pending_appointments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Appointment)
        .where(Appointment.status == AppointmentStatus.PENDING)
        .options(selectinload(Appointment.user))
        .order_by(Appointment.created_at.desc())
    )
    appointments = result.scalars().all()
    return [
        {
            "id": app.id,
            "user_id": app.user_id,
            "user_name": f'{app.user.last_name} {app.user.first_name}',
            "user_phone": app.user.phone,
            "created_at": app.created_at,
        }
        for app in appointments
    ]


@router.post("/appointments/confirm/{appointment_id}/")
async def confirm_appointment(appointment_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment.status = AppointmentStatus.CONFIRMED
    await db.commit()
    return {"status": "confirmed"}
