from django.urls import path
from . import views

urlpatterns = [
    path('impact/', views.volunteer_impact, name='volunteer-impact'),
    path('certificate/<int:assignment_id>/', views.download_certificate, name='volunteer-certificate'),
]
