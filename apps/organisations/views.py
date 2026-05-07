from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.utils import timezone

from apps.accounts.models import User
from .models import Organisation
from .serializers import OrganisationRegisterSerializer, OrganisationSerializer


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_organisation(request):
    """Register an organisation for manual GreenGig review."""
    if hasattr(request.user, 'organisation'):
        return Response({'detail': 'Organisation already registered.'}, status=status.HTTP_400_BAD_REQUEST)

    serializer = OrganisationRegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    org = serializer.save(user=request.user)

    request.user.role = User.Role.ORGANISATION
    request.user.save(update_fields=['role'])

    return Response({
        'detail': 'Registration submitted. GreenGig will review within 24 hours.',
        'organisation': OrganisationSerializer(org).data,
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_organisation(request):
    try:
        org = request.user.organisation
    except Organisation.DoesNotExist:
        return Response({'detail': 'No organisation found.'}, status=status.HTTP_404_NOT_FOUND)
    return Response(OrganisationSerializer(org).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def approve_organisation(request, org_id):
    try:
        org = Organisation.objects.get(pk=org_id)
    except Organisation.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    org.status = Organisation.Status.APPROVED
    org.rejection_reason = ''
    org.save(update_fields=['status', 'rejection_reason'])
    return Response({'detail': f'{org.name} approved.'})


@api_view(['POST'])
@permission_classes([IsAdminUser])
def reject_organisation(request, org_id):
    reason = request.data.get('reason', '').strip()
    if not reason:
        return Response({'detail': 'Rejection reason required.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        org = Organisation.objects.get(pk=org_id)
    except Organisation.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    org.status = Organisation.Status.REJECTED
    org.rejection_reason = reason
    org.save(update_fields=['status', 'rejection_reason'])
    return Response({'detail': f'{org.name} rejected.'})
