from django.contrib import admin
from .models import ProofSubmission, ProofPhoto


@admin.register(ProofSubmission)
class ProofSubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'ai_validation_passed', 'submitted_at')
    list_filter = ('ai_validation_passed',)


@admin.register(ProofPhoto)
class ProofPhotoAdmin(admin.ModelAdmin):
    list_display = ('submission', 'stage', 'captured_at', 'ai_flag')
    list_filter = ('stage', 'ai_flag')
