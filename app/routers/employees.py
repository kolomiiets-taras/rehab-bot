from datetime import datetime

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse
from passlib.handlers.bcrypt import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import app_config
from app.db.database import get_db
from app.models.employee import Employee, Role
from .utils import access_for

router = APIRouter(prefix="/employees")
templates = app_config.TEMPLATES


@router.get("/")
@access_for(Role.ADMIN)
async def employees_list(request: Request, db: AsyncSession = Depends(get_db)):
    query = request.query_params.get("q")

    stmt = select(Employee)
    if query:
        stmt = stmt.where(
            Employee.first_name.ilike(f"%{query}%") |
            Employee.last_name.ilike(f"%{query}%") |
            Employee.email.ilike(f"%{query}%") |
            Employee.phone.ilike(f"%{query}%")
        )

    result = await db.execute(stmt)
    employees = result.scalars().all()
    for emp in employees:
        emp.role_name = Role(emp.role).name
    return templates.TemplateResponse("employees.html", {
        "request": request,
        "employees": employees,
        "query": query
    })


@router.post("/{employee_id}/edit")
@access_for(Role.ADMIN)
async def edit_employee(
    employee_id: int,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    role: int = Form(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar_one_or_none()
    if employee:
        employee.first_name = first_name
        employee.last_name = last_name
        employee.email = email
        employee.role = role
        employee.phone = phone
        await db.commit()
    return RedirectResponse(url="/employees?success=1", status_code=303)


@router.post("/delete/{employee_id}")
@access_for()
async def delete_employee(employee_id: int, db: AsyncSession = Depends(get_db)):
    employee = await db.get(Employee, employee_id)
    if employee:
        await db.delete(employee)
        await db.commit()
    return RedirectResponse(url="/employees?success=1", status_code=303)


@router.post("/add")
@access_for()
async def add_employee(
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    role: int = Form(...),
    db: AsyncSession = Depends(get_db),
):
    hashed_password = bcrypt.hash(password)
    new_employee = Employee(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=hashed_password,
        role=role,
        phone=phone,
        created_at=datetime.now()
    )
    db.add(new_employee)
    await db.commit()
    return RedirectResponse(url="/employees?success=1", status_code=303)
