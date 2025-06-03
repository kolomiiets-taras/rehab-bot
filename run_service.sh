#!/bin/bash
set -e  # Зупинка при помилках

echo "SERVICE_TYPE: $SERVICE_TYPE"

if [ "$SERVICE_TYPE" = "bot" ]; then
    echo "Starting Telegram Bot..."
    python -m telegram_bot
elif [ "$SERVICE_TYPE" = "api" ]; then
    echo "Starting FastAPI application..."
    python -m backend
else
    echo "ERROR: Unknown SERVICE_TYPE: $SERVICE_TYPE"
    echo "Available options: 'api' for FastAPI or 'bot' for Telegram Bot"
    exit 1
fi