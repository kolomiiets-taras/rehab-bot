from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db.database import get_db
from logger import logger
from db.models import MotivationMessage, Role
from config import app_config
from backend.routers.utils import access_for, error_handler

router = APIRouter(prefix="/motivation")
templates = app_config.TEMPLATES


@router.get("/")
@access_for(Role.ADMIN)
async def list_messages(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MotivationMessage))
    messages = result.scalars().all()
    return templates.TemplateResponse("motivation/motivations.html", {"request": request, "messages": messages})


@router.post("/add")
@access_for(Role.ADMIN)
@error_handler('motivation')
async def create_message(request: Request, message: str = Form(...), db: AsyncSession = Depends(get_db)):
    msg = MotivationMessage(message=message)
    db.add(msg)
    await db.commit()
    logger.info(f"Added new motivation message: {message}")
    return RedirectResponse(url="/motivation?success=1", status_code=303)


@router.post("/edit/{message_id}")
@access_for(Role.ADMIN)
@error_handler('motivation')
async def update_message(request: Request, message_id: int, message: str = Form(...), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MotivationMessage).where(MotivationMessage.id == message_id))
    msg = result.scalar_one_or_none()
    if msg:
        msg.message = message
        await db.commit()
        logger.info(f"Updated motivation message ID {message_id}")
        return RedirectResponse(url="/motivation?success=1", status_code=303)
    logger.error(f"Motivation message not found ID {message_id}")
    return RedirectResponse(url="/motivation?error=1", status_code=303)


@router.post("/delete/{message_id}")
@access_for(Role.ADMIN)
@error_handler('motivation')
async def delete_message(request: Request, message_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MotivationMessage).where(MotivationMessage.id == message_id))
    msg = result.scalar_one_or_none()
    if msg:
        await db.delete(msg)
        await db.commit()
        logger.info(f"Deleted motivation message ID {message_id}")
        return RedirectResponse(url="/motivation?success=1", status_code=303)
    logger.error(f"Motivation message not found ID {message_id}")
    return RedirectResponse(url="/motivation?error=1", status_code=303)
