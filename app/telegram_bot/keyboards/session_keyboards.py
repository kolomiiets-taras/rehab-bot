from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.constants import WELLNESS_EMOJI_MAP
from app.telegram_bot.middlewares.localization import i18n

_ = i18n.gettext


def skip_start_keyboard(session_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text=_('keyboards.start'), callback_data=f'start_{session_id}')
    builder.button(text=_('keyboards.skip'), callback_data=f'skip_{session_id}')
    builder.adjust(1)
    return builder.as_markup()


def next_step_keyboard(session_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text=_('keyboards.next'), callback_data=f'next_{session_id}')
    builder.adjust(1)
    return builder.as_markup()


def finish_keyboard(session_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text=_('keyboards.finish'), callback_data=f'finish_{session_id}')
    builder.adjust(1)
    return builder.as_markup()


def wellbeing_keyboard():
    builder = InlineKeyboardBuilder()
    for key, value in WELLNESS_EMOJI_MAP.items():
        builder.button(text=value, callback_data=f'wellbeing_{key}')
    builder.adjust(len(WELLNESS_EMOJI_MAP))
    return builder.as_markup()


