"""Serializers for devices app."""

from rest_framework import serializers

from apps.devices.models import Device, DeviceSyncLog


class DeviceSerializer(serializers.ModelSerializer):
    """Serializer untuk Device."""
    device_type_display = serializers.CharField(source='get_device_type_display', read_only=True)
    connection_status_display = serializers.CharField(source='get_connection_status_display', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Device
        fields = [
            'id', 'user_email',
            'device_type', 'device_type_display',
            'device_name', 'device_model', 'serial_number', 'firmware_version',
            'connection_status', 'connection_status_display',
            'battery_level',
            'last_sync_at', 'paired_at', 'is_active', 'notes',
        ]
        read_only_fields = ['id', 'paired_at', 'user_email']


class DeviceCreateSerializer(serializers.ModelSerializer):
    """Serializer untuk pairing device baru."""

    class Meta:
        model = Device
        fields = [
            'device_type', 'device_name', 'device_model',
            'serial_number', 'firmware_version',
        ]

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return Device.objects.create(**validated_data)


class DeviceSyncLogSerializer(serializers.ModelSerializer):
    """Serializer untuk sync log."""
    sync_status_display = serializers.CharField(source='get_sync_status_display', read_only=True)

    class Meta:
        model = DeviceSyncLog
        fields = [
            'id', 'sync_status', 'sync_status_display',
            'records_synced', 'error_message', 'synced_at',
        ]
        read_only_fields = ['id']


class DeviceSyncDataSerializer(serializers.Serializer):
    """
    Serializer untuk endpoint sinkronisasi data dari device.
    Device mengirim batch data vital signs.
    """
    device_token = serializers.CharField(required=True)
    records = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False,
        max_length=500,
    )


class DeviceTokenSerializer(serializers.Serializer):
    """Response serializer saat regenerate token."""
    device_token = serializers.CharField(read_only=True)