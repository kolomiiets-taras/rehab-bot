from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.constants import WELLBEING_EMOJI_MAP
from app.telegram_bot.middlewares.localization import i18n
from app.config import app_config

_ = i18n.gettext


def skip_start_keyboard(session_id: int, locale: str = app_config.DEFAULT_LANGUAGE):
    builder = InlineKeyboardBuilder()
    builder.button(text=_('keyboards.start', locale=locale), callback_data=f'start_{session_id}')
    builder.button(text=_('keyboards.skip', locale=locale), callback_data=f'skip_{session_id}')
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
    for key, value in WELLBEING_EMOJI_MAP.items():
        builder.button(text=value, callback_data=f'wellbeing_{key}')
    builder.adjust(len(WELLBEING_EMOJI_MAP))
    return builder.as_markup()


