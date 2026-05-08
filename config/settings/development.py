from .base import *
import os

DEBUG = True
SECRET_KEY = 'django-insecure-dev-key-greengig-africa-2026'
ALLOWED_HOSTS = ['*']

DEV_MODE = True

TWILIO_ACCOUNT_SID = ''
TWILIO_AUTH_TOKEN = ''
TWILIO_PHONE_NUMBER = ''

# ── CORS ──────────────────────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# ── Database ──────────────────────────────────────────────────────────────────
_database_url = os.environ.get('DATABASE_URL', '').strip()

if _database_url:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            default=_database_url,
            conn_max_age=600,
            ssl_require=True,
        )
    }
    print(f'[DB] Using PostgreSQL via DATABASE_URL')
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    print('[DB] Using SQLite (local)')
