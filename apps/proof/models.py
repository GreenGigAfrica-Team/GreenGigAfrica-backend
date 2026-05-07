from django.db import models
from apps.tasks.models import TaskAssignment


class ProofSubmission(models.Model):
    assignment = models.OneToOneField(
        TaskAssignment, on_delete=models.CASCADE, related_name='proof_submission'
    )
    ai_validation_passed = models.BooleanField(null=True, blank=True)
    ai_validation_notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Proof for {self.assignment}'


class ProofPhoto(models.Model):
    class Stage(models.TextChoices):
        START = 'start', 'Task Start'
        DURING = 'during', 'During Task'
        COMPLETION = 'completion', 'Task Completion'

    submission = models.ForeignKey(
        ProofSubmission, on_delete=models.CASCADE, related_name='photos'
    )
    stage = models.CharField(max_length=20, choices=Stage.choices)
    image = models.ImageField(upload_to='proof_photos/%Y/%m/%d/')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    captured_at = models.DateTimeField(auto_now_add=True)
    ai_flag = models.BooleanField(null=True, blank=True)

    class Meta:
        ordering = ['captured_at']

    def __str__(self):
        return f'{self.stage} — {self.submission.assignment}'
