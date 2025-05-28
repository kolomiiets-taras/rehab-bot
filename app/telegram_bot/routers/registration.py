from datetime import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session_wraper import with_session
from app.models import User
from app.telegram_bot.keyboards.main_menu import main_menu_appointment_keyboard
from app.telegram_bot.middlewares.localization import i18n
from aiogram.utils.i18n import lazy_gettext as __


router = Router(name=__name__)
_ = i18n.gettext


class Registration(StatesGroup):
    phone = State()
    first_name = State()
    last_name = State()
    birthday = State()


@router.message(F.text == __('keyboards.registration'))
@with_session
async def registration_handler(message: Message, state: FSMContext, session: AsyncSession) -> None:
    result = await session.execute(select(User).where(User.telegram_id == message.from_user.id))
    user = result.scalar_one_or_none()
    if user:
        await message.answer(_('registration.already_registered'))
        return

    await message.answer(_('registration.phone_number'))
    await state.set_state(Registration.phone)


@router.message(Registration.phone)
async def get_phone(message: Message, state: FSMContext) -> None:
    await state.update_data(phone=message.text)
    await message.answer(_('registration.first_name'))
    await state.set_state(Registration.first_name)


@router.message(Registration.first_name)
async def get_first_name(message: Message, state: FSMContext) -> None:
    await state.update_data(first_name=message.text)
    await message.answer(_('registration.last_name'))
    await state.set_state(Registration.last_name)


@router.message(Registration.last_name)
async def get_last_name(message: Message, state: FSMContext) -> None:
    await state.update_data(last_name=message.text)
    await message.answer(_('registration.birth_date'))
    await state.set_state(Registration.birthday)


@router.message(Registration.birthday)
@with_session
async def get_birthday(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        birthday = datetime.strptime(message.text, '%d.%m.%Y').date()
    except ValueError:
        await message.answer(_('registration.error'))
        return

    data = await state.get_data()
    user = User(
        telegram_id=message.from_user.id,
        phone=data['phone'],
        first_name=data['first_name'],
        last_name=data['last_name'],
        birthday=birthday
    )
    session.add(user)
    await session.commit()

    await message.answer(_('registration.success'), reply_markup=main_menu_appointment_keyboard())
    await state.clear()
