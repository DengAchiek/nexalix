release: python manage.py migrate && python manage.py collectstatic --noinput
web: gunicorn nexalix_site.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120
