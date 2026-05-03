"""Proof admin."""
from django.contrib import admin
from .models import ProofSubmission, ProofPhoto


class ProofPhotoInline(admin.TabularInline):
    model = ProofPhoto
    extra = 0
    readonly_fields = ["captured_at", "ai_flag", "ai_confidence", "ai_label"]


@admin.register(ProofSubmission)
class ProofSubmissionAdmin(admin.ModelAdmin):
    list_display = ["assignment", "ai_validation_passed", "submitted_at"]
    list_filter = ["ai_validation_passed"]
    inlines = [ProofPhotoInline]


@admin.register(ProofPhoto)
class ProofPhotoAdmin(admin.ModelAdmin):
    list_display = ["submission", "stage", "captured_at", "ai_flag", "ai_confidence"]
    list_filter = ["stage", "ai_flag"]
