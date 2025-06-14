"""Celery application instance configuration."""
import os

from celery import Celery

# Configure Redis broker and backend URL from environment or default
redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
celery = Celery('celery_app', broker=redis_url, backend=redis_url, include=['tasks'])
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

from flask_app import app as flask_app

class ContextTask(celery.Task):
    abstract = True
    def __call__(self, *args, **kwargs):
        with flask_app.app_context():
            return super(ContextTask, self).__call__(*args, **kwargs)

celery.Task = ContextTask