import logging
from logging.handlers import TimedRotatingFileHandler
import os
from .config import app_config

# Создаём директорию для логов, если она не существует
os.makedirs(app_config.LOGS_PATH, exist_ok=True)
log_file_path = os.path.join(app_config.LOGS_PATH, 'app.log')

# Настройка форматировщика логов
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Создаём логгер
logger = logging.getLogger('rehab_bot_logger')
logger.setLevel(logging.INFO)  # можно установить уровень DEBUG, если нужно больше деталей

# Обработчик для записи логов в файл с ежедневной ротацией в 00:00 и хранением за 7 дней
file_handler = TimedRotatingFileHandler(
    filename=log_file_path,
    when='midnight',          # Ротация в полночь
    interval=1,               # Интервал - один день
    backupCount=7,            # Хранить файлы за последние 7 дней
    encoding='utf-8'
)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Обработчик для вывода логов в консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Пример использования логгера
logger.info('Logger started')
