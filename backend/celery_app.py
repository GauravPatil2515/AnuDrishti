"""
Celery Configuration for Async Task Processing
==============================================
Handles long-running batch jobs and what-if optimizations asynchronously.
"""
import os
from celery import Celery

# Celery configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1')

celery_app = Celery('pharmaguard')
celery_app.conf.update(
    broker_url=CELERY_BROKER_URL,
    result_backend=CELERY_RESULT_BACKEND,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50,
    # Retry policy
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Result expiration
    result_expires=86400,  # 24 hours
)

# Auto-discover tasks
celery_app.autodiscover_tasks(['backend.tasks'])

if __name__ == '__main__':
    celery_app.start()