"""
Production settings for TerraSketch project.
"""
from .base import *
import dj_database_url

# Production settings
DEBUG = False

# Security settings for production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Database for production (PostgreSQL with PostGIS)
DATABASES = {
    'default': dj_database_url.parse(
        config('DATABASE_URL'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Ensure PostGIS is used in production
DATABASES['default']['ENGINE'] = 'django.contrib.gis.db.backends.postgis'

# File storage (Cloudflare R2)
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'

AWS_ACCESS_KEY_ID = CLOUDFLARE_R2_ACCESS_KEY
AWS_SECRET_ACCESS_KEY = CLOUDFLARE_R2_SECRET_KEY
AWS_STORAGE_BUCKET_NAME = CLOUDFLARE_R2_BUCKET
AWS_S3_ENDPOINT_URL = CLOUDFLARE_R2_ENDPOINT
AWS_S3_REGION_NAME = 'auto'
AWS_DEFAULT_ACL = None
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}

# Production logging
LOGGING['handlers']['file']['level'] = 'ERROR'
LOGGING['loggers']['django']['level'] = 'ERROR'
LOGGING['loggers']['terrasketch']['level'] = 'INFO'

# Sentry for error monitoring
SENTRY_DSN = config('SENTRY_DSN', default='')
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.celery import CeleryIntegration
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(),
            CeleryIntegration(),
        ],
        traces_sample_rate=0.1,
        send_default_pii=True
    )