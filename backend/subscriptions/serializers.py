from rest_framework import serializers

from .models import Subscription


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ("id", "ticker", "email", "is_active", "created_at")
        read_only_fields = ("id", "is_active", "created_at")

    def validate_ticker(self, value):
        return value.upper().strip()
