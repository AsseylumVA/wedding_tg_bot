FROM python:3.12
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir
RUN mkdir -p /app/var/log && chmod 777 /app/var/log
COPY . .
CMD ["python3", "aiogram_run.py"]