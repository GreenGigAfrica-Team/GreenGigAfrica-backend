"""
Accounts API views.

Endpoints:
  POST /api/v1/auth/request-otp/   — send OTP to phone number
  POST /api/v1/auth/verify-otp/    — verify OTP, return JWT tokens
  POST /api/v1/auth/setup-profile/ — complete onboarding profile
  GET  /api/v1/auth/me/            — current user profile
  POST /api/v1/auth/token/refresh/ — refresh JWT
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.conf import settings

from .models import JobSeekerProfile, User
from .serializers import (
    JobSeekerProfileSerializer,
    ProfileSetupSerializer,
    RequestOTPSerializer,
    UserSerializer,
    VerifyOTPSerializer,
)
from .services import get_or_create_user, issue_tokens, send_otp, verify_otp


@api_view(["POST"])
@permission_classes([AllowAny])
def request_otp(request):
    """
    Step 1 of signup/login: send OTP to phone number.
    In DEBUG mode with no SMS provider configured, returns the OTP
    in the response so developers can test without SMS.
    """
    serializer = RequestOTPSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    phone_number = serializer.validated_data["phone_number"]
    otp = send_otp(phone_number)

    response_data = {"detail": f"OTP sent to {phone_number}. Valid for 10 minutes."}

    # In DEBUG with no SMS provider, expose the code for easy testing
    no_sms = not settings.AT_API_KEY and not settings.TWILIO_ACCOUNT_SID
    if settings.DEBUG and no_sms:
        response_data["dev_otp"] = otp.code
        response_data["dev_note"] = "SMS not configured — use this code for testing"

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_otp_view(request):
    """
    Step 2: verify OTP.  Returns JWT tokens + user info.
    If the user is new, `profile_complete` is False — frontend should
    redirect to profile setup.
    """
    serializer = VerifyOTPSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    phone_number = serializer.validated_data["phone_number"]
    code = serializer.validated_data["code"]

    success, message = verify_otp(phone_number, code)
    if not success:
        return Response({"detail": message}, status=status.HTTP_400_BAD_REQUEST)

    user, created = get_or_create_user(phone_number)
    user.is_phone_verified = True
    user.save(update_fields=["is_phone_verified"])

    tokens = issue_tokens(user)
    profile_complete = hasattr(user, "job_seeker_profile")

    return Response(
        {
            "tokens": tokens,
            "user": UserSerializer(user).data,
            "profile_complete": profile_complete,
            "is_new_user": created,
        },
        status=status.HTTP_200_OK,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def setup_profile(request):
    """
    Step 3 (onboarding): create JobSeekerProfile after OTP verification.
    """
    if hasattr(request.user, "job_seeker_profile"):
        return Response(
            {"detail": "Profile already set up."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = ProfileSetupSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    # Update user role
    request.user.role = data["role"]
    request.user.save(update_fields=["role"])

    profile = JobSeekerProfile.objects.create(
        user=request.user,
        full_name=data["full_name"],
        lga=data["lga"],
        task_interests=data["task_interests"],
    )

    return Response(
        JobSeekerProfileSerializer(profile).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def me(request):
    """Return or update the current user's profile."""
    try:
        profile = request.user.job_seeker_profile
    except JobSeekerProfile.DoesNotExist:
        return Response(
            {"detail": "Profile not found. Please complete onboarding."},
            status=status.HTTP_404_NOT_FOUND,
        )

    if request.method == "GET":
        return Response(JobSeekerProfileSerializer(profile).data)

    # PATCH — partial update
    serializer = JobSeekerProfileSerializer(profile, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)
