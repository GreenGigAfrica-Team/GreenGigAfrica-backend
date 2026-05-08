from .base import *
import os

DEBUG = False
SECRET_KEY = os.environ['SECRET_KEY']
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

DEV_MODE = False

TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '')

# PostgreSQL from Railway or Supabase
# _db_host = os.environ.get('DB_HOST', '').strip()
# if _db_host:
#   DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'postgres'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': _db_host,
            'PORT': os.environ.get('DB_PORT', '5432'),
            'OPTIONS': {'sslmode': 'require'},
        }
    }
#else:
    # Railway provides DATABASE_URL automatically
    import dj_database_url
    DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=True,
    )
}
    
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
