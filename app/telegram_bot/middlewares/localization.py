from aiogram.utils.i18n import I18n, FSMI18nMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import app_config
from app.db.session_wraper import with_session

from app.db.utils.user import get_user_language

I18N_DOMAIN = 'messages'
i18n = I18n(domain=I18N_DOMAIN, path=app_config.LOCALES_PATH)
_ = i18n.gettext


class LocalizationMiddleware(FSMI18nMiddleware):
    @with_session
    async def get_locale(self, event: TelegramObject, data: dict, session: AsyncSession) -> str:
        user = data.get('event_from_user')
        if not user:
            return 'en'

        # 🔹 Отримуємо мову з бази даних
        user_language = await get_user_language(session, user.id)

        # 🔹 Якщо мова не встановлена в БД, використовуємо мову Telegram
        language = user_language or user.language_code
        if language not in app_config.SUPPORTED_LANGUAGES:
            return app_config.DEFAULT_LANGUAGE
        return language


locale_middleware = LocalizationMiddleware(i18n=i18n)
