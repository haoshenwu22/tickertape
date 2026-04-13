import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

FRONTEND_URL = getattr(settings, "FRONTEND_URL", "http://localhost:5173")


@shared_task
def send_verification_email_task(username, email, token, token_type):
    """Send verification email asynchronously via Celery."""
    verification_url = f"{FRONTEND_URL}/verify-email?token={token}"

    if token_type == "registration":
        subject = "TickerTape: Verify Your Email Address"
        message_text = (
            "Thanks for registering with TickerTape! "
            "Please verify your email address to activate your account."
        )
    else:
        subject = "TickerTape: Verify Your Subscription Email"
        message_text = (
            f"Please verify that you own the email address {email} "
            "to activate your stock subscriptions."
        )

    html_message = render_to_string(
        "accounts/verification_email.html",
        {
            "user": {"username": username},
            "email": email,
            "verification_url": verification_url,
            "message_text": message_text,
            "token_type": token_type,
        },
    )

    plain_message = (
        f"TickerTape Email Verification\n\n"
        f"{message_text}\n\n"
        f"Click the link below to verify your email:\n"
        f"{verification_url}\n\n"
        f"This link will expire in 24 hours."
    )

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
        )
        logger.info(f"Verification email sent to {email} (type={token_type})")
    except Exception as e:
        logger.error(f"Failed to send verification email to {email}: {e}")
