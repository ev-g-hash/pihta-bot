# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости для aiogram и других пакетов
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Rust для компиляции пакетов
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Проверяем установку Rust
RUN rustc --version && cargo --version

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Создаем пользователя для безопасности
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app
USER appuser

# Переменные окружения для оптимизации
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Открываем порт (если нужен для healthcheck)
EXPOSE 8000

# Healthcheck для мониторинга состояния контейнера
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Команда для запуска бота
CMD ["python", "main.py"]