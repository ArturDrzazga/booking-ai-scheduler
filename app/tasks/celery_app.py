from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "booking_tasks", broker=settings.REDIS_URL, backend=settings.REDIS_URL
)

celery_app.autodiscover_tasks(["app.tasks"])

celery_app.conf.beat_schedule = {
    "send-reminders-daily": {
        "task": "app.tasks.email_tasks.send_reminders_for_tomorrow",
        "schedule": crontab(hour=9, minute=0)
    }
}
