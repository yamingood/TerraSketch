"""
Configuration PostgreSQL avec PostGIS pour TerraSketch
"""
from .base import *
from decouple import config

# Base de données PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': config('DB_NAME', default='terrasketch_db'),
        'USER': config('DB_USER', default='terrasketch_user'),
        'PASSWORD': config('DB_PASSWORD', default='terrasketch_pass'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'OPTIONS': {
            'charset': 'utf8',
        },
    }
}

# Applications PostGIS
INSTALLED_APPS += [
    'django.contrib.gis',
]

# Cache Redis pour production
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.backends.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Session Redis
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Configuration Celery
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# Configuration GDAL/GEOS (nécessaire pour PostGIS sur macOS)
import os
if os.path.exists('/usr/local/lib'):
    GDAL_LIBRARY_PATH = '/usr/local/lib/libgdal.dylib'
    GEOS_LIBRARY_PATH = '/usr/local/lib/libgeos_c.dylib'
elif os.path.exists('/opt/homebrew/lib'):
    GDAL_LIBRARY_PATH = '/opt/homebrew/lib/libgdal.dylib'
    GEOS_LIBRARY_PATH = '/opt/homebrew/lib/libgeos_c.dylib'

# Logging pour la production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'terrasketch': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Créer le dossier des logs s'il n'existe pas
LOG_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Security settings pour la production
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Configuration CORS pour la production
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    "https://terrasketch.vercel.app",
    "https://app.terrasketch.com",
]

if DEBUG:
    CORS_ALLOWED_ORIGINS += [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]