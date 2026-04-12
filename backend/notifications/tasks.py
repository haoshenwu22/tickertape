import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def send_periodic_emails():
    """Periodic task: send merged stock price emails to all subscribers."""
    from .services import send_merged_emails
    logger.info("Starting periodic email send...")
    send_merged_emails()
    logger.info("Periodic email send complete.")
