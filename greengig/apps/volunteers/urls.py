"""Volunteer URL patterns."""
from django.urls import path
from . import views

urlpatterns = [
    path("certificate/<int:assignment_id>/", views.download_certificate, name="volunteer-certificate"),
    path("impact/", views.volunteer_impact, name="volunteer-impact"),
]
