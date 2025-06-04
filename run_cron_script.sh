#!/bin/bash
BASE_DIR="/home/dmytro_admin/rehab-bot"
LOG_DIR="$BASE_DIR/cron_logs"
SCRIPT_NAME=$1  # Приймаємо назву скрипта як параметр

# Створюємо директорію, якщо вона не існує
mkdir -p $LOG_DIR

# Додаємо позначку часу для кращого логування
TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
echo "[$TIMESTAMP] Запуск скрипта $SCRIPT_NAME" >> $LOG_DIR/bash_execution.log

# Активуємо віртуальне середовище
cd $BASE_DIR
source venv/bin/activate

# Запускаємо скрипт
python -m scripts.$SCRIPT_NAME

# Деактивуємо віртуальне середовище
deactivate

echo "[$TIMESTAMP] Завершено виконання скрипта $SCRIPT_NAME" >> $LOG_DIR/bash_execution.log