import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("tickertape")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.conf.timezone = "America/New_York"
app.autodiscover_tasks()

# Periodic task schedule
app.conf.beat_schedule = {
    "send-stock-price-emails": {
        "task": "notifications.tasks.send_periodic_emails",
        "schedule": crontab(minute=0, hour="9-17", day_of_week="1-5"),
    },
    "check-price-alerts": {
        "task": "alerts.tasks.check_price_alerts",
        "schedule": crontab(minute="*/15"),
    },
}
