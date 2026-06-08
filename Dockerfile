FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN groupadd -r booklat && useradd -r -g booklat booklat

RUN mkdir -p /app/staticfiles && chown -R booklat:booklat /app

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

USER booklat

CMD exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers ${GUNICORN_WORKERS:-2} \
    ${GUNICORN_THREADS:+--worker-class gthread --threads $GUNICORN_THREADS} \
    --access-logfile -