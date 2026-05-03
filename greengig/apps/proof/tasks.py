"""
Celery tasks for proof of work:
  - AI image validation
  - Worker notification after review
  - Impact score update after approval
"""
import logging
from config.celery import app

logger = logging.getLogger(__name__)


@app.task(bind=True, max_retries=3)
def run_ai_validation(self, photo_id: int, task_type: str):
    """
    Run AI image validation on a proof photo.
    Uses TACO dataset model for waste tasks, DeepForest for tree tasks.
    Falls back to a stub if models are not loaded.
    """
    try:
        from .models import ProofPhoto
        photo = ProofPhoto.objects.get(pk=photo_id)

        from apps.ai_engine.validators import validate_proof_image
        result = validate_proof_image(photo.image.path, task_type)

        photo.ai_flag = result["passed"]
        photo.ai_confidence = result["confidence"]
        photo.ai_label = result["label"]
        photo.save(update_fields=["ai_flag", "ai_confidence", "ai_label"])

        # Update submission-level flag
        submission = photo.submission
        all_photos = submission.photos.all()
        if all_photos.filter(ai_flag=False).exists():
            submission.ai_validation_passed = False
            submission.ai_validation_notes = "One or more photos failed AI content check."
        elif all_photos.filter(ai_flag=True).count() == all_photos.count():
            submission.ai_validation_passed = True
            submission.ai_validation_notes = "All photos passed AI content validation."
        submission.save(update_fields=["ai_validation_passed", "ai_validation_notes"])

    except Exception as exc:
        logger.error("AI validation failed for photo %s: %s", photo_id, exc)
        raise self.retry(exc=exc, countdown=30)


@app.task(bind=True, max_retries=3)
def notify_worker_review_result(self, assignment_id: int):
    """Send SMS to worker after org approves or rejects their proof."""
    try:
        from apps.tasks.models import TaskAssignment
        from django.conf import settings

        assignment = TaskAssignment.objects.select_related(
            "worker", "task"
        ).get(pk=assignment_id)

        phone = assignment.worker.phone_number
        task_title = assignment.task.title

        if assignment.status == TaskAssignment.Status.APPROVED:
            msg = (
                f"Great news! Your proof of work for '{task_title}' has been approved. "
                f"Your payment will be processed shortly via OPay/PalmPay."
            )
        else:
            msg = (
                f"Your proof of work for '{task_title}' was not approved. "
                f"Reason: {assignment.rejection_reason}. "
                f"Contact the organisation if you have questions."
            )

        if settings.TWILIO_ACCOUNT_SID:
            from twilio.rest import Client
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=msg, from_=settings.TWILIO_PHONE_NUMBER, to=phone
            )
        else:
            print(f"[DEV SMS] {phone}: {msg}")

    except Exception as exc:
        logger.error("notify_worker_review_result failed for assignment %s: %s", assignment_id, exc)
        raise self.retry(exc=exc, countdown=60)


@app.task(bind=True, max_retries=3)
def update_worker_impact(self, assignment_id: int):
    """
    After approval, update the worker's impact score and earnings.
    """
    try:
        from apps.tasks.models import TaskAssignment
        from apps.accounts.models import JobSeekerProfile
        from decimal import Decimal

        assignment = TaskAssignment.objects.select_related(
            "task", "worker"
        ).get(pk=assignment_id)

        try:
            profile = assignment.worker.job_seeker_profile
        except JobSeekerProfile.DoesNotExist:
            return

        task = assignment.task
        profile.total_tasks_completed += 1

        if task.task_type == "waste_collection" or task.task_type == "recycling":
            # Estimate: 10kg per task (real value would come from org input)
            profile.total_waste_kg += Decimal("10.00")
        elif task.task_type == "tree_planting":
            profile.total_trees_planted += 1

        if task.pay_per_worker:
            profile.total_earnings += task.pay_per_worker

        profile.save(update_fields=[
            "total_tasks_completed",
            "total_waste_kg",
            "total_trees_planted",
            "total_earnings",
        ])

    except Exception as exc:
        logger.error("update_worker_impact failed for assignment %s: %s", assignment_id, exc)
        raise self.retry(exc=exc, countdown=60)
