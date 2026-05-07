from django.urls import path
from . import views

urlpatterns = [
    path('<int:assignment_id>/upload/', views.upload_proof_photo, name='proof-upload'),
    path('<int:assignment_id>/', views.get_proof_submission, name='proof-detail'),
    path('<int:assignment_id>/review/', views.review_proof, name='proof-review'),
]
