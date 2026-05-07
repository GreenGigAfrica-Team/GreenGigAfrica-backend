from rest_framework import serializers
from .models import Task, TaskAssignment


class TaskSerializer(serializers.ModelSerializer):
    organisation_name = serializers.CharField(source='organisation.name', read_only=True)
    spots_remaining = serializers.ReadOnlyField()
    is_full = serializers.ReadOnlyField()

    class Meta:
        model = Task
        fields = [
            'id', 'organisation_name', 'title', 'task_type', 'description',
            'location_lga', 'location_address', 'start_datetime', 'end_datetime',
            'workers_needed', 'workers_accepted', 'spots_remaining', 'is_full',
            'pay_per_worker', 'is_volunteer_only', 'proof_requirements',
            'day_of_contact_name', 'day_of_contact_phone', 'status', 'created_at',
        ]


class TaskCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'title', 'task_type', 'description', 'location_lga', 'location_address',
            'start_datetime', 'end_datetime', 'workers_needed', 'pay_per_worker',
            'is_volunteer_only', 'proof_requirements', 'day_of_contact_name', 'day_of_contact_phone',
        ]

    def validate(self, data):
        if not data.get('is_volunteer_only') and not data.get('pay_per_worker'):
            raise serializers.ValidationError(
                'Set a pay_per_worker amount or mark the task as volunteer-only.'
            )
        if data['start_datetime'] >= data['end_datetime']:
            raise serializers.ValidationError('end_datetime must be after start_datetime.')
        return data


class TaskAssignmentSerializer(serializers.ModelSerializer):
    worker_name = serializers.SerializerMethodField()
    worker_phone = serializers.CharField(source='worker.phone_number', read_only=True)
    task_title = serializers.CharField(source='task.title', read_only=True)

    class Meta:
        model = TaskAssignment
        fields = [
            'id', 'task_title', 'worker_name', 'worker_phone',
            'status', 'rejection_reason', 'accepted_at', 'submitted_at', 'reviewed_at',
        ]

    def get_worker_name(self, obj):
        try:
            return obj.worker.profile.full_name
        except Exception:
            return obj.worker.phone_number


class MyTaskSerializer(serializers.ModelSerializer):
    """Used for /tasks/my-tasks/ — matches frontend expectation exactly."""
    assignment_id = serializers.IntegerField(source='id', read_only=True)
    assignment_status = serializers.CharField(source='status', read_only=True)
    task = TaskSerializer(read_only=True)

    class Meta:
        model = TaskAssignment
        fields = ['assignment_id', 'assignment_status', 'task']
