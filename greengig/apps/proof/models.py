"""
Proof of Work models.

Each TaskAssignment can have multiple ProofPhoto submissions
across three stages: start, during, completion.
"""
from django.db import models
from apps.tasks.models import TaskAssignment


class ProofSubmission(models.Model):
    """
    Container for all proof photos for a single assignment.
    Status mirrors TaskAssignment status for convenience.
    """

    class Stage(models.TextChoices):
        START = "start", "Task Start"
        DURING = "during", "During Task"
        COMPLETION = "completion", "Task Completion"

    assignment = models.OneToOneField(
        TaskAssignment,
        on_delete=models.CASCADE,
        related_name="proof_submission",
    )
    ai_validation_passed = models.BooleanField(null=True, blank=True)
    ai_validation_notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Proof Submission"

    def __str__(self):
        return f"Proof for {self.assignment}"


class ProofPhoto(models.Model):
    """
    A single GPS-tagged, timestamped photo within a proof submission.
    """

    submission = models.ForeignKey(
        ProofSubmission, on_delete=models.CASCADE, related_name="photos"
    )
    stage = models.CharField(max_length=20, choices=ProofSubmission.Stage.choices)
    image = models.ImageField(upload_to="proof_photos/%Y/%m/%d/")

    # GPS captured at upload time
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Timestamp captured server-side at upload
    captured_at = models.DateTimeField(auto_now_add=True)

    # AI validation result for this individual photo
    ai_flag = models.BooleanField(null=True, blank=True)
    ai_confidence = models.FloatField(null=True, blank=True)
    ai_label = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["captured_at"]
        verbose_name = "Proof Photo"

    def __str__(self):
        return f"{self.stage} photo — {self.submission.assignment}"
