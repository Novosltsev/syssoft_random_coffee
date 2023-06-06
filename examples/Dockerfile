FROM python:3.10

WORKDIR /app

COPY libs.txt .

RUN pip install --no-cache-dir -r libs.txt

COPY . .

CMD ["python", "manage.py migrate"]
CMD ["python", "manage.py runserver"]
CMD ["python", "main.py"]
