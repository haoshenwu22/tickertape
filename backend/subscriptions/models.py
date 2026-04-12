import uuid

from django.conf import settings
from django.db import models


class Subscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscriptions")
    ticker = models.CharField(max_length=10)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "ticker", "email")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.ticker} → {self.email}"
