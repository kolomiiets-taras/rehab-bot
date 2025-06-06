import json

from fastapi import APIRouter, Request, Depends, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, delete
from sqlalchemy.orm import selectinload

from config import app_config
from db.database import get_db
from logger import get_site_logger
from db.models import Complex, ComplexExercise, Role
from fastapi.responses import RedirectResponse

from backend.routers.utils import access_for, error_handler

router = APIRouter(prefix="/complexes")
templates = app_config.TEMPLATES

logger = get_site_logger()


@router.get("/")
@access_for(Role.ADMIN, Role.DOCTOR)
async def complexes_list(request: Request, db: AsyncSession = Depends(get_db)):
    query = request.query_params.get("q")

    stmt = select(Complex).options(
        selectinload(Complex.exercises).selectinload(ComplexExercise.exercise)
    )
    if query:
        stmt = stmt.where(or_(Complex.name.ilike(f"%{query}%"))).options(
            selectinload(Complex.exercises).selectinload(ComplexExercise.exercise)
        )

    complexes_result = await db.execute(stmt)
    complexes = complexes_result.scalars().all()

    return templates.TemplateResponse(
        "complex/complexes.html", {
            "request": request,
            "complexes": complexes,
            "query": query
        }
    )


@router.get("/{complex_id}")
@access_for(Role.ADMIN, Role.DOCTOR)
async def complex_details(request: Request, complex_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Complex).where(Complex.id == complex_id).options(
            selectinload(Complex.exercises).selectinload(ComplexExercise.exercise)
        )
    )
    comp = result.scalar_one_or_none()
    if not comp:
        logger.error(f"Complex with id {complex_id} not found")
        return RedirectResponse(url="/complexes?error=1", status_code=303)

    return templates.TemplateResponse(
        "complex/complex-detail.html", {
            "request": request,
            "complex": comp
        }
    )


@router.post("/add")
@access_for(Role.ADMIN)
@error_handler('complexes')
async def add_complex(
        request: Request,
        name: str = Form(...),
        exercises_json: str = Form(...),  # JSON string of [{id, position}, …]
        db: AsyncSession = Depends(get_db),
):
    # 1) parse your JSON string into Python list of dicts
    try:
        items = json.loads(exercises_json)
    except json.JSONDecodeError:
        items = []

    # 2) create the Complex record
    new_complex = Complex(name=name)
    db.add(new_complex)
    await db.flush()  # so new_complex.id is set

    # 3) for each {id, position} dict insert a ComplexExercise
    for obj in items:
        ex_id = obj.get("id")
        pos = obj.get("position")
        # optional: skip invalid entries
        if ex_id is None or pos is None:
            continue

        ce = ComplexExercise(
            complex_id=new_complex.id,
            exercise_id=int(ex_id),
            position=int(pos),
        )
        db.add(ce)

    # 4) commit everything
    await db.commit()
    logger.info(f"Added new complex ID {new_complex.id} {new_complex.name}")
    return RedirectResponse(url=f"/complexes/{new_complex.id}?success=1", status_code=303)


@router.post("/delete/{complex_id}")
@access_for(Role.ADMIN)
@error_handler('complexes')
async def delete_complex(request: Request, complex_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Complex).where(Complex.id == complex_id))
    comp = result.scalar_one_or_none()
    if comp:
        await db.delete(comp)
        await db.commit()
        logger.info(f"Deleted complex ID {complex_id} {comp.name}")
        return RedirectResponse(url="/complexes?success=1", status_code=303)

    logger.error(f"Complex with id {complex_id} not found for deletion")
    return RedirectResponse(url="/complexes?error=1", status_code=303)


@router.post("/edit/{complex_id}")
@access_for(Role.ADMIN)
@error_handler('complexes')
async def edit_complex(
        request: Request,
        complex_id: int,
        name: str = Form(...),
        exercises_json: str = Form(...),
        db: AsyncSession = Depends(get_db),
):
    # 1) Получаем комплекс
    result = await db.execute(select(Complex).where(Complex.id == complex_id))
    comp = result.scalar_one_or_none()
    if not comp:
        logger.error(f"Complex with id {complex_id} not found for edit")
        return RedirectResponse(url="/complexes?error=1", status_code=303)

    comp.name = name

    try:
        items = json.loads(exercises_json)
    except json.JSONDecodeError:
        items = []

    await db.execute(
        delete(ComplexExercise).where(ComplexExercise.complex_id == complex_id)
    )

    for entry in items:
        ex_id = entry.get("id")
        pos = entry.get("position", 0)
        ce = ComplexExercise(
            complex_id=complex_id,
            exercise_id=int(ex_id),
            position=int(pos),
        )
        db.add(ce)

    await db.commit()
    logger.info(f"Updated complex ID {complex_id} {comp.name}")

    return RedirectResponse(
        url=f"/complexes/{complex_id}?success=1", status_code=status.HTTP_303_SEE_OTHER
    )
