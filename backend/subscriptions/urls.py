from django.urls import path

from . import views

urlpatterns = [
    path("", views.SubscriptionListCreateView.as_view(), name="subscription-list-create"),
    path("<uuid:pk>/", views.SubscriptionDeleteView.as_view(), name="subscription-delete"),
    path("<uuid:pk>/send-now/", views.SendNowView.as_view(), name="subscription-send-now"),
]
