import logging
from logging.handlers import TimedRotatingFileHandler
import os
from pathlib import Path
from config import app_config

# Визначаємо шлях для логів (з пріоритетом: змінна оточення > конфіг)
log_dir = os.environ.get('LOG_DIR', str(app_config.LOGS_PATH))
log_file = os.environ.get('LOG_FILE', 'backend.log')

# Створюємо директорію для логів, якщо вона не існує
try:
    os.makedirs(log_dir, exist_ok=True)
    log_file_path = os.path.join(log_dir, log_file)
except (PermissionError, OSError) as e:
    # Якщо не вдалося створити директорію логів, використовуємо директорію в домашньому каталозі
    fallback_dir = os.path.join(str(Path.home()), "rehab_logs")
    os.makedirs(fallback_dir, exist_ok=True)
    log_file_path = os.path.join(fallback_dir, log_file)
    print(f"Увага: не вдалося використати директорію {log_dir}, використовуємо {fallback_dir}")

# Налаштування форматувальника логів
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Створюємо логер
logger = logging.getLogger('rehab_bot_logger')
logger.setLevel(logging.INFO)

# Видаляємо існуючі обробники, щоб уникнути дублювання
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

try:
    # Обробник для запису логів у файл з ротацією
    file_handler = TimedRotatingFileHandler(
        filename=log_file_path,
        when='midnight',
        interval=1,
        backupCount=7,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
except (PermissionError, OSError) as e:
    print(f"Увага: не вдалося створити файловий обробник логів: {e}")

# Обробник для виводу логів у консоль
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Інформація про запуск логера
print(f'Логер запущено. Шлях до файлу: {log_file_path}')