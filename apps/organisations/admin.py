from django.contrib import admin
from .models import Organisation


@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ('name', 'org_type', 'status', 'created_at')
    list_filter = ('status', 'org_type')
    search_fields = ('name', 'cac_number')
    actions = ['approve_selected']

    def approve_selected(self, request, queryset):
        queryset.update(status=Organisation.Status.APPROVED)
    approve_selected.short_description = 'Approve selected organisations'
