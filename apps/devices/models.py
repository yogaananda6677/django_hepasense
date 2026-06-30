"""Models for devices app (wearable integration)."""

import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone


def generate_device_token():
    """Generate secure device token."""
    return secrets.token_urlsafe(48)


class Device(models.Model):
    """Wearable device yang terhubung ke user."""
    DEVICE_TYPE_CHOICES = [
        ('apple_watch', 'Apple Watch'),
        ('garmin', 'Garmin'),
        ('fitbit', 'Fitbit'),
        ('mi_band', 'Mi Band'),
        ('samsung', 'Samsung Galaxy Watch'),
        ('xiaomi', 'Xiaomi'),
        ('other', 'Lainnya'),
    ]
    CONNECTION_STATUS_CHOICES = [
        ('connected', 'Connected'),
        ('disconnected', 'Disconnected'),
        ('pairing', 'Pairing'),
        ('error', 'Error'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='devices',
        verbose_name='User',
    )

    device_type = models.CharField('Tipe Device', max_length=20,
                                    choices=DEVICE_TYPE_CHOICES)
    device_name = models.CharField('Nama Device', max_length=100)
    device_model = models.CharField('Model', max_length=100, blank=True)
    serial_number = models.CharField('Serial Number', max_length=100, blank=True)
    firmware_version = models.CharField('Firmware', max_length=50, blank=True)

    connection_status = models.CharField(
        'Status Koneksi',
        max_length=15,
        choices=CONNECTION_STATUS_CHOICES,
        default='disconnected',
    )
    battery_level = models.PositiveIntegerField(
        'Baterai (%)',
        null=True, blank=True,
        validators=[],
    )

    device_token = models.CharField(
        'Device Token',
        max_length=64,
        unique=True,
        default=generate_device_token,
        help_text='Token untuk autentikasi device (API key)',
    )

    last_sync_at = models.DateTimeField('Sync Terakhir', null=True, blank=True)
    paired_at = models.DateTimeField('Waktu Pairing', auto_now_add=True)
    is_active = models.BooleanField('Aktif', default=True)
    notes = models.TextField('Catatan', blank=True)

    class Meta:
        db_table = 'devices'
        verbose_name = 'Device'
        verbose_name_plural = 'Devices'
        ordering = ['-paired_at']
        indexes = [
            models.Index(fields=['user', '-paired_at']),
            models.Index(fields=['device_type']),
            models.Index(fields=['connection_status']),
        ]
        unique_together = [['user', 'serial_number']]

    def __str__(self):
        return f"{self.get_device_type_display()} - {self.device_name} ({self.user.email})"

    def regenerate_token(self):
        self.device_token = generate_device_token()
        self.save(update_fields=['device_token'])
        return self.device_token

    def mark_synced(self):
        self.last_sync_at = timezone.now()
        self.connection_status = 'connected'
        self.save(update_fields=['last_sync_at', 'connection_status'])


class DeviceSyncLog(models.Model):
    """Log sync data dari device."""
    SYNC_STATUS_CHOICES = [
        ('success', 'Success'),
        ('partial', 'Partial Success'),
        ('failed', 'Failed'),
    ]

    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='sync_logs',
        verbose_name='Device',
    )
    sync_status = models.CharField(
        'Status Sync',
        max_length=10,
        choices=SYNC_STATUS_CHOICES,
    )
    records_synced = models.PositiveIntegerField('Records Synced', default=0)
    error_message = models.TextField('Error', blank=True)

    synced_at = models.DateTimeField('Waktu Sync', default=timezone.now)

    class Meta:
        db_table = 'device_sync_logs'
        verbose_name = 'Sync Log'
        verbose_name_plural = 'Sync Logs'
        ordering = ['-synced_at']
        indexes = [
            models.Index(fields=['device', '-synced_at']),
        ]

    def __str__(self):
        return f"{self.device.device_name} - {self.sync_status} @ {self.synced_at:%Y-%m-%d %H:%M}"