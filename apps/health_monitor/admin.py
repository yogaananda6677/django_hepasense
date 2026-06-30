from django.contrib import admin

from apps.health_monitor.models import SensorReading, VitalSign, HealthAlert


@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = ['sensor_type', 'value', 'unit', 'user', 'location',
                    'is_alert', 'recorded_at']
    list_filter = ['sensor_type', 'is_alert', 'location']
    search_fields = ['user__email', 'location']
    date_hierarchy = 'recorded_at'


@admin.register(VitalSign)
class VitalSignAdmin(admin.ModelAdmin):
    list_display = ['user', 'heart_rate', 'blood_pressure_systolic',
                    'blood_pressure_diastolic', 'oxygen_saturation',
                    'body_temperature', 'is_anomaly', 'recorded_at']
    list_filter = ['is_anomaly']
    search_fields = ['user__email']
    date_hierarchy = 'recorded_at'


@admin.register(HealthAlert)
class HealthAlertAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'alert_level', 'source_type',
                    'is_read', 'is_resolved', 'triggered_at']
    list_filter = ['alert_level', 'source_type', 'is_read', 'is_resolved']
    search_fields = ['user__email', 'title', 'message']
    date_hierarchy = 'triggered_at'
    actions = ['mark_as_read', 'mark_as_resolved']

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = 'Tandai sebagai sudah dibaca'

    def mark_as_resolved(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_resolved=True, resolved_at=timezone.now())
    mark_as_resolved.short_description = 'Tandai sebagai selesai'