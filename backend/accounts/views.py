from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import EmailVerificationToken, VerifiedEmail
from .serializers import RegisterSerializer, UserSerializer
from .tasks import send_verification_email_task


def send_verification_email(user, email, token, token_type):
    """Send verification email synchronously (no Celery dependency)."""
    send_verification_email_task(user.username, email, token, token_type)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Create verification token
        token = EmailVerificationToken.objects.create(
            user=user,
            email=user.email,
            token_type="registration",
        )

        # Send verification email
        send_verification_email(user, user.email, token.token, "registration")

        return Response(
            {"message": "Verification email sent. Please check your inbox to activate your account."},
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]


class MeView(APIView):
    def get(self, request):
        return Response(UserSerializer(request.user).data)


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token_value = request.data.get("token")
        if not token_value:
            return Response(
                {"error": "Token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = EmailVerificationToken.objects.get(token=token_value)
        except EmailVerificationToken.DoesNotExist:
            return Response(
                {"error": "Invalid verification token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if token.is_used:
            return Response(
                {"error": "This token has already been used."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if token.is_expired():
            return Response(
                {"error": "This token has expired. Please request a new verification email."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Mark token as used
        token.is_used = True
        token.save()

        # Create verified email entry
        VerifiedEmail.objects.get_or_create(user=token.user, email=token.email)

        if token.token_type == "registration":
            # Activate user account
            token.user.is_active = True
            token.user.save()
            return Response(
                {"message": "Email verified successfully. Your account is now active."},
                status=status.HTTP_200_OK,
            )

        elif token.token_type == "subscription_email":
            # Activate pending subscriptions for this email
            from subscriptions.models import Subscription

            pending_subs = Subscription.objects.filter(
                user=token.user,
                email=token.email,
                is_active=False,
            )
            activated_count = pending_subs.update(is_active=True)
            return Response(
                {
                    "message": f"Email verified. {activated_count} subscription(s) activated.",
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"message": "Email verified successfully."},
            status=status.HTTP_200_OK,
        )


class ResendVerificationView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from django.contrib.auth import get_user_model

        User = get_user_model()

        email = request.data.get("email")
        if not email:
            return Response(
                {"error": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Don't reveal whether the email exists
            return Response(
                {"message": "If an account exists with this email, a verification email has been sent."},
                status=status.HTTP_200_OK,
            )

        # Determine token type based on user state
        if not user.is_active:
            token_type = "registration"
        else:
            token_type = "subscription_email"

        # Create new token
        token = EmailVerificationToken.objects.create(
            user=user,
            email=email,
            token_type=token_type,
        )

        send_verification_email(user, email, token.token, token_type)

        return Response(
            {"message": "If an account exists with this email, a verification email has been sent."},
            status=status.HTTP_200_OK,
        )
