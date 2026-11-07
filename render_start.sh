#!/usr/bin/env bash
set -o errexit
set -o pipefail

python manage.py migrate --noinput

exec gunicorn nexalix_site.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers "${WEB_CONCURRENCY:-3}" --timeout "${GUNICORN_TIMEOUT:-120}"
