import logging
from logging.handlers import TimedRotatingFileHandler
import os
from pathlib import Path

# Глобальний кеш логерів
_loggers_cache = {}


def setup_logger(component_name: str, script_name: str = None) -> logging.Logger:
    """
    Налаштування логера для різних компонентів (з кешуванням)

    Args:
        component_name: 'bot', 'site', 'scripts'
        script_name: назва скрипта (тільки для scripts)
    """

    # Створюємо унікальний ключ для кешу
    if component_name == 'scripts' and script_name:
        cache_key = f'{component_name}_{script_name}'
        logger_name = cache_key
    else:
        cache_key = component_name
        logger_name = component_name

    # Перевіряємо чи вже є в кеші
    if cache_key in _loggers_cache:
        return _loggers_cache[cache_key]

    # Базова директорія логів
    base_log_dir = Path(os.environ.get('LOG_DIR', './logs'))

    # Визначаємо конкретну директорію
    if component_name == 'scripts' and script_name:
        log_dir = base_log_dir / 'scripts' / script_name
        log_file = f'{script_name}.log'
    else:
        log_dir = base_log_dir / component_name
        log_file = f'{component_name}.log'

    # Створюємо директорію з правами для всіх
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        # Встановлюємо права після створення
        import stat
        log_dir.chmod(stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)  # 755

        log_file_path = log_dir / log_file

        # Перевіряємо можливість запису
        test_file = log_dir / '.test_write'
        test_file.touch()
        test_file.unlink()

    except (PermissionError, OSError) as e:
        # Fallback до домашньої директорії
        fallback_dir = Path.home() / "rehab_logs" / component_name
        if script_name:
            fallback_dir = fallback_dir / script_name
        fallback_dir.mkdir(parents=True, exist_ok=True)
        log_file_path = fallback_dir / log_file
        print(f"Увага: використовуємо fallback директорію {fallback_dir}")

    # Налаштування форматування
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Створюємо або отримуємо існуючий логер
    logger = logging.getLogger(logger_name)

    # Перевіряємо чи логер вже налаштований
    if logger.handlers:
        _loggers_cache[cache_key] = logger
        return logger

    logger.setLevel(logging.INFO)

    # Файловий обробник з ротацією
    try:
        file_handler = TimedRotatingFileHandler(
            filename=str(log_file_path),
            when='midnight',
            interval=1,
            backupCount=7,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (PermissionError, OSError) as e:
        print(f"Помилка створення файлового обробника: {e}")

    # Консольний обробник
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Виводимо повідомлення тільки при першому створенні
    print(f'Логер {logger_name} налаштовано: {log_file_path}')

    # Зберігаємо в кеш
    _loggers_cache[cache_key] = logger
    return logger


# Логери для різних компонентів
def get_bot_logger():
    return setup_logger('bot')


def get_site_logger():
    return setup_logger('site')


def get_script_logger(script_name: str):
    return setup_logger('scripts', script_name)