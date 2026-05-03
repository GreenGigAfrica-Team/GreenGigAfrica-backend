"""Organisation admin."""
from django.contrib import admin
from .models import Organisation


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ["name", "org_type", "cac_number", "status", "created_at"]
    list_filter = ["status", "org_type"]
    search_fields = ["name", "cac_number", "contact_person_name"]
    readonly_fields = ["created_at", "updated_at", "reviewed_at"]
    actions = ["approve_selected", "reject_selected"]

    def approve_selected(self, request, queryset):
        from django.utils import timezone
        queryset.update(
            status=Organisation.Status.APPROVED,
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
        )
        self.message_user(request, f"{queryset.count()} organisation(s) approved.")
    approve_selected.short_description = "Approve selected organisations"

    def reject_selected(self, request, queryset):
        queryset.update(status=Organisation.Status.REJECTED)
        self.message_user(request, f"{queryset.count()} organisation(s) rejected.")
    reject_selected.short_description = "Reject selected organisations"
