from django.urls import path

from . import views

urlpatterns = [
    path("prices/", views.StockPricesView.as_view(), name="stock-prices"),
    path("history/", views.StockHistoryView.as_view(), name="stock-history"),
    path("recommendation/", views.StockRecommendationView.as_view(), name="stock-recommendation"),
    path("validate/", views.ValidateTickerView.as_view(), name="validate-ticker"),
]
