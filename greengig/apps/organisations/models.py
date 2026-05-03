"""Organisation models."""
from django.db import models
from django.conf import settings


class OrganisationType(models.TextChoices):
    NGO = "ngo", "NGO"
    GOVERNMENT = "government", "Government Agency"
    STARTUP = "startup", "Climate Startup"
    CSR = "csr", "CSR / Corporate Foundation"
    OTHER = "other", "Other"


class Organisation(models.Model):
    """
    Represents an NGO, government agency, or company that posts tasks.
    Must be manually approved by GreenGig before tasks go live.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        SUSPENDED = "suspended", "Suspended"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organisation",
    )
    name = models.CharField(max_length=200)
    org_type = models.CharField(max_length=30, choices=OrganisationType.choices)
    cac_number = models.CharField(max_length=50, unique=True)
    contact_person_name = models.CharField(max_length=150)
    contact_phone = models.CharField(max_length=20)
    lagos_office_address = models.TextField()
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="org_logos/", blank=True, null=True)

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    rejection_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_organisations",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Organisation"
        ordering = ["-created_at"]

    @property
    def is_approved(self):
        return self.status == self.Status.APPROVED

    def __str__(self):
        return f"{self.name} [{self.status}]"
