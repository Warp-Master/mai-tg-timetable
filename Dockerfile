FROM python:3.11-alpine
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV MUSL_LOCPATH /usr/share/i18n/locales/musl

RUN apk add --no-cache tzdata musl-locales

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py .
COPY templates ./templates/

ENTRYPOINT ["python", "main.py"]
