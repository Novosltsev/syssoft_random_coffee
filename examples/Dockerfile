# Устанавливаем базовый образ
FROM python:3.10

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем зависимости в контейнер
COPY libs.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r libs.txt

# Копируем исходный код в контейнер
COPY . .

# Запускаем команду для запуска сервера и для запуска бота
CMD ["python", "admin/manage.py", "runserver", "&", "python", "main.py"]
