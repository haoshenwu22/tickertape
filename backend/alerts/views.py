from rest_framework import generics

from stocks.services import validate_ticker

from .models import PriceAlert
from .serializers import PriceAlertSerializer


class AlertListCreateView(generics.ListCreateAPIView):
    serializer_class = PriceAlertSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return PriceAlert.objects.all()
        return PriceAlert.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        ticker = serializer.validated_data["ticker"]
        if not validate_ticker(ticker):
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"ticker": f"'{ticker}' is not a valid stock symbol."})
        serializer.save(user=self.request.user)


class AlertDeleteView(generics.DestroyAPIView):
    serializer_class = PriceAlertSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return PriceAlert.objects.all()
        return PriceAlert.objects.filter(user=self.request.user)
