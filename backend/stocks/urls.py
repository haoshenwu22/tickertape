from django.urls import path

from . import views

urlpatterns = [
    path("prices/", views.StockPricesView.as_view(), name="stock-prices"),
    path("history/", views.StockHistoryView.as_view(), name="stock-history"),
    path("validate/", views.ValidateTickerView.as_view(), name="validate-ticker"),
]
