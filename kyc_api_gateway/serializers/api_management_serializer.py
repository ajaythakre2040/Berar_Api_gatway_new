from django.utils import timezone
from rest_framework import serializers
from kyc_api_gateway.models.api_management import ApiManagement
from kyc_api_gateway.models.vendor_management import VendorManagement
from kyc_api_gateway.models.supported_vendor import SupportedVendor


class ApiManagementSerializer(serializers.ModelSerializer):
    supported_vendors = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True
    )
    supported_vendor_ids = serializers.SerializerMethodField(read_only=True)
    vendor_name = serializers.CharField(source='vendor.vendor_name', read_only=True)  

    class Meta:
        model = ApiManagement
        exclude = (
            "created_by",
            "updated_by",
            "deleted_by",
            "created_at",
            "updated_at",
            "deleted_at",
        )

    def get_supported_vendor_ids(self, obj):
        return list(
            SupportedVendor.objects.filter(
                api=obj, deleted_at__isnull=True
            ).values_list("vendor_id", flat=True)
        )

    def create(self, validated_data):
        supported_vendors = validated_data.pop("supported_vendors", [])
        user_id = self.context["request"].user.id
        api = ApiManagement.objects.create(**validated_data, created_by=user_id)

        for vendor_id in supported_vendors:
            SupportedVendor.objects.create(
                api=api, vendor_id=vendor_id, created_by=user_id
            )
        return api

    def update(self, instance, validated_data):
        supported_vendors = validated_data.pop("supported_vendors", None)
        user_id = self.context["request"].user.id

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.updated_by = user_id
        instance.save()

        if supported_vendors is not None:
            # Delete old ones
            # SupportedVendor.objects.filter(api=instance).delete()
            SupportedVendor.objects.filter(
                api=instance, deleted_at__isnull=True
            ).update(deleted_at=timezone.now(), deleted_by=user_id)
        #     for vendor_id in supported_vendors:
        #         SupportedVendor.objects.create(
        #             api=instance, vendor_id=vendor_id, created_by=user_id
        #         )

        # return instance
        for vendor_id in supported_vendors:
            existing = SupportedVendor.objects.filter(
                api=instance, vendor_id=vendor_id
            ).first()
            if existing:
                # Reactivate if it was soft-deleted
                existing.deleted_at = None
                existing.deleted_by = None
                existing.updated_by = user_id
                existing.updated_at = timezone.now()
                existing.save()
            else:
                SupportedVendor.objects.create(
                    api=instance, vendor_id=vendor_id, created_by=user_id
                )

        return instance
