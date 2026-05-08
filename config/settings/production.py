from .base import *
import os
import dj_database_url

DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-in-production')
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

DEV_MODE = False

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')

# Africa's Talking SMS
AT_USERNAME = os.environ.get('AT_USERNAME', '')
AT_API_KEY = os.environ.get('AT_API_KEY', '')

# Termii SMS (free tier, works in Nigeria + Ethiopia)
TERMII_API_KEY = os.environ.get('TERMII_API_KEY', '')

# ── Database ──────────────────────────────────────────────────────────────────
# Django reads DATABASE_URL environment variable automatically
# Railway sets this automatically when you add a PostgreSQL database
# Supabase: set DATABASE_URL=postgresql://postgres:password@host:5432/postgres
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=True,
    )
}

# ── CORS ──────────────────────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# ── Static files ──────────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
