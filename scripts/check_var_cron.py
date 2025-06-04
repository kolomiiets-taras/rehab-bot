import os
import sys
import asyncio

os.environ["POSTGRES_HOST"] = "localhost"

# Тепер імпортуємо config, щоб переконатися, що змінні оточення застосовані
from config import app_config
from logger import logger

# Перевіряємо, що URL змінився
logger.info(f"Підключення до бази даних: {app_config.SQLALCHEMY_DATABASE_URL}")
logger.info(f"Хост бази даних: {app_config.POSTGRES_HOST}")

# Імпортуємо необхідні модулі для роботи з базою даних
from sqlalchemy import select
from db.models.employee import Employee
from db.database import async_session


async def list_employees():
    """Отримати та показати список всіх працівників з бази даних."""
    try:
        async with async_session() as session:
            # Виконуємо запит до бази даних
            result = await session.execute(select(Employee))
            employees = result.scalars().all()

            if not employees:
                logger.info("У базі даних немає працівників.")
                return

            logger.info(f"\nЗнайдено {len(employees)} працівників:")
            logger.info("-" * 50)

            for emp in employees:
                logger.info(f"ID: {emp.id}")
                logger.info(f"Ім'я: {emp.first_name}")
                logger.info(f"Прізвище: {emp.last_name}")
                logger.info(f"Email: {emp.email}")
                logger.info(f"Роль: {emp.role}")
                logger.info("-" * 50)

            logger.info("Підключення до бази даних через localhost успішне!")

    except Exception as e:
        logger.warning(f"Помилка при отриманні даних: {e}")
        raise


if __name__ == "__main__":
    try:
        # Запускаємо асинхронну функцію
        asyncio.run(list_employees())
    except Exception as e:
        logger.warning(f"Критична помилка: {e}")
        sys.exit(1)