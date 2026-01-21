FROM python:3.11-slim

WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY main.py .

# Создаем директорию для логов
RUN mkdir -p /app/logs

# Запуск приложения
CMD ["python", "main.py"]