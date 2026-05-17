from .base import *
import os

DEBUG = True
SECRET_KEY = 'django-insecure-dev-key-greengig-africa-2026'
ALLOWED_HOSTS = ['*']

DEV_MODE = True

# ── Load .env file ────────────────────────────────────────────────────────────
import environ
env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

# ── Termii SMS ────────────────────────────────────────────────────────────────
TERMII_API_KEY = env('TERMII_API_KEY', default='')
TERMII_SENDER_ID = env('TERMII_SENDER_ID', default='GreenGig')

# ── Twilio SMS ────────────────────────────────────────────────────────────────
TWILIO_ACCOUNT_SID = env('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = env('TWILIO_AUTH_TOKEN', default='')
TWILIO_PHONE_NUMBER = env('TWILIO_PHONE_NUMBER', default='')

# ── Africa's Talking SMS ──────────────────────────────────────────────────────
AT_USERNAME = env('AT_USERNAME', default='')
AT_API_KEY = env('AT_API_KEY', default='')

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

# ── Logging — print everything to console ────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'apps.accounts': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
