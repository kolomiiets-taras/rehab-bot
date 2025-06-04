#!/bin/bash
BASE_DIR="/home/dmytro_admin/rehab-bot"
LOG_DIR="$BASE_DIR/cron_logs"
SCRIPT_NAME=$1  # Приймаємо назву скрипта як параметр

# Перевірка, чи передано назву скрипта
if [ -z "$SCRIPT_NAME" ]; then
    echo "Помилка: не вказано назву скрипта"
    echo "Використання: $0 назва_скрипта"
    exit 1
fi

# Створюємо директорію для логів, якщо вона не існує
mkdir -p "$LOG_DIR"

# Встановлюємо змінні оточення
export LOG_DIR="$LOG_DIR"
export LOG_FILE="${SCRIPT_NAME}.log"
export POSTGRES_HOST="localhost"

# Додаємо запис про початок виконання
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
echo "[$TIMESTAMP] Початок виконання скрипта $SCRIPT_NAME" >> "$LOG_DIR/bash_execution.log"

# Активуємо віртуальне середовище і запускаємо скрипт
cd "$BASE_DIR"
source venv/bin/activate

# Запускаємо скрипт з переданим ім'ям
python -m "scripts.$SCRIPT_NAME"
EXIT_CODE=$?

# Перевіряємо успішність виконання
if [ $EXIT_CODE -eq 0 ]; then
    STATUS="успішно завершено"
else
    STATUS="завершено з помилкою (код $EXIT_CODE)"
fi

# Деактивуємо віртуальне середовище
deactivate

# Додаємо запис про завершення виконання
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
echo "[$TIMESTAMP] Скрипт $SCRIPT_NAME $STATUS" >> "$LOG_DIR/bash_execution.log"

exit $EXIT_CODE