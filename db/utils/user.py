from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User


async def get_user_language(session: AsyncSession, telegram_id: int) -> str:
    """Отримує мову користувача з БД."""
    result = await session.execute(
        select(User.language).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()
