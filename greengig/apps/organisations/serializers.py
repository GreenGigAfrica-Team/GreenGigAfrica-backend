"""Organisation serializers."""
from rest_framework import serializers
from .models import Organisation


class OrganisationRegisterSerializer(serializers.ModelSerializer):
    """Used during organisation onboarding (US-06)."""

    class Meta:
        model = Organisation
        fields = [
            "name",
            "org_type",
            "cac_number",
            "contact_person_name",
            "contact_phone",
            "lagos_office_address",
            "website",
            "description",
            "logo",
        ]

    def validate_cac_number(self, value):
        if Organisation.objects.filter(cac_number=value).exists():
            raise serializers.ValidationError(
                "An organisation with this CAC number is already registered."
            )
        return value


class OrganisationSerializer(serializers.ModelSerializer):
    """Read serializer — safe for public consumption."""

    class Meta:
        model = Organisation
        fields = [
            "id",
            "name",
            "org_type",
            "contact_person_name",
            "contact_phone",
            "lagos_office_address",
            "website",
            "description",
            "logo",
            "status",
            "created_at",
        ]
        read_only_fields = ["status", "created_at"]


class OrganisationAdminSerializer(serializers.ModelSerializer):
    """Full serializer for GreenGig admin review."""

    class Meta:
        model = Organisation
        fields = "__all__"
