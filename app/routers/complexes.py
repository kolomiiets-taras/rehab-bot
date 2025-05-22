import json

from fastapi import APIRouter, Request, Depends, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, delete
from sqlalchemy.orm import selectinload

from app.config import app_config
from app.db.database import get_db
from app.models import Complex, ComplexExercise, Role
from fastapi.responses import RedirectResponse
from fastapi.exceptions import HTTPException

from app.routers.utils import access_for

router = APIRouter(prefix="/complexes")
templates = app_config.TEMPLATES


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
    for comp in complexes:
        comp.exercises_count = len(comp.exercises)

    return templates.TemplateResponse(
        "complexes.html", {
            "request": request,
            "complexes": complexes,
            "query": query
        }
    )


@router.post("/add")
@access_for(Role.ADMIN)
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
    return RedirectResponse(url=f"/complexes/{new_complex.id}?success=1", status_code=303)


@router.get("/{complex_id}")
@access_for(Role.ADMIN, Role.DOCTOR)
async def complex_details(request: Request, complex_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Complex).where(Complex.id == complex_id).options(
            selectinload(Complex.exercises).selectinload(ComplexExercise.exercise)
        )
    )
    comp = result.scalar_one_or_none()
    if not complex:
        raise HTTPException(status_code=404, detail="Complex not found")

    return templates.TemplateResponse(
        "complex-detail.html", {
            "request": request,
            "complex": comp
        }
    )


@router.post("/delete/{complex_id}")
@access_for(Role.ADMIN)
async def delete_complex(complex_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Complex).where(Complex.id == complex_id))
    comp = result.scalar_one_or_none()
    if comp:
        await db.delete(comp)
        await db.commit()
    return RedirectResponse(url="/complexes?success=1", status_code=303)


@router.post("/edit/{complex_id}")
@access_for(Role.ADMIN)
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
        raise HTTPException(status_code=404, detail="Complex not found")

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

    return RedirectResponse(
        url=f"/complexes/{complex_id}?success=1", status_code=status.HTTP_303_SEE_OTHER
    )
