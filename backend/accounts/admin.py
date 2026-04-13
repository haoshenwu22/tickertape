from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import EmailVerificationToken, User, VerifiedEmail


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "is_staff", "date_joined")
    list_filter = ("is_staff", "is_active")


@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ("user", "email", "token_type", "is_used", "created_at")
    list_filter = ("token_type", "is_used")
    search_fields = ("user__username", "email", "token")
    readonly_fields = ("token", "created_at")


@admin.register(VerifiedEmail)
class VerifiedEmailAdmin(admin.ModelAdmin):
    list_display = ("user", "email")
    search_fields = ("user__username", "email")
