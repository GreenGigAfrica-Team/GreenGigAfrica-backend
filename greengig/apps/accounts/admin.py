"""Accounts admin."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTPCode, JobSeekerProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["phone_number", "role", "is_phone_verified", "is_active", "date_joined"]
    list_filter = ["role", "is_phone_verified", "is_active"]
    search_fields = ["phone_number", "email"]
    ordering = ["-date_joined"]
    fieldsets = (
        (None, {"fields": ("phone_number", "password")}),
        ("Personal info", {"fields": ("email", "role")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "is_phone_verified")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("phone_number", "password1", "password2", "role"),
        }),
    )


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ["phone_number", "code", "created_at", "is_used"]
    list_filter = ["is_used"]
    search_fields = ["phone_number"]


@admin.register(JobSeekerProfile)
class JobSeekerProfileAdmin(admin.ModelAdmin):
    list_display = ["full_name", "lga", "total_tasks_completed", "total_earnings"]
    list_filter = ["lga"]
    search_fields = ["full_name", "user__phone_number"]
