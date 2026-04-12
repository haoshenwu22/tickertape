from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/subscriptions/", include("subscriptions.urls")),
    path("api/stocks/", include("stocks.urls")),
    path("api/alerts/", include("alerts.urls")),
]
