from fastapi import APIRouter, Request, Form, Response
from fastapi.responses import RedirectResponse
from .jwt_utils import create_access_token
from app.db import async_session
from app.models import Employee
from sqlalchemy import select
from passlib.hash import bcrypt
from app.config import app_config

router = APIRouter()


@router.get("/login")
async def login_form(request: Request):
    return app_config.TEMPLATES.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login_submit(request: Request, email: str = Form(...), password: str = Form(...)):
    async with async_session() as session:
        result = await session.execute(select(Employee).where(Employee.email == email))
        user = result.scalar_one_or_none()

        if not user or not bcrypt.verify(password, user.password):
            return app_config.TEMPLATES.TemplateResponse(
                "login.html", {"request": request, "error": "Невірний email або пароль"}, status_code=401
            )

        token = create_access_token({"sub": user.email})
        response = RedirectResponse("/users", status_code=302)
        response.set_cookie("access_token", token, httponly=True)
        return response


@router.get("/logout")
async def logout(response: Response):
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("access_token")
    return response
