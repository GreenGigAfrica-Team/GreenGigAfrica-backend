"""
Proof of Work API views.

POST /api/v1/proof/<assignment_id>/upload/  — worker uploads a photo
GET  /api/v1/proof/<assignment_id>/         — get full proof submission
POST /api/v1/proof/<assignment_id>/review/  — org approves or rejects
"""
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.tasks.models import TaskAssignment
from apps.organisations.models import Organisation
from .models import ProofSubmission, ProofPhoto
from .serializers import (
    ProofPhotoUploadSerializer,
    ProofSubmissionSerializer,
    ProofReviewSerializer,
)
from .tasks import run_ai_validation, notify_worker_review_result, update_worker_impact


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def upload_proof_photo(request, assignment_id):
    """
    US-04: Worker uploads a proof photo for a specific stage.
    GPS + timestamp captured automatically.
    """
    try:
        assignment = TaskAssignment.objects.select_related("task", "worker").get(
            pk=assignment_id, worker=request.user
        )
    except TaskAssignment.DoesNotExist:
        return Response({"detail": "Assignment not found."}, status=status.HTTP_404_NOT_FOUND)

    if assignment.status not in [
        TaskAssignment.Status.ACCEPTED,
        TaskAssignment.Status.SUBMITTED,
    ]:
        return Response(
            {"detail": "Cannot upload proof for this assignment status."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = ProofPhotoUploadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    # Get or create the proof submission container
    submission, _ = ProofSubmission.objects.get_or_create(assignment=assignment)

    photo = ProofPhoto.objects.create(
        submission=submission,
        stage=data["stage"],
        image=data["image"],
        latitude=data.get("latitude"),
        longitude=data.get("longitude"),
    )

    # If this is the completion photo, mark assignment as submitted
    if data["stage"] == "completion":
        assignment.status = TaskAssignment.Status.SUBMITTED
        assignment.submitted_at = timezone.now()
        assignment.save(update_fields=["status", "submitted_at"])

        submission.submitted_at = timezone.now()
        submission.save(update_fields=["submitted_at"])

    # Trigger async AI validation
    run_ai_validation.delay(photo.id, assignment.task.task_type)

    return Response(
        {
            "detail": f"Photo uploaded for stage: {data['stage']}.",
            "photo_id": photo.id,
            "assignment_status": assignment.status,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_proof_submission(request, assignment_id):
    """
    Get the full proof submission for an assignment.
    Accessible by the worker or the owning organisation.
    """
    try:
        assignment = TaskAssignment.objects.select_related(
            "task__organisation", "worker"
        ).get(pk=assignment_id)
    except TaskAssignment.DoesNotExist:
        return Response({"detail": "Assignment not found."}, status=status.HTTP_404_NOT_FOUND)

    # Permission: worker or org
    is_worker = assignment.worker == request.user
    is_org = (
        hasattr(request.user, "organisation")
        and request.user.organisation == assignment.task.organisation
    )
    if not (is_worker or is_org):
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    try:
        submission = assignment.proof_submission
    except ProofSubmission.DoesNotExist:
        return Response({"detail": "No proof submitted yet."}, status=status.HTTP_404_NOT_FOUND)

    return Response(ProofSubmissionSerializer(submission).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def review_proof(request, assignment_id):
    """
    US-08: Organisation approves or rejects a proof submission.
    """
    try:
        assignment = TaskAssignment.objects.select_related(
            "task__organisation", "worker"
        ).get(pk=assignment_id)
    except TaskAssignment.DoesNotExist:
        return Response({"detail": "Assignment not found."}, status=status.HTTP_404_NOT_FOUND)

    # Only the owning organisation can review
    try:
        org = request.user.organisation
    except Organisation.DoesNotExist:
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    if assignment.task.organisation != org:
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    if assignment.status != TaskAssignment.Status.SUBMITTED:
        return Response(
            {"detail": "Only submitted assignments can be reviewed."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = ProofReviewSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    if data["action"] == "approve":
        assignment.status = TaskAssignment.Status.APPROVED
        assignment.rejection_reason = ""
    else:
        assignment.status = TaskAssignment.Status.REJECTED
        assignment.rejection_reason = data["rejection_reason"]

    assignment.reviewed_at = timezone.now()
    assignment.save(update_fields=["status", "rejection_reason", "reviewed_at"])

    # Async: notify worker + update impact stats if approved
    notify_worker_review_result.delay(assignment.id)
    if data["action"] == "approve":
        update_worker_impact.delay(assignment.id)

    return Response(
        {
            "detail": f"Submission {data['action']}d.",
            "assignment_status": assignment.status,
        }
    )
