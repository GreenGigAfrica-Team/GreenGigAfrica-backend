from django.urls import path
from . import views

urlpatterns = [
    path('', views.task_list_create, name='task-list-create'),
    path('my-tasks/', views.my_tasks, name='my-tasks'),
    path('org-dashboard/', views.org_dashboard, name='org-dashboard'),
    path('<int:task_id>/', views.task_detail, name='task-detail'),
    path('<int:task_id>/accept/', views.accept_task, name='task-accept'),
    path('<int:task_id>/withdraw/', views.withdraw_task, name='task-withdraw'),
]
