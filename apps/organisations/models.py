from django.db import models
from django.conf import settings


class Organisation(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending Review'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    class OrgType(models.TextChoices):
        NGO = 'ngo', 'NGO'
        GOVERNMENT = 'government', 'Government Agency'
        STARTUP = 'startup', 'Climate Startup'
        CSR = 'csr', 'CSR / Corporate Foundation'
        OTHER = 'other', 'Other'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='organisation'
    )
    name = models.CharField(max_length=200)
    org_type = models.CharField(max_length=30, choices=OrgType.choices)
    cac_number = models.CharField(max_length=50, unique=True)
    contact_person_name = models.CharField(max_length=150)
    contact_phone = models.CharField(max_length=25)
    lagos_office_address = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_approved(self):
        return self.status == self.Status.APPROVED

    def __str__(self):
        return f'{self.name} [{self.status}]'
