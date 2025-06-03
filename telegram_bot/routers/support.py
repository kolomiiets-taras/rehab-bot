from aiogram import Router, F
from aiogram.types import Message
from aiogram.utils.i18n import lazy_gettext as __

from telegram_bot.middlewares.localization import i18n
from telegram_bot.routers.utils import error_logger
from config import app_config

router = Router(name=__name__)
_ = i18n.gettext


@router.message(F.text == __('keyboards.support'))
@error_logger
async def support_handler(message: Message):
    await message.answer(_('support.message').format(support=app_config.SUPPORT_TAG))
