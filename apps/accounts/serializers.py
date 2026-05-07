from rest_framework import serializers
from .models import User, OTPCode, JobSeekerProfile


class RequestOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=25)

    def validate_phone_number(self, value):
        value = value.strip().replace(' ', '')
        if not value.startswith('+'):
            raise serializers.ValidationError(
                'Phone number must include country code, e.g. +2348012345678'
            )
        digits = value[1:]
        if not digits.isdigit() or len(digits) < 7:
            raise serializers.ValidationError('Enter a valid international phone number.')
        return value


class VerifyOTPSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=25)
    code = serializers.CharField(max_length=10)


class ProfileSetupSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)
    lga = serializers.ChoiceField(choices=['alimosho', 'epe', 'ikorodu', 'mushin', 'lekki', 'other'])
    task_interests = serializers.ListField(child=serializers.CharField(), min_length=1)
    role = serializers.ChoiceField(choices=['job_seeker', 'volunteer'])


class ProfileSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    role = serializers.CharField(source='user.role', read_only=True)
    impact_score = serializers.ReadOnlyField()

    class Meta:
        model = JobSeekerProfile
        fields = [
            'id', 'phone_number', 'role', 'full_name', 'lga',
            'task_interests', 'total_tasks_completed', 'total_waste_kg',
            'total_trees_planted', 'total_earnings', 'impact_score', 'created_at',
        ]
        read_only_fields = [
            'total_tasks_completed', 'total_waste_kg',
            'total_trees_planted', 'total_earnings', 'impact_score', 'created_at',
        ]
