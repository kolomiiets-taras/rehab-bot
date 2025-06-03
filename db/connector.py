from .database import Base, engine, async_session
from db.models import Employee, Role
from passlib.hash import bcrypt


async def create_db_and_tables() -> None:
    """Ініціалізація бази даних: створення таблиць."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def add_first_admin() -> None:
    async with async_session() as session:
        admin = Employee(
            first_name="Admin",
            last_name="Adminov",
            email="owner@owner.com",
            password=bcrypt.hash("1234"),
            role=Role.OWNER
        )
        session.add(admin)
        await session.commit()
        if await session.get(Employee, admin.id):
            print("Admin added successfully")


async def drop_db_tables() -> None:
    """❌ Видаляє всі таблиці в базі даних (для тестування)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
