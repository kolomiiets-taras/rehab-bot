from aiogram import Router, F
from aiogram.types import Message
from aiogram.utils.i18n import lazy_gettext as __
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session_wraper import with_session
from app.models import User
from app.models.appointment import Appointment, AppointmentStatus
from app.telegram_bot.middlewares.localization import i18n


router = Router(name=__name__)
_ = i18n.gettext


@router.message(F.text == __('keyboards.appointment'))
@with_session
async def appointments_handler(message: Message, session: AsyncSession):
    result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
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
            await message.answer(_('appointment.success'))
        else:
            await message.answer(_('appointment.already_exists'))
