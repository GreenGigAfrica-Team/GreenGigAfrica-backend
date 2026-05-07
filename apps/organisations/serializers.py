from rest_framework import serializers
from .models import Organisation


class OrganisationRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = ['name', 'org_type', 'cac_number', 'contact_person_name',
                  'contact_phone', 'lagos_office_address']

    def validate_cac_number(self, value):
        if Organisation.objects.filter(cac_number=value).exists():
            raise serializers.ValidationError(
                'An organisation with this CAC number is already registered.'
            )
        return value


class OrganisationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organisation
        fields = ['id', 'name', 'org_type', 'contact_person_name',
                  'contact_phone', 'lagos_office_address', 'status', 'created_at']
        read_only_fields = ['status', 'created_at']
