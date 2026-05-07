from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from apps.accounts.models import JobSeekerProfile
from apps.tasks.serializers import TaskSerializer
from .matching import get_matched_tasks


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def matched_tasks(request):
    """Return AI-matched task recommendations for the authenticated user."""
    try:
        profile = request.user.profile
    except JobSeekerProfile.DoesNotExist:
        return Response(
            {'detail': 'Complete your profile to get recommendations.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    limit = int(request.query_params.get('limit', 10))
    tasks = get_matched_tasks(profile, limit=limit)

    return Response({
        'count': len(tasks),
        'results': TaskSerializer(tasks, many=True).data,
    })
