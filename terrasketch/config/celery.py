"""
Configuration Celery pour TerraSketch.
"""
import os
from celery import Celery
from django.conf import settings

# Set default Django settings module for 'celery' program
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")

app = Celery("terrasketch")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes
app.config_from_object("django.conf:settings", namespace="CELERY")

# Celery Configuration Options
app.conf.task_track_started = True
app.conf.task_serializer = "json"
app.conf.result_serializer = "json"
app.conf.accept_content = ["json"]
app.conf.result_expires = 60 * 60 * 24  # 24 hours
app.conf.timezone = "UTC"
app.conf.enable_utc = True

# Load task modules from all registered Django app configs
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
