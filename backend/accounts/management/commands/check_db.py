from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import EmailVerificationToken, VerifiedEmail
from subscriptions.models import Subscription


class Command(BaseCommand):
    def handle(self, *args, **options):
        User = get_user_model()
        self.stdout.write("=== USERS ===")
        for u in User.objects.all():
            self.stdout.write(f"  {u.username} | {u.email} | active={u.is_active} | staff={u.is_staff}")

        self.stdout.write("=== VERIFICATION TOKENS ===")
        for t in EmailVerificationToken.objects.all():
            self.stdout.write(f"  {t.user.username} | {t.email} | type={t.token_type} | used={t.is_used} | expired={t.is_expired()}")

        self.stdout.write("=== VERIFIED EMAILS ===")
        for v in VerifiedEmail.objects.all():
            self.stdout.write(f"  {v.user.username} | {v.email}")

        self.stdout.write("=== SUBSCRIPTIONS ===")
        for s in Subscription.objects.all():
            self.stdout.write(f"  {s.user.username} | {s.ticker} | {s.email} | active={s.is_active}")
