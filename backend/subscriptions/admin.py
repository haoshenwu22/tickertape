from django.contrib import admin

from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("ticker", "email", "user", "created_at")
    list_filter = ("ticker", "user")
    search_fields = ("ticker", "email", "user__username")
