"""
Organisation API views.

POST /api/v1/organisations/register/   — submit org for review
GET  /api/v1/organisations/me/         — get own org profile
PATCH /api/v1/organisations/me/        — update own org profile
POST /api/v1/organisations/<id>/approve/ — GreenGig admin approves
POST /api/v1/organisations/<id>/reject/  — GreenGig admin rejects
"""
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from apps.accounts.models import User
from .models import Organisation
from .serializers import OrganisationRegisterSerializer, OrganisationSerializer
from .tasks import notify_org_approval


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def register_organisation(request):
    """US-06: Organisation submits registration for manual GreenGig review."""
    if hasattr(request.user, "organisation"):
        return Response(
            {"detail": "Organisation already registered."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = OrganisationRegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    org = serializer.save(user=request.user)

    # Update user role
    request.user.role = User.Role.ORGANISATION
    request.user.save(update_fields=["role"])

    return Response(
        {
            "detail": "Registration submitted. GreenGig will review and notify you within 24 hours.",
            "organisation": OrganisationSerializer(org).data,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def my_organisation(request):
    """Get or update the current user's organisation."""
    try:
        org = request.user.organisation
    except Organisation.DoesNotExist:
        return Response(
            {"detail": "No organisation found for this account."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        return Response(OrganisationSerializer(org).data)

    serializer = OrganisationSerializer(org, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAdminUser])
def approve_organisation(request, org_id):
    """GreenGig admin approves an organisation."""
    try:
        org = Organisation.objects.get(pk=org_id)
    except Organisation.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    org.status = Organisation.Status.APPROVED
    org.reviewed_by = request.user
    org.reviewed_at = timezone.now()
    org.rejection_reason = ""
    org.save(update_fields=["status", "reviewed_by", "reviewed_at", "rejection_reason"])

    # Async notification
    notify_org_approval.delay(org.id, approved=True)

    return Response({"detail": f"{org.name} has been approved."})


@api_view(["POST"])
@permission_classes([IsAdminUser])
def reject_organisation(request, org_id):
    """GreenGig admin rejects an organisation with a reason."""
    reason = request.data.get("reason", "").strip()
    if not reason:
        return Response(
            {"detail": "A rejection reason is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        org = Organisation.objects.get(pk=org_id)
    except Organisation.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    org.status = Organisation.Status.REJECTED
    org.reviewed_by = request.user
    org.reviewed_at = timezone.now()
    org.rejection_reason = reason
    org.save(update_fields=["status", "reviewed_by", "reviewed_at", "rejection_reason"])

    notify_org_approval.delay(org.id, approved=False, reason=reason)

    return Response({"detail": f"{org.name} has been rejected."})
