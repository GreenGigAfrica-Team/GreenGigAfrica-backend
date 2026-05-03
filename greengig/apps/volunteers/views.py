"""
Volunteer API views.

GET /api/v1/volunteers/certificate/<assignment_id>/ — download PDF certificate
GET /api/v1/volunteers/impact/                      — volunteer impact summary
"""
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.tasks.models import TaskAssignment
from apps.accounts.models import JobSeekerProfile
from .certificate import generate_certificate


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_certificate(request, assignment_id):
    """
    US-05: Volunteer downloads PDF certificate after task approval.
    """
    try:
        assignment = TaskAssignment.objects.select_related(
            "task__organisation", "worker"
        ).get(pk=assignment_id, worker=request.user)
    except TaskAssignment.DoesNotExist:
        return Response({"detail": "Assignment not found."}, status=status.HTTP_404_NOT_FOUND)

    if assignment.status != TaskAssignment.Status.APPROVED:
        return Response(
            {"detail": "Certificate is only available after your submission is approved."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not assignment.task.is_volunteer_only:
        return Response(
            {"detail": "Certificates are issued for volunteer tasks only."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        volunteer_name = request.user.job_seeker_profile.full_name
    except JobSeekerProfile.DoesNotExist:
        volunteer_name = request.user.phone_number

    pdf_bytes = generate_certificate(
        volunteer_name=volunteer_name,
        task_title=assignment.task.title,
        org_name=assignment.task.organisation.name,
        completed_date=assignment.reviewed_at,
    )

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    safe_name = volunteer_name.replace(" ", "_")
    response["Content-Disposition"] = (
        f'attachment; filename="GreenGig_Certificate_{safe_name}.pdf"'
    )
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def volunteer_impact(request):
    """Return the volunteer's cumulative impact score and breakdown."""
    try:
        profile = request.user.job_seeker_profile
    except JobSeekerProfile.DoesNotExist:
        return Response(
            {"detail": "Profile not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    return Response(
        {
            "full_name": profile.full_name,
            "total_tasks_completed": profile.total_tasks_completed,
            "total_waste_kg": str(profile.total_waste_kg),
            "total_trees_planted": profile.total_trees_planted,
            "impact_score": str(profile.impact_score),
        }
    )
