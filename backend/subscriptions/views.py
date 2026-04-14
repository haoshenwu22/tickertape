from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import VerifiedEmail
from notifications.services import send_stock_email_for_subscription
from stocks.services import validate_ticker

from .models import Subscription
from .serializers import SubscriptionSerializer


def _user_subscriptions(user):
    """Get subscriptions visible to a user: their own + any targeting their verified emails."""
    verified_emails = VerifiedEmail.objects.filter(user=user).values_list("email", flat=True)
    return Subscription.objects.filter(
        Q(user=user) | Q(email__in=verified_emails)
    ).distinct()


class SubscriptionListCreateView(generics.ListCreateAPIView):
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return Subscription.objects.all()
        return _user_subscriptions(self.request.user)

    def perform_create(self, serializer):
        from django.db import IntegrityError
        from rest_framework.exceptions import ValidationError

        from accounts.models import EmailVerificationToken, VerifiedEmail
        from accounts.views import send_verification_email

        ticker = serializer.validated_data["ticker"]
        if not validate_ticker(ticker):
            raise ValidationError({"ticker": f"'{ticker}' is not a valid stock symbol."})

        user = self.request.user
        email = serializer.validated_data["email"]

        # Admin users: no verification needed
        if user.is_staff:
            try:
                serializer.save(user=user, is_active=True)
            except IntegrityError:
                raise ValidationError(
                    {"detail": f"You already have a subscription for {ticker} with this email address."}
                )
            return

        # Regular users: check if email is verified
        is_verified = VerifiedEmail.objects.filter(user=user, email=email).exists()

        try:
            subscription = serializer.save(user=user, is_active=is_verified)
        except IntegrityError:
            raise ValidationError(
                {"detail": f"You already have a subscription for {ticker} with this email address."}
            )

        if not is_verified:
            # Create verification token and send email
            token = EmailVerificationToken.objects.create(
                user=user,
                email=email,
                token_type="subscription_email",
            )
            send_verification_email(user, email, token.token, "subscription_email")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get("email", "")
        user = request.user

        self.perform_create(serializer)

        response_data = serializer.data

        # Check if verification was needed
        if not user.is_staff:
            from accounts.models import VerifiedEmail

            is_verified = VerifiedEmail.objects.filter(user=user, email=email).exists()
            if not is_verified:
                response_data["verification_needed"] = True
                response_data["message"] = (
                    f"A verification email has been sent to {email}. "
                    "Please verify to activate this subscription."
                )

        headers = self.get_success_headers(serializer.data)
        return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)


class SubscriptionDeleteView(generics.DestroyAPIView):
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return Subscription.objects.all()
        return _user_subscriptions(self.request.user)


class SendNowView(APIView):
    def post(self, request, pk):
        try:
            if request.user.is_staff:
                subscription = Subscription.objects.get(pk=pk)
            else:
                subscription = _user_subscriptions(request.user).get(pk=pk)
        except Subscription.DoesNotExist:
            return Response({"error": "Subscription not found."}, status=status.HTTP_404_NOT_FOUND)

        if not subscription.is_active:
            return Response(
                {"error": "Cannot send email for an inactive subscription. Please verify the email first."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        send_stock_email_for_subscription(subscription)
        return Response({"message": f"Email sent to {subscription.email}"})
