FROM python:alpine

WORKDIR /app_telebot

COPY . .

RUN pip install -r requirements.txt

ENTRYPOINT ["python", "main.py"]
