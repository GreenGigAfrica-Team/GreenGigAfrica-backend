from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_organisation, name='org-register'),
    path('me/', views.my_organisation, name='org-me'),
    path('<int:org_id>/approve/', views.approve_organisation, name='org-approve'),
    path('<int:org_id>/reject/', views.reject_organisation, name='org-reject'),
]
