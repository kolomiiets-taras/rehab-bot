from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.i18n import lazy_gettext as __
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from db.session_wraper import with_session
from logger import get_bot_logger

from db.models import User
from db.models.appointment import Appointment, AppointmentStatus
from telegram_bot.middlewares.localization import i18n
from telegram_bot.routers.utils import error_logger

router = Router(name=__name__)
_ = i18n.gettext

logger = get_bot_logger()


@router.message(F.text == __('keyboards.appointment'))
async def appointments_message(message: Message):
    await appointments_handler(message, message.from_user.id)


@router.callback_query(F.data == 'appointment_yes')
async def appointments_callback_yes(callback: CallbackQuery):
    await appointments_handler(callback.message, callback.from_user.id)
    await callback.message.delete()


@router.callback_query(F.data == 'appointment_no')
async def appointments_callback_no(callback: CallbackQuery):
    await callback.message.delete()


@error_logger
@with_session
async def appointments_handler(message: Message, user_id: int, session: AsyncSession):
    result = await session.execute(select(User).where(User.telegram_id == user_id))
    user = result.scalar_one_or_none()

    if user:
        filters = and_(
            Appointment.user_id == user.id,
            Appointment.status == AppointmentStatus.PENDING
        )
        app_result = await session.execute(select(Appointment).where(filters))
        pending_appointments = app_result.scalars().all()
        if not pending_appointments:
            appointment = Appointment(user_id=user.id)
            session.add(appointment)
            await session.commit()
            logger.info(f'New appointment created for user {user.telegram_id} ({user.id})')
            await message.answer(_('appointment.success'))
        else:
            await message.answer(_('appointment.already_exists'))
    else:
        logger.error(f'User {message.from_user.id} not found in the database')
