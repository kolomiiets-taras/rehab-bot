import random

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db import Complex, ComplexExercise
from db.session_wraper import with_session
from db.models import DailySession, CourseItem, UserCourse, Course, DailySessionState, MotivationMessage
from telegram_bot.keyboards.session_keyboards import wellbeing_keyboard, yes_no_keyboard
from telegram_bot.middlewares.localization import i18n
from telegram_bot.routers.utils import validate_pulse, finish_session, error_logger
from telegram_bot.utils import send_exercise, clean_html_for_telegram

router = Router(name=__name__)
_ = i18n.gettext


class Session(StatesGroup):
    pulse_before = State()
    pulse_after = State()
    wellbeing_before = State()
    wellbeing_after = State()
    exercise = State()
    course_finishing = State()


@router.callback_query(F.data.startswith("start_"))
@error_logger
@with_session
async def start_session_handler(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    session_id = int(callback.data.split('_')[1])
    result = await session.execute(
        select(DailySession)
        .where(DailySession.id == session_id)
        .options(
            selectinload(DailySession.user_course)
            .selectinload(UserCourse.course)
            .selectinload(Course.items)
            .selectinload(CourseItem.exercise),

            selectinload(DailySession.user_course)
            .selectinload(UserCourse.course)
            .selectinload(Course.items)
            .selectinload(CourseItem.complex)
            .selectinload(Complex.exercises)
            .selectinload(ComplexExercise.exercise)
        )
    )
    daily_session = result.scalar_one_or_none()

    exercises = []
    for item in daily_session.user_course.course.items:
        if item.is_exercise:
            exercises.append(item.exercise)
        elif item.is_complex:
            exercises.extend([ex.exercise for ex in item.complex.exercises])

    if daily_session:
        daily_session.state = DailySessionState.IN_PROGRESS
        await state.update_data(exercises=exercises)
        await state.update_data(daily_session=daily_session)
        await state.set_state(Session.pulse_before)
        await callback.message.delete()
        session.add(daily_session)
        await session.commit()
        await callback.message.answer(_('session.pulse'))
        return

    await callback.message.answer(_('error.general'))


@router.callback_query(F.data.startswith("skip_"))
@error_logger
@with_session
async def skip_session_handler(callback: CallbackQuery, session: AsyncSession) -> None:
    session_id = int(callback.data.split('_')[1])
    result = await session.execute(
        select(DailySession)
        .where(DailySession.id == session_id)
        .options(
            selectinload(DailySession.user_course)
            .selectinload(UserCourse.course)
            .selectinload(Course.items)
        )
    )
    daily_session = result.scalar_one_or_none()
    if daily_session:
        finished = await finish_session(daily_session, session, skipped=True)
        await callback.message.delete()
        await callback.message.answer(_('session.skipped'))
        if finished:
            await callback.message.answer(
                _('session.course_finishing').format(course_title=daily_session.user_course.course.name),
                reply_markup=yes_no_keyboard()
            )
        return

    await callback.message.answer(_('session.not_found'))


@router.message(Session.pulse_before)
@error_logger
@with_session
async def pulse_before_handler(message: Message, state: FSMContext, session: AsyncSession) -> None:
    pulse = message.text
    if not validate_pulse(pulse):
        await message.answer(_("session.pulse"))
        return

    pulse = int(pulse)
    data = await state.get_data()
    daily_session = data.get("daily_session")

    if daily_session is None:
        await message.answer(_('error.general'))
        await state.clear()
        return

    daily_session.pulse_before = pulse
    await message.answer(_('session.pulse_saved'))
    await state.set_state(Session.wellbeing_before)
    await message.answer(_('session.wellbeing'), reply_markup=wellbeing_keyboard())

    session.add(daily_session)
    await session.commit()


@router.callback_query(Session.wellbeing_before, F.data.startswith("wellbeing_"))
@error_logger
@with_session
async def wellbeing_before_handler(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    parts = callback.data.split("_")
    if len(parts) != 2:
        await callback.answer(_('error.general'), show_alert=True)
        return

    try:
        wellbeing_value = int(parts[1])
    except ValueError:
        await callback.answer(_('error.general'), show_alert=True)
        return

    data = await state.get_data()
    daily_session = data.get("daily_session")
    if not daily_session:
        await callback.message.answer(_('session.not_found'))
        await state.clear()
        return

    daily_session.wellbeing_before = wellbeing_value
    await callback.message.answer(_('session.wellbeing_saved'))

    await state.set_state(Session.exercise)
    first_exercise = data["exercises"][0]
    await send_exercise(
        message=callback.message,
        session_id=daily_session.id,
        title=first_exercise.title,
        text=first_exercise.text,
        media=first_exercise.media,
        last=len(data["exercises"]) == 1
    )
    await state.update_data(current_index=0)

    session.add(daily_session)
    await session.commit()
    await callback.answer()


@router.callback_query(Session.exercise, F.data.startswith("next_"))
@error_logger
@with_session
async def next_exercise_handler(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    await callback.message.delete()
    data = await state.get_data()
    exercises = data.get("exercises", [])
    index = data.get("current_index", 0) + 1

    await state.update_data(current_index=index)
    exercise = exercises[index]
    last = index == len(exercises) - 1

    motivation_result = await session.execute(select(MotivationMessage))
    motivation_messages = motivation_result.scalars().all()
    if motivation_messages and last:
        motivation_message = random.choice(motivation_messages)
        message = await callback.message.answer(clean_html_for_telegram(motivation_message.message))
        motivation = data.get("motivation", [])
        motivation.append(message)
        await state.update_data(motivation=motivation)

    await send_exercise(
        callback.message,
        session_id=int(callback.data.split("_")[1]),
        title=exercise.title,
        text=exercise.text,
        media=exercise.media,
        last=last
    )
    await callback.answer()


@router.callback_query(Session.exercise, F.data.startswith("finish_"))
@error_logger
async def finish_exercises(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    for msg in data.get("motivation", []):
        await msg.delete()

    await state.set_state(Session.pulse_after)
    await callback.message.delete()
    await callback.message.answer(_('session.pulse'))
    await callback.answer()


@router.message(Session.pulse_after)
@error_logger
@with_session
async def pulse_after_handler(message: Message, state: FSMContext, session: AsyncSession) -> None:
    pulse = message.text
    if not validate_pulse(pulse):
        await message.answer(_("session.pulse"))
        return

    pulse = int(pulse)
    data = await state.get_data()
    daily_session = data.get("daily_session")

    if daily_session is None:
        await message.answer(_('error.general'))
        await state.clear()
        return

    daily_session.pulse_after = pulse
    await message.answer(_('session.pulse_saved'))
    await state.set_state(Session.wellbeing_after)
    await message.answer(_('session.wellbeing'), reply_markup=wellbeing_keyboard())

    session.add(daily_session)
    await session.commit()


@router.callback_query(Session.wellbeing_after, F.data.startswith("wellbeing_"))
@error_logger
@with_session
async def wellbeing_after_handler(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    parts = callback.data.split("_")
    if len(parts) != 2:
        await callback.answer(_('error.general'), show_alert=True)
        return

    try:
        wellbeing_value = int(parts[1])
    except ValueError:
        await callback.answer(_('error.general'), show_alert=True)
        return

    data = await state.get_data()
    daily_session = data.get("daily_session")
    if not daily_session:
        await callback.message.answer(_('session.not_found'))
        await state.clear()
        return

    daily_session.wellbeing_after = wellbeing_value
    await callback.message.answer(_('session.wellbeing_saved'))
    await callback.message.answer(_('session.finished'))

    finished = await finish_session(daily_session, session, skipped=False)

    if finished:
        await callback.message.answer(
            _('session.course_finishing').format(course_title=daily_session.user_course.course.name),
            reply_markup=yes_no_keyboard()
        )

    await state.clear()
    await callback.answer()
