from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from notifications.services import send_stock_email_for_subscription
from stocks.services import validate_ticker

from .models import Subscription
from .serializers import SubscriptionSerializer


class SubscriptionListCreateView(generics.ListCreateAPIView):
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return Subscription.objects.all()
        return Subscription.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        from django.db import IntegrityError
        from rest_framework.exceptions import ValidationError

        ticker = serializer.validated_data["ticker"]
        if not validate_ticker(ticker):
            raise ValidationError({"ticker": f"'{ticker}' is not a valid stock symbol."})
        try:
            serializer.save(user=self.request.user)
        except IntegrityError:
            raise ValidationError(
                {"detail": f"You already have a subscription for {ticker} with this email address."}
            )


class SubscriptionDeleteView(generics.DestroyAPIView):
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return Subscription.objects.all()
        return Subscription.objects.filter(user=self.request.user)


class SendNowView(APIView):
    def post(self, request, pk):
        try:
            if request.user.is_staff:
                subscription = Subscription.objects.get(pk=pk)
            else:
                subscription = Subscription.objects.get(pk=pk, user=request.user)
        except Subscription.DoesNotExist:
            return Response({"error": "Subscription not found."}, status=status.HTTP_404_NOT_FOUND)

        send_stock_email_for_subscription(subscription)
        return Response({"message": f"Email sent to {subscription.email}"})
