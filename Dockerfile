FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN apt-get update && apt-get upgrade -y && apt-get clean

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

CMD ["python", "bot.py"]