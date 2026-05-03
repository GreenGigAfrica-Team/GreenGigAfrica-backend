"""Accounts serializers."""
from rest_framework import serializers
from .models import User, OTPCode, JobSeekerProfile


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "full_name",
            "phone_number",
            "password",
            "role",
        ]

    def create(self, validated_data):
        password = validated_data.pop("password")

        user = User(**validated_data)
        user.set_password(password)
        user.save()

        return user
    
class RequestOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)

    def validate_phone_number(self, value):
        # Normalise: strip spaces
        value = value.strip().replace(" ", "")
        if not value.startswith("+"):
            raise serializers.ValidationError(
                "Phone number must include country code, e.g. +2348012345678 or +251912345678"
            )
        # Must have at least 7 digits after the +
        digits = value[1:].replace(" ", "")
        if not digits.isdigit() or len(digits) < 7:
            raise serializers.ValidationError(
                "Enter a valid international phone number."
            )
        return value


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)
    code = serializers.CharField(max_length=10)


class JobSeekerProfileSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(source="user.phone_number", read_only=True)
    role = serializers.CharField(source="user.role", read_only=True)
    impact_score = serializers.ReadOnlyField()

    class Meta:
        model = JobSeekerProfile
        fields = [
            "id",
            "phone_number",
            "role",
            "full_name",
            "lga",
            "task_interests",
            "bio",
            "profile_photo",
            "total_tasks_completed",
            "total_waste_kg",
            "total_trees_planted",
            "total_earnings",
            "impact_score",
            "created_at",
        ]
        read_only_fields = [
            "total_tasks_completed",
            "total_waste_kg",
            "total_trees_planted",
            "total_earnings",
            "impact_score",
            "created_at",
        ]


class ProfileSetupSerializer(serializers.Serializer):
    """Used during onboarding — step 2 after OTP verification."""

    full_name = serializers.CharField(max_length=150)
    lga = serializers.ChoiceField(choices=[
        "alimosho", "epe", "ikorodu", "mushin", "lekki", "other"
    ])
    task_interests = serializers.ListField(
        child=serializers.CharField(), min_length=1
    )
    role = serializers.ChoiceField(choices=["job_seeker", "volunteer"])


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "phone_number", "role", "is_phone_verified", "date_joined"]
        read_only_fields = fields

