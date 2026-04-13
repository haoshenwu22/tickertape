import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """Custom user model. Uses Django's built-in is_staff as the admin flag."""

    class Meta:
        ordering = ["-date_joined"]


class EmailVerificationToken(models.Model):
    TOKEN_TYPE_CHOICES = [
        ("registration", "Registration"),
        ("subscription_email", "Subscription Email"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="verification_tokens",
    )
    email = models.EmailField()
    token = models.CharField(max_length=64, unique=True, default=uuid.uuid4)
    token_type = models.CharField(max_length=20, choices=TOKEN_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        return timezone.now() - self.created_at > timezone.timedelta(hours=24)

    def save(self, *args, **kwargs):
        if not self.token or self.token == "":
            self.token = uuid.uuid4().hex
        elif hasattr(self.token, "hex"):
            # Convert UUID to hex string if default generated a UUID object
            self.token = self.token.hex
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.token_type} token for {self.email}"


class VerifiedEmail(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="verified_emails",
    )
    email = models.EmailField()

    class Meta:
        unique_together = ("user", "email")

    def __str__(self):
        return f"{self.user.username} - {self.email}"
