import uuid

from django.conf import settings
from django.db import models


class PriceAlert(models.Model):
    CONDITION_CHOICES = [
        ("above", "Above"),
        ("below", "Below"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alerts")
    ticker = models.CharField(max_length=10)
    target_price = models.DecimalField(max_digits=12, decimal_places=2)
    condition = models.CharField(max_length=5, choices=CONDITION_CHOICES)
    is_triggered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    triggered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.ticker} {self.condition} ${self.target_price}"
