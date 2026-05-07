import random
import string
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.conf import settings


class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra):
        if not phone_number:
            raise ValueError('Phone number is required.')
        user = self.model(phone_number=phone_number, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self.create_user(phone_number, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        JOB_SEEKER = 'job_seeker', 'Job Seeker'
        VOLUNTEER = 'volunteer', 'Volunteer'
        ORGANISATION = 'organisation', 'Organisation'
        ADMIN = 'admin', 'Admin'

    phone_number = models.CharField(max_length=25, unique=True)
    email = models.EmailField(blank=True, null=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.JOB_SEEKER)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.phone_number


class OTPCode(models.Model):
    phone_number = models.CharField(max_length=25)
    code = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def is_valid(self):
        from datetime import timedelta
        expiry = self.created_at + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
        return not self.is_used and timezone.now() <= expiry

    @classmethod
    def generate_code(cls):
        return ''.join(random.choices(string.digits, k=settings.OTP_LENGTH))

    def __str__(self):
        return f'{self.phone_number} — {self.code}'


class LGA(models.TextChoices):
    ALIMOSHO = 'alimosho', 'Alimosho'
    EPE = 'epe', 'Epe'
    IKORODU = 'ikorodu', 'Ikorodu'
    MUSHIN = 'mushin', 'Mushin'
    LEKKI = 'lekki', 'Lekki'
    OTHER = 'other', 'Other'


class JobSeekerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=150)
    lga = models.CharField(max_length=50, choices=LGA.choices)
    task_interests = models.JSONField(default=list)
    total_tasks_completed = models.PositiveIntegerField(default=0)
    total_waste_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_trees_planted = models.PositiveIntegerField(default=0)
    total_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def impact_score(self):
        return float(self.total_waste_kg * 1 + self.total_trees_planted * 5)

    def __str__(self):
        return f'{self.full_name} ({self.user.phone_number})'
