from fastapi import APIRouter, Request, Form, Response, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from .jwt_utils import create_access_token
from db.models import Employee
from sqlalchemy import select
from passlib.hash import bcrypt
from config import app_config
from .utils import error_handler
from db.database import get_db
from logger import logger

router = APIRouter()


@router.get("/login")
async def login_form(request: Request):
    return app_config.TEMPLATES.TemplateResponse("login/login.html", {"request": request})


@router.post("/login")
@error_handler('login')
async def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Employee).where(Employee.email == email))
    user = result.scalar_one_or_none()

    if not user or not bcrypt.verify(password, user.password):
        return app_config.TEMPLATES.TemplateResponse(
            "login/login.html", {"request": request, "error": "Невірний email або пароль"}, status_code=401
        )

    token = create_access_token({"sub": user.email})
    response = RedirectResponse("/users", status_code=302)
    response.set_cookie("access_token", token, httponly=True)
    logger.info(f"Employee {user.email} logged in successfully")
    return response


@router.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    employee = request.state.user
    logger.info(f"Employee {employee.email} logged out successfully")
    return response
