from django.db import models
from django.conf import settings


class Task(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        CLOSED = 'closed', 'Closed'

    class TaskType(models.TextChoices):
        WASTE_COLLECTION = 'waste_collection', 'Waste Collection'
        TREE_PLANTING = 'tree_planting', 'Tree Planting'
        URBAN_FARMING = 'urban_farming', 'Urban Farming'
        CLIMATE_DATA = 'climate_data', 'Climate Data Collection'
        RECYCLING = 'recycling', 'Recycling & Sorting'
        COMMUNITY_EDUCATION = 'community_education', 'Community Education'

    organisation = models.ForeignKey(
        'organisations.Organisation', on_delete=models.CASCADE, related_name='tasks'
    )
    title = models.CharField(max_length=200)
    task_type = models.CharField(max_length=50, choices=TaskType.choices)
    description = models.TextField()
    location_lga = models.CharField(max_length=50)
    location_address = models.CharField(max_length=300)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    workers_needed = models.PositiveIntegerField(default=1)
    workers_accepted = models.PositiveIntegerField(default=0)
    pay_per_worker = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_volunteer_only = models.BooleanField(default=False)
    proof_requirements = models.TextField(blank=True)
    day_of_contact_name = models.CharField(max_length=150, blank=True)
    day_of_contact_phone = models.CharField(max_length=25, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def spots_remaining(self):
        return max(0, self.workers_needed - self.workers_accepted)

    @property
    def is_full(self):
        return self.workers_accepted >= self.workers_needed

    def __str__(self):
        return f'{self.title} [{self.status}]'


class TaskAssignment(models.Model):
    class Status(models.TextChoices):
        ACCEPTED = 'accepted', 'Accepted'
        SUBMITTED = 'submitted', 'Proof Submitted'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        WITHDRAWN = 'withdrawn', 'Withdrawn'

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='assignments')
    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assignments'
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACCEPTED)
    rejection_reason = models.TextField(blank=True)
    payout_notified = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [('task', 'worker')]
        ordering = ['-accepted_at']

    def __str__(self):
        return f'{self.worker} → {self.task.title} [{self.status}]'
