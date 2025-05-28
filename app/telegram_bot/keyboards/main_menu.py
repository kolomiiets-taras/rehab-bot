from aiogram.utils.keyboard import ReplyKeyboardBuilder
from app.telegram_bot.middlewares.localization import i18n
from app.config import app_config

_ = i18n.gettext


def main_menu_registration_keyboard(locale: str = app_config.DEFAULT_LANGUAGE):
    builder = ReplyKeyboardBuilder()
    builder.button(text=_('keyboards.registration', locale=locale))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)


def main_menu_appointment_keyboard(locale: str = app_config.DEFAULT_LANGUAGE):
    builder = ReplyKeyboardBuilder()
    builder.button(text=_('keyboards.appointment', locale=locale))
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)
