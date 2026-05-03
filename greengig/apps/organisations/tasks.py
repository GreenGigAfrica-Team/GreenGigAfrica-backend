"""Celery tasks for organisation notifications."""
from config.celery import app
import logging

logger = logging.getLogger(__name__)


@app.task(bind=True, max_retries=3)
def notify_org_approval(self, org_id: int, approved: bool, reason: str = ""):
    """
    Send SMS/email notification to organisation after approval or rejection.
    """
    try:
        from .models import Organisation
        from django.core.mail import send_mail
        from django.conf import settings

        org = Organisation.objects.select_related("user").get(pk=org_id)
        phone = org.user.phone_number
        email = org.user.email

        if approved:
            message = (
                f"Congratulations! Your organisation '{org.name}' has been approved on "
                f"GreenGig Africa. You can now log in and post climate tasks."
            )
        else:
            message = (
                f"Your GreenGig Africa organisation registration for '{org.name}' was not approved. "
                f"Reason: {reason}. Please contact support@greengigafrica.com for assistance."
            )

        # SMS via Twilio
        if settings.TWILIO_ACCOUNT_SID:
            from twilio.rest import Client
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone,
            )

        # Email if available
        if email:
            subject = "GreenGig Africa — Organisation Approved" if approved else "GreenGig Africa — Registration Update"
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

    except Exception as exc:
        logger.error("notify_org_approval failed for org %s: %s", org_id, exc)
        raise self.retry(exc=exc, countdown=60)
