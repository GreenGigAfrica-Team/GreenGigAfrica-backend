from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTPCode, JobSeekerProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('phone_number', 'role', 'is_phone_verified', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_phone_verified')
    search_fields = ('phone_number',)
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Info', {'fields': ('email', 'role', 'is_phone_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {'classes': ('wide',), 'fields': ('phone_number', 'password1', 'password2', 'role')}),
    )


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'code', 'is_used', 'created_at')
    list_filter = ('is_used',)


@admin.register(JobSeekerProfile)
class JobSeekerProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'lga', 'total_tasks_completed', 'total_earnings')
    search_fields = ('full_name', 'user__phone_number')
