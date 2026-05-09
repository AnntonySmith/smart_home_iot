# Используем официальный образ Python
FROM python:3.11-slim-buster

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /workspace

# Копируем файл с зависимостями и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Команда, которая выполнится при запуске контейнера
CMD ["python", "app.py"]
