"""Proof of work serializers."""
from rest_framework import serializers
from .models import ProofSubmission, ProofPhoto


class ProofPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProofPhoto
        fields = [
            "id",
            "stage",
            "image",
            "latitude",
            "longitude",
            "captured_at",
            "ai_flag",
            "ai_confidence",
            "ai_label",
        ]
        read_only_fields = ["captured_at", "ai_flag", "ai_confidence", "ai_label"]


class ProofPhotoUploadSerializer(serializers.Serializer):
    """Used when a worker uploads a single proof photo."""

    stage = serializers.ChoiceField(choices=["start", "during", "completion"])
    image = serializers.ImageField()
    latitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True
    )
    longitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True
    )


class ProofSubmissionSerializer(serializers.ModelSerializer):
    photos = ProofPhotoSerializer(many=True, read_only=True)
    assignment_id = serializers.IntegerField(source="assignment.id", read_only=True)
    worker_name = serializers.SerializerMethodField()
    task_title = serializers.CharField(
        source="assignment.task.title", read_only=True
    )

    class Meta:
        model = ProofSubmission
        fields = [
            "id",
            "assignment_id",
            "worker_name",
            "task_title",
            "ai_validation_passed",
            "ai_validation_notes",
            "submitted_at",
            "photos",
        ]

    def get_worker_name(self, obj):
        try:
            return obj.assignment.worker.job_seeker_profile.full_name
        except Exception:
            return obj.assignment.worker.phone_number


class ProofReviewSerializer(serializers.Serializer):
    """Organisation approves or rejects a proof submission."""

    action = serializers.ChoiceField(choices=["approve", "reject"])
    rejection_reason = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data["action"] == "reject" and not data.get("rejection_reason", "").strip():
            raise serializers.ValidationError(
                {"rejection_reason": "A written reason is required when rejecting."}
            )
        return data
