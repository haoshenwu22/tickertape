from rest_framework import serializers

from .models import PriceAlert


class PriceAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceAlert
        fields = ("id", "ticker", "target_price", "condition", "is_triggered", "created_at", "triggered_at")
        read_only_fields = ("id", "is_triggered", "created_at", "triggered_at")

    def validate_ticker(self, value):
        return value.upper().strip()
