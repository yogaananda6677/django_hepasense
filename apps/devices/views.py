"""
Views for devices app.

Endpoints (user-facing):
- GET    /api/v1/devices/                   : list devices user
- POST   /api/v1/devices/                   : pair new device
- GET    /api/v1/devices/{id}/              : detail device
- PATCH  /api/v1/devices/{id}/              : update device
- DELETE /api/v1/devices/{id}/              : unpair device
- POST   /api/v1/devices/{id}/sync/         : manual sync trigger
- POST   /api/v1/devices/{id}/regenerate_token/ : get new device token
- GET    /api/v1/devices/{id}/sync_logs/    : lihat sync history

- POST   /api/v1/devices/sync-data/         : endpoint untuk device push data (no JWT)
"""

import logging

from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from apps.devices.models import Device, DeviceSyncLog
from apps.devices.permissions import IsDeviceOwner
from apps.devices.serializers import (
    DeviceSerializer,
    DeviceCreateSerializer,
    DeviceSyncLogSerializer,
    DeviceSyncDataSerializer,
)

logger = logging.getLogger(__name__)


class DeviceViewSet(viewsets.ModelViewSet):
    """
    ViewSet untuk wearable device management.

    User hanya bisa manage device miliknya sendiri.
    """
    permission_classes = [IsAuthenticated, IsDeviceOwner]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['device_type', 'connection_status', 'is_active']
    ordering_fields = ['paired_at', 'last_sync_at', 'device_name']
    ordering = ['-paired_at']

    def get_queryset(self):
        return Device.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action in ['create']:
            return DeviceCreateSerializer
        return DeviceSerializer

    def perform_destroy(self, instance):
        """Soft delete: set is_active=False"""
        instance.is_active = False
        instance.save()

    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """
        POST /api/v1/devices/{id}/sync/

        Trigger manual sync. Update last_sync_at dan status.
        """
        device = self.get_object()
        device.mark_synced()

        # Log sync
        DeviceSyncLog.objects.create(
            device=device,
            sync_status='success',
            records_synced=0,
        )

        return Response({
            'message': f'Sync berhasil untuk {device.device_name}.',
            'last_sync_at': device.last_sync_at,
        })

    @action(detail=True, methods=['post'])
    def regenerate_token(self, request, pk=None):
        """
        POST /api/v1/devices/{id}/regenerate_token/

        Generate ulang device_token untuk keamanan.
        """
        device = self.get_object()
        new_token = device.regenerate_token()
        return Response({
            'message': 'Token berhasil di-regenerate.',
            'device_token': new_token,
            'warning': 'Update konfigurasi device dengan token baru ini.',
        })

    @action(detail=True, methods=['get'])
    def sync_logs(self, request, pk=None):
        """GET /api/v1/devices/{id}/sync_logs/ — lihat history sync."""
        device = self.get_object()
        logs = device.sync_logs.all()[:50]
        serializer = DeviceSyncLogSerializer(logs, many=True)
        return Response(serializer.data)


class DeviceDataSyncView(viewsets.ViewSet):
    """
    Endpoint untuk device mengirim data vital signs.
    Tidak butuh JWT - autentikasi via device_token.

    POST /api/v1/devices/sync-data/
    Body:
    {
        "device_token": "xxx",
        "records": [
            {
                "heart_rate": 72,
                "blood_pressure_systolic": 120,
                "blood_pressure_diastolic": 80,
                "oxygen_saturation": 98,
                "body_temperature": 36.6,
                "recorded_at": "2026-06-30T10:00:00Z"
            },
            ...
        ]
    }
    """
    permission_classes = [AllowAny]
    serializer_class = DeviceSyncDataSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        device_token = serializer.validated_data['device_token']
        records = serializer.validated_data['records']

        try:
            device = Device.objects.get(device_token=device_token, is_active=True)
        except Device.DoesNotExist:
            return Response(
                {'error': 'Invalid device token.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Import di sini untuk avoid circular import
        from apps.health_monitor.models import VitalSign, HealthAlert

        success_count = 0
        failed_count = 0
        errors = []

        for idx, record in enumerate(records):
            try:
                vital = VitalSign.objects.create(
                    user=device.user,
                    device=device,
                    heart_rate=record.get('heart_rate'),
                    blood_pressure_systolic=record.get('blood_pressure_systolic'),
                    blood_pressure_diastolic=record.get('blood_pressure_diastolic'),
                    oxygen_saturation=record.get('oxygen_saturation'),
                    body_temperature=record.get('body_temperature'),
                    respiratory_rate=record.get('respiratory_rate'),
                    blood_glucose=record.get('blood_glucose'),
                    steps=record.get('steps'),
                    sleep_hours=record.get('sleep_hours'),
                    calories_burned=record.get('calories_burned'),
                    recorded_at=record.get('recorded_at', timezone.now()),
                )
                if vital.check_anomaly():
                    vital.save()
                    HealthAlert.objects.create(
                        user=device.user,
                        alert_level='critical' if (
                            vital.oxygen_saturation and vital.oxygen_saturation < 92
                        ) else 'warning',
                        title='Vital sign anomali dari device',
                        message=f'Device {device.device_name} mendeteksi nilai vital tidak normal.',
                        source_type='vital',
                        source_id=vital.id,
                    )
                success_count += 1
            except Exception as e:
                failed_count += 1
                errors.append(f'Record {idx}: {str(e)}')
                logger.exception(f"Failed to sync record {idx} from device {device.id}")

        # Update device last sync & status
        device.last_sync_at = timezone.now()
        device.connection_status = 'connected' if failed_count == 0 else 'error'
        device.save(update_fields=['last_sync_at', 'connection_status'])

        # Log sync
        DeviceSyncLog.objects.create(
            device=device,
            sync_status='success' if failed_count == 0 else 'partial',
            records_synced=success_count,
            error_message='\n'.join(errors)[:500] if errors else '',
        )

        return Response({
            'message': 'Sync selesai.',
            'success_count': success_count,
            'failed_count': failed_count,
            'errors': errors[:10],  # limit error list
        }, status=status.HTTP_200_OK)