"""Task serializers."""
from rest_framework import serializers
from .models import Task, TaskAssignment


class TaskSerializer(serializers.ModelSerializer):
    """Full task detail — used for task feed and detail card."""

    organisation_name = serializers.CharField(
        source="organisation.name", read_only=True
    )
    spots_remaining = serializers.ReadOnlyField()
    is_full = serializers.ReadOnlyField()

    class Meta:
        model = Task
        fields = [
            "id",
            "organisation_name",
            "title",
            "task_type",
            "description",
            "location_lga",
            "location_address",
            "latitude",
            "longitude",
            "start_datetime",
            "end_datetime",
            "workers_needed",
            "workers_accepted",
            "spots_remaining",
            "is_full",
            "pay_per_worker",
            "is_volunteer_only",
            "proof_requirements",
            "day_of_contact_name",
            "day_of_contact_phone",
            "status",
            "created_at",
        ]
        read_only_fields = ["workers_accepted", "status", "created_at"]


class TaskCreateSerializer(serializers.ModelSerializer):
    """Used by organisations to post a new task (US-07)."""

    class Meta:
        model = Task
        fields = [
            "title",
            "task_type",
            "description",
            "location_lga",
            "location_address",
            "latitude",
            "longitude",
            "start_datetime",
            "end_datetime",
            "workers_needed",
            "pay_per_worker",
            "is_volunteer_only",
            "proof_requirements",
            "day_of_contact_name",
            "day_of_contact_phone",
        ]

    def validate(self, data):
        if not data.get("is_volunteer_only") and not data.get("pay_per_worker"):
            raise serializers.ValidationError(
                "Either set a pay_per_worker amount or mark the task as volunteer-only."
            )
        if data["start_datetime"] >= data["end_datetime"]:
            raise serializers.ValidationError(
                "end_datetime must be after start_datetime."
            )
        return data


class TaskAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for task assignments — used in org dashboard."""

    worker_name = serializers.SerializerMethodField()
    worker_phone = serializers.CharField(source="worker.phone_number", read_only=True)
    task_title = serializers.CharField(source="task.title", read_only=True)

    class Meta:
        model = TaskAssignment
        fields = [
            "id",
            "task_title",
            "worker_name",
            "worker_phone",
            "status",
            "rejection_reason",
            "accepted_at",
            "submitted_at",
            "reviewed_at",
        ]
        read_only_fields = ["accepted_at", "submitted_at", "reviewed_at"]

    def get_worker_name(self, obj):
        try:
            return obj.worker.job_seeker_profile.full_name
        except Exception:
            return obj.worker.phone_number
