from django.urls import path
from . import views

urlpatterns = [
    path('match/', views.matched_tasks, name='ai-match'),
]
