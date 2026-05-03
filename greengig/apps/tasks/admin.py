"""Tasks admin."""
from django.contrib import admin
from .models import Task, TaskAssignment


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["title", "task_type", "location_lga", "status", "workers_needed", "workers_accepted", "created_at"]
    list_filter = ["status", "task_type", "location_lga", "is_volunteer_only"]
    search_fields = ["title", "organisation__name"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(TaskAssignment)
class TaskAssignmentAdmin(admin.ModelAdmin):
    list_display = ["worker", "task", "status", "accepted_at"]
    list_filter = ["status"]
    search_fields = ["worker__phone_number", "task__title"]
