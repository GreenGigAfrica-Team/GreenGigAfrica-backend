web: DJANGO_SETTINGS_MODULE=config.settings.production gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
release: DJANGO_SETTINGS_MODULE=config.settings.production python manage.py migrate
