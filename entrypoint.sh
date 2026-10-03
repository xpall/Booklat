#!/bin/sh
set -eu

python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py seed_data
if [ "${DEMO_MODE:-0}" = "1" ]; then
    python manage.py seed_demo
fi

WORKERS=${GUNICORN_WORKERS:-3}

exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "$WORKERS" \
    --worker-class sync \
    --timeout 30 \
    --graceful-timeout 30 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile -
