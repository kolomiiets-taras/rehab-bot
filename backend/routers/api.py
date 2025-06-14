import csv
from io import StringIO

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload, with_loader_criteria
from starlette.responses import StreamingResponse

from db.models import Exercise, Complex, User, Appointment, AppointmentStatus, Role, UserCourse
from db.database import get_db
from backend.routers.utils import access_for

router = APIRouter(prefix="/api")


@router.get("/exercises")
@access_for(Role.ADMIN, Role.DOCTOR, Role.MANAGER)
async def get_all_exercises(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Exercise))
    exercises = result.scalars().all()
    return [
        {"id": exercise.id, "title": exercise.title}
        for exercise in exercises
    ]


@router.get("/complexes")
@access_for(Role.ADMIN, Role.DOCTOR, Role.MANAGER)
async def get_all_complexes(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Complex))
    complexes = result.scalars().all()
    return [
        {"id": comp.id, "name": comp.name}
        for comp in complexes
    ]


@router.get("/users")
@access_for(Role.ADMIN, Role.DOCTOR, Role.MANAGER)
async def get_all_users(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [
        {"id": user.id, "name": f'{user.last_name} {user.first_name}'}
        for user in users
    ]


@router.get("/appointments/{pending}")
@access_for(Role.ADMIN, Role.DOCTOR, Role.MANAGER)
async def get_appointments(request: Request, pending: str, db: AsyncSession = Depends(get_db)):
    if pending.lower() not in ["true", "false"]:
        raise HTTPException(status_code=400, detail="Invalid 'pending' parameter. Use 'true' or 'false'.")
    is_pending = pending.lower() == "true"
    result = await db.execute(
        select(Appointment)
        .where(Appointment.status == (AppointmentStatus.PENDING if is_pending else AppointmentStatus.CONFIRMED))
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
@access_for(Role.ADMIN, Role.DOCTOR, Role.MANAGER)
async def confirm_appointment(request: Request, appointment_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
    appointment = result.scalar_one_or_none()

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    appointment.status = AppointmentStatus.CONFIRMED
    await db.commit()
    return {"status": "confirmed"}


@router.get("/export/users", name="export_patients_csv")
@access_for(Role.ADMIN, Role.MANAGER)
async def export_patients_csv(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.courses).selectinload(UserCourse.course),
            with_loader_criteria(UserCourse, UserCourse.finished == False)
        )
    )
    users = result.scalars().all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["ID", "Telegram ID", "Імʼя", "Прізвище", "Телефон", "Поточний курс", "Дата реєстрації"]
    )

    for user in users:
        writer.writerow([
            user.id,
            user.telegram_id,
            user.first_name,
            user.last_name,
            user.phone,
            user.courses[0].course.name if user.courses else "-",
            user.created_at.strftime('%Y-%m-%d %H:%M')
        ])

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=patients.csv"},
    )
