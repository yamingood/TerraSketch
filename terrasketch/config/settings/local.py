"""
Settings pour développement local avec PostgreSQL
"""
from .base import *

# Base de données PostgreSQL locale
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='terrasketch_dev'),
        'USER': config('DB_USER', default='terrasketch'),
        'PASSWORD': config('DB_PASSWORD', default='terrasketch123'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'options': '-c default_transaction_isolation=read_committed'
        }
    }
}

# Redis local pour Celery
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Cache Redis local
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Logs plus détaillés en développement
LOGGING['loggers']['terrasketch']['level'] = 'DEBUG'
# Configuration safe pour django.db.backends
if 'django.db.backends' in LOGGING['loggers']:
    LOGGING['loggers']['django.db.backends']['level'] = 'DEBUG'

# CORS permissif pour développement
CORS_ALLOW_ALL_ORIGINS = True

DEBUG = True