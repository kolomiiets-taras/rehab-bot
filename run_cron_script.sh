#!/bin/bash
BASE_DIR="/home/dmytro_admin/rehab-bot"
SCRIPT_NAME=$1

if [ -z "$SCRIPT_NAME" ]; then
    echo "Помилка: не вказано назву скрипта"
    echo "Використання: $0 назва_скрипта"
    exit 1
fi

# Встановлюємо змінні оточення
export POSTGRES_HOST="localhost"

# Переходимо в директорію проєкту
cd "$BASE_DIR"
source venv/bin/activate

# Запускаємо скрипт
python -m "scripts.$SCRIPT_NAME"
EXIT_CODE=$?

deactivate
exit $EXIT_CODE