from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session_wraper import with_session
from db.models import User
from telegram_bot.keyboards.main_menu import main_menu_registration_keyboard, main_menu_keyboard
from telegram_bot.middlewares.localization import i18n
from telegram_bot.routers.utils import error_logger

router = Router(name=__name__)
_ = i18n.gettext


@router.message(CommandStart())
@error_logger
@with_session
async def start_handler(message: Message, session: AsyncSession) -> None:
    result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
    user = result.scalar_one_or_none()
    if user:
        await message.answer(
            _('start.welcome'), reply_markup=main_menu_keyboard(), parse_mode='HTML'
        )
        return

    await message.answer(
            _('start.welcome_new'), reply_markup=main_menu_registration_keyboard(), parse_mode='HTML'
        )
