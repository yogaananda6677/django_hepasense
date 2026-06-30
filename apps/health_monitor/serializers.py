"""Serializers for health monitor app."""

from rest_framework import serializers

from apps.health_monitor.models import SensorReading, VitalSign, HealthAlert


class SensorReadingSerializer(serializers.ModelSerializer):
    """Serializer untuk SensorReading."""
    sensor_type_display = serializers.CharField(source='get_sensor_type_display', read_only=True)

    class Meta:
        model = SensorReading
        fields = [
            'id', 'sensor_type', 'sensor_type_display', 'value', 'unit',
            'location', 'is_alert', 'notes', 'recorded_at', 'created_at',
        ]
        read_only_fields = ['id', 'is_alert', 'created_at']


class VitalSignSerializer(serializers.ModelSerializer):
    """Serializer untuk VitalSign."""
    has_anomaly = serializers.BooleanField(source='is_anomaly', read_only=True)

    class Meta:
        model = VitalSign
        fields = [
            'id',
            'heart_rate',
            'blood_pressure_systolic',
            'blood_pressure_diastolic',
            'oxygen_saturation',
            'body_temperature',
            'respiratory_rate',
            'blood_glucose',
            'weight',
            'steps',
            'sleep_hours',
            'calories_burned',
            'is_anomaly',
            'has_anomaly',
            'notes',
            'recorded_at',
            'created_at',
        ]
        read_only_fields = ['id', 'is_anomaly', 'created_at']


class HealthAlertSerializer(serializers.ModelSerializer):
    """Serializer untuk HealthAlert."""
    alert_level_display = serializers.CharField(source='get_alert_level_display', read_only=True)
    source_type_display = serializers.CharField(source='get_source_type_display', read_only=True)

    class Meta:
        model = HealthAlert
        fields = [
            'id', 'alert_level', 'alert_level_display',
            'source_type', 'source_type_display', 'source_id',
            'title', 'message',
            'is_read', 'is_resolved',
            'triggered_at', 'resolved_at', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class DashboardSummarySerializer(serializers.Serializer):
    """Serializer untuk dashboard summary (response only)."""
    latest_sensor = SensorReadingSerializer(many=True)
    latest_vitals = VitalSignSerializer(many=True)
    active_alerts = HealthAlertSerializer(many=True)
    sensor_stats = serializers.DictField()
    vitals_stats = serializers.DictField()