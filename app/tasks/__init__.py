from app.tasks.celery_app import celery_app
from app.tasks.test_tasks import test_task

__all__ = ["celery_app", "test_task"]
