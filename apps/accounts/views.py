from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import JobSeekerProfile
from .serializers import (
    RequestOTPSerializer, VerifyOTPSerializer,
    ProfileSetupSerializer, ProfileSerializer,
)
from .services import send_otp, verify_otp, get_or_create_user, issue_tokens


@api_view(['POST'])
@permission_classes([AllowAny])
def request_otp(request):
    """Send OTP to phone number."""
    serializer = RequestOTPSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    phone = serializer.validated_data['phone_number']
    otp = send_otp(phone)

    response = {'detail': f'OTP sent to {phone}.'}

    # Always include dev_otp so frontend can show it as fallback
    # When real SMS works, frontend can choose to hide it
    response['dev_otp'] = otp.code

    return Response(response, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp_view(request):
    """Verify OTP and return JWT tokens."""
    serializer = VerifyOTPSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    phone = serializer.validated_data['phone_number']
    code = serializer.validated_data['code']

    ok, message = verify_otp(phone, code)
    if not ok:
        return Response({'detail': message}, status=status.HTTP_400_BAD_REQUEST)

    user, _ = get_or_create_user(phone)
    user.is_phone_verified = True
    user.save(update_fields=['is_phone_verified'])

    tokens = issue_tokens(user)
    profile_complete = hasattr(user, 'profile')

    return Response({
        'tokens': tokens,
        'profile_complete': profile_complete,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def setup_profile(request):
    """Create profile after OTP verification (onboarding step 3)."""
    if hasattr(request.user, 'profile'):
        return Response({'detail': 'Profile already set up.'}, status=status.HTTP_400_BAD_REQUEST)

    serializer = ProfileSetupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    request.user.role = data['role']
    request.user.save(update_fields=['role'])

    profile = JobSeekerProfile.objects.create(
        user=request.user,
        full_name=data['full_name'],
        lga=data['lga'],
        task_interests=data['task_interests'],
    )
    return Response(ProfileSerializer(profile).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    """Return current user's profile."""
    try:
        profile = request.user.profile
    except JobSeekerProfile.DoesNotExist:
        return Response(
            {'detail': 'Profile not found. Please complete onboarding.'},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(ProfileSerializer(profile).data)
