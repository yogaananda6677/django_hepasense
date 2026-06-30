from django.contrib import admin

from apps.devices.models import Device, DeviceSyncLog


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ['device_name', 'device_type', 'user', 'connection_status',
                    'battery_level', 'last_sync_at', 'paired_at', 'is_active']
    list_filter = ['device_type', 'connection_status', 'is_active']
    search_fields = ['user__email', 'device_name', 'serial_number']
    date_hierarchy = 'paired_at'
    readonly_fields = ['device_token', 'paired_at', 'last_sync_at']


@admin.register(DeviceSyncLog)
class DeviceSyncLogAdmin(admin.ModelAdmin):
    list_display = ['device', 'sync_status', 'records_synced', 'synced_at']
    list_filter = ['sync_status']
    search_fields = ['device__device_name', 'device__user__email']
    date_hierarchy = 'synced_at'