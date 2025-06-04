# Базовий образ
FROM python:3.12-slim

# Встановлення системних залежностей
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    libpq-dev \
    gettext \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Робоча директорія
WORKDIR /app

# Копіювання залежностей
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копіювання проєкту
COPY . .

# Компіляція мовних файлів
RUN pybabel compile -d telegram_bot/locales --use-fuzzy

# Змінні середовища для Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app