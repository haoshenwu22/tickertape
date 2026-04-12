from django.urls import path

from . import views

urlpatterns = [
    path("", views.AlertListCreateView.as_view(), name="alert-list-create"),
    path("<uuid:pk>/", views.AlertDeleteView.as_view(), name="alert-delete"),
]
