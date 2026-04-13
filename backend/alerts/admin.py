from django.contrib import admin

from .models import PriceAlert


@admin.register(PriceAlert)
class PriceAlertAdmin(admin.ModelAdmin):
    list_display = ("ticker", "target_price", "condition", "is_triggered", "user", "created_at")
    list_filter = ("condition", "is_triggered")
    search_fields = ("ticker", "user__username")
