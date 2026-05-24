from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .firebase import verify_firebase_token
from .models import User, JobSeekerProfile
from .serializers import (
    RequestOTPSerializer, VerifyOTPSerializer,
    ProfileSetupSerializer, ProfileSerializer,
)
from .services import send_otp, verify_otp, get_or_create_user, issue_tokens


@api_view(['POST'])
@permission_classes([AllowAny])
def firebase_login(request):
    id_token = request.data.get("token")

    if not id_token:
        return Response(
            {"error": "Token is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    decoded = verify_firebase_token(id_token)

    if not decoded:
        return Response(
            {"error": "Invalid Firebase token"},
            status=status.HTTP_401_UNAUTHORIZED
        )

    phone = decoded.get("phone_number")

    if not phone:
        return Response(
            {"error": "Phone number not found"},
            status=status.HTTP_400_BAD_REQUEST
        )

    user, created = User.objects.get_or_create(phone_number=phone)
    user.is_phone_verified = True
    user.save(update_fields=['is_phone_verified'])

    tokens = issue_tokens(user)
    profile_complete = hasattr(user, 'profile')

    return Response({
        "message": "Login successful",
        "phone": phone,
        "tokens": tokens,
        "profile_complete": profile_complete,
    })
    
@api_view(['POST'])
@permission_classes([AllowAny])
def request_otp(request):
    """Send OTP to phone number. Rate limited to 3 requests per 10 minutes."""
    serializer = RequestOTPSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    phone = serializer.validated_data['phone_number']

    try:
        otp = send_otp(phone)
    except ValueError as e:
        return Response({'detail': str(e)}, status=status.HTTP_429_TOO_MANY_REQUESTS)

    response = {'detail': f'OTP sent to {phone}.'}
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
