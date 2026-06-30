"""
Views for health monitor app.

Endpoints:
- SensorReadingViewSet    : CRUD untuk sensor reading
- VitalSignViewSet        : CRUD untuk vital sign
- HealthAlertViewSet      : list & manage alerts
- DashboardSummaryView    : aggregated data untuk dashboard
"""

from datetime import timedelta

from django.db.models import Avg, Max, Min, Count, Q
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from apps.health_monitor.models import SensorReading, VitalSign, HealthAlert
from apps.health_monitor.serializers import (
    SensorReadingSerializer,
    VitalSignSerializer,
    HealthAlertSerializer,
    DashboardSummarySerializer,
)


class SensorReadingViewSet(viewsets.ModelViewSet):
    """
    ViewSet untuk sensor reading (NH3, suhu, kelembapan, dll).

    list    : GET    /api/v1/health-monitor/sensors/
    create  : POST   /api/v1/health-monitor/sensors/
    retrieve: GET    /api/v1/health-monitor/sensors/{id}/
    update  : PUT    /api/v1/health-monitor/sensors/{id}/
    partial : PATCH  /api/v1/health-monitor/sensors/{id}/
    destroy : DELETE /api/v1/health-monitor/sensors/{id}/

    Filters: ?sensor_type=nh3&location=Ruang%20Tidur&is_alert=true
    """
    serializer_class = SensorReadingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['sensor_type', 'location', 'is_alert', 'device']
    ordering_fields = ['recorded_at', 'value']
    ordering = ['-recorded_at']

    def get_queryset(self):
        """User hanya bisa lihat reading miliknya sendiri."""
        return SensorReading.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        reading = serializer.save(user=self.request.user)
        # Auto-check threshold dan flag alert
        if reading.check_threshold():
            reading.save()
            HealthAlert.objects.create(
                user=self.request.user,
                alert_level='critical' if reading.sensor_type == 'nh3' else 'warning',
                title=f"{reading.get_sensor_type_display()} tidak normal",
                message=f"Pembacaan {reading.get_sensor_type_display()} = "
                        f"{reading.value} {reading.unit} di {reading.location or 'Lokasi tidak diketahui'}. "
                        f"Segera lakukan tindakan!",
                source_type='sensor',
                source_id=reading.id,
            )


class VitalSignViewSet(viewsets.ModelViewSet):
    """
    ViewSet untuk vital sign user.

    list    : GET    /api/v1/health-monitor/vitals/
    create  : POST   /api/v1/health-monitor/vitals/
    retrieve: GET    /api/v1/health-monitor/vitals/{id}/
    update  : PUT    /api/v1/health-monitor/vitals/{id}/
    partial : PATCH  /api/v1/health-monitor/vitals/{id}/
    destroy : DELETE /api/v1/health-monitor/vitals/{id}/

    Filters: ?is_anomaly=true
    """
    serializer_class = VitalSignSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_anomaly']
    ordering_fields = ['recorded_at', 'heart_rate', 'body_temperature']
    ordering = ['-recorded_at']

    def get_queryset(self):
        return VitalSign.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        vital = serializer.save(user=self.request.user)
        if vital.check_anomaly():
            vital.save()
            HealthAlert.objects.create(
                user=self.request.user,
                alert_level='critical' if vital.oxygen_saturation and vital.oxygen_saturation < 92 else 'warning',
                title="Vital sign tidak normal",
                message="Ada nilai vital sign yang melewati ambang batas normal. "
                        "Perhatikan kondisi Anda.",
                source_type='vital',
                source_id=vital.id,
            )

    @action(detail=False, methods=['get'])
    def latest(self, request):
        """GET /api/v1/health-monitor/vitals/latest/ — vital sign terbaru."""
        latest = self.get_queryset().first()
        if not latest:
            return Response({'detail': 'Belum ada data vital sign.'},
                            status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(latest)
        return Response(serializer.data)


class HealthAlertViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet untuk health alerts (read-only untuk user).

    list    : GET /api/v1/health-monitor/alerts/
    retrieve: GET /api/v1/health-monitor/alerts/{id}/

    Filters: ?is_read=false&alert_level=critical

    Actions:
    - mark_read     : POST /api/v1/health-monitor/alerts/{id}/mark_read/
    - mark_resolved : POST /api/v1/health-monitor/alerts/{id}/mark_resolved/
    """
    serializer_class = HealthAlertSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['alert_level', 'is_read', 'is_resolved', 'source_type']
    ordering_fields = ['triggered_at']
    ordering = ['-triggered_at']

    def get_queryset(self):
        return HealthAlert.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        alert = self.get_object()
        alert.is_read = True
        alert.save()
        return Response({'status': 'marked as read'})

    @action(detail=True, methods=['post'])
    def mark_resolved(self, request, pk=None):
        alert = self.get_object()
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.save()
        return Response({'status': 'resolved'})

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """GET /api/v1/health-monitor/alerts/unread_count/"""
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'unread_count': count})


class DashboardSummaryView(APIView):
    """
    GET /api/v1/health-monitor/dashboard/

    Aggregated dashboard data:
    - Latest sensor readings (NH3, temperature, humidity)
    - Latest vital signs
    - Active alerts
    - 7-day statistics
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        now = timezone.now()
        seven_days_ago = now - timedelta(days=7)

        # Latest readings per sensor type
        latest_sensor = []
        for sensor_type, _ in SensorReading.SENSOR_TYPE_CHOICES:
            latest = SensorReading.objects.filter(
                user=user, sensor_type=sensor_type
            ).first()
            if latest:
                latest_sensor.append(latest)

        # Latest vital
        latest_vitals = VitalSign.objects.filter(user=user)[:5]

        # Active alerts (unread & not resolved)
        active_alerts = HealthAlert.objects.filter(
            user=user, is_resolved=False
        )[:10]

        # Stats (7 hari terakhir)
        sensor_qs = SensorReading.objects.filter(user=user, recorded_at__gte=seven_days_ago)
        sensor_stats = {}
        for stype, _ in SensorReading.SENSOR_TYPE_CHOICES:
            stats = sensor_qs.filter(sensor_type=stype).aggregate(
                avg=Avg('value'), max=Max('value'), min=Min('value'),
                count=Count('id'),
            )
            if stats['count']:
                sensor_stats[stype] = {k: round(v, 2) if isinstance(v, float) else v
                                        for k, v in stats.items()}

        vitals_qs = VitalSign.objects.filter(user=user, recorded_at__gte=seven_days_ago)
        vitals_stats = {
            'avg_heart_rate': vitals_qs.aggregate(avg=Avg('heart_rate'))['avg'],
            'avg_systolic': vitals_qs.aggregate(avg=Avg('blood_pressure_systolic'))['avg'],
            'avg_diastolic': vitals_qs.aggregate(avg=Avg('blood_pressure_diastolic'))['avg'],
            'avg_oxygen': vitals_qs.aggregate(avg=Avg('oxygen_saturation'))['avg'],
            'avg_temp': vitals_qs.aggregate(avg=Avg('body_temperature'))['avg'],
            'total_records': vitals_qs.count(),
        }
        # Round floats
        vitals_stats = {k: round(v, 2) if isinstance(v, float) else v
                         for k, v in vitals_stats.items()}

        data = {
            'latest_sensor': latest_sensor,
            'latest_vitals': latest_vitals,
            'active_alerts': active_alerts,
            'sensor_stats': sensor_stats,
            'vitals_stats': vitals_stats,
        }
        serializer = DashboardSummarySerializer(data)
        return Response(serializer.data)