#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py seed_data

WORKERS=${GUNICORN_WORKERS:-2}
THREADS=${GUNICORN_THREADS:-}

GUNICORN_ARGS="--bind 0.0.0.0:8000 --workers $WORKERS --access-logfile -"

if [ -n "$THREADS" ]; then
    GUNICORN_ARGS="$GUNICORN_ARGS --worker-class gthread --threads $THREADS"
fi

exec gunicorn config.wsgi:application $GUNICORN_ARGS