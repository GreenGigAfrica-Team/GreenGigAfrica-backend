"""Accounts URL patterns."""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path("request-otp/", views.request_otp, name="request-otp"),
    path("verify-otp/", views.verify_otp_view, name="verify-otp"),
    path("setup-profile/", views.setup_profile, name="setup-profile"),
    path("me/", views.me, name="me"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
]
