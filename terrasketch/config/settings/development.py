"""
Development settings for TerraSketch project.
"""
from .base import *

# Development-specific settings
DEBUG = True

# Database for development (SQLite)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Development email backend (console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Allow all origins for development
CORS_ALLOW_ALL_ORIGINS = True

# Disable CSRF for development
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'http://localhost:5173',
    'http://127.0.0.1:3000',
    'http://127.0.0.1:5173',
]

# Development logging
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['terrasketch']['level'] = 'DEBUG'

# Django Debug Toolbar (if needed later)
INTERNAL_IPS = ['127.0.0.1', 'localhost']

# Development-specific apps
DEV_APPS = []
INSTALLED_APPS += DEV_APPS