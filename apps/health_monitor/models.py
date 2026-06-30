"""
Health Monitor models.

Berisi sensor data (NH3, suhu, kelembapan) dan vital sign user
(heart rate, blood pressure, oxygen saturation, dll).
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class SensorReading(models.Model):
    """
    Pembacaan sensor lingkungan (NH3, suhu, kelembapan).
    Berasosiasi dengan Device & lokasi (room).
    """
    SENSOR_TYPE_CHOICES = [
        ('nh3', 'Amonia (NH3)'),
        ('temperature', 'Suhu'),
        ('humidity', 'Kelembapan'),
        ('air_quality', 'Kualitas Udara'),
        ('co2', 'CO2'),
        ('pm25', 'PM2.5'),
    ]

    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.CASCADE,
        related_name='sensor_readings',
        verbose_name='Device',
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sensor_readings',
        verbose_name='User',
        null=True,
        blank=True,
    )

    sensor_type = models.CharField(
        'Tipe Sensor',
        max_length=20,
        choices=SENSOR_TYPE_CHOICES,
    )
    value = models.FloatField('Nilai Pembacaan')
    unit = models.CharField('Satuan', max_length=20, default='ppm')

    location = models.CharField(
        'Lokasi',
        max_length=100,
        blank=True,
        help_text='Contoh: Ruang Tidur, Dapur, Kantor',
    )

    is_alert = models.BooleanField(
        'Status Alert',
        default=False,
        help_text='Apakah pembacaan ini melebihi threshold',
    )
    notes = models.TextField('Catatan', blank=True)

    recorded_at = models.DateTimeField(
        'Waktu Pembacaan',
        default=timezone.now,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sensor_readings'
        verbose_name = 'Pembacaan Sensor'
        verbose_name_plural = 'Pembacaan Sensor'
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['sensor_type', '-recorded_at']),
            models.Index(fields=['user', '-recorded_at']),
            models.Index(fields=['is_alert', '-recorded_at']),
        ]

    def __str__(self):
        return f"{self.get_sensor_type_display()} = {self.value} {self.unit} @ {self.recorded_at:%Y-%m-%d %H:%M}"

    def check_threshold(self):
        """Cek apakah nilai melewati threshold dari settings."""
        from django.conf import settings as dj_settings
        thresholds = dj_settings.HEALTH_THRESHOLDS
        # Map sensor_type ke threshold key yang sesuai
        key_map = {
            'nh3': 'nh3',
            'temperature': 'temperature_ambient',  # Sensor = ambient, vital = body
            'humidity': 'humidity',
            'co2': 'co2',
            'pm25': 'pm25',
            'air_quality': 'air_quality',
        }
        threshold_key = key_map.get(self.sensor_type, self.sensor_type)
        threshold = thresholds.get(threshold_key, {})
        if 'max' in threshold and self.value > threshold['max']:
            self.is_alert = True
        elif 'min' in threshold and self.value < threshold['min']:
            self.is_alert = True
        return self.is_alert


class VitalSign(models.Model):
    """
    Vital sign user: detak jantung, tekanan darah, saturasi oksigen, suhu tubuh.
    Bisa auto-sync dari wearable atau input manual.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vital_signs',
        verbose_name='User',
    )
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.SET_NULL,
        related_name='vital_signs',
        verbose_name='Source Device',
        null=True,
        blank=True,
    )

    # Vital sign fields (nullable - bisa partial record)
    heart_rate = models.PositiveIntegerField(
        'Detak Jantung (bpm)',
        null=True,
        blank=True,
    )
    blood_pressure_systolic = models.PositiveIntegerField(
        'Tekanan Darah Sistolik (mmHg)',
        null=True,
        blank=True,
    )
    blood_pressure_diastolic = models.PositiveIntegerField(
        'Tekanan Darah Diastolik (mmHg)',
        null=True,
        blank=True,
    )
    oxygen_saturation = models.FloatField(
        'Saturasi Oksigen (%)',
        null=True,
        blank=True,
    )
    body_temperature = models.FloatField(
        'Suhu Tubuh (°C)',
        null=True,
        blank=True,
    )
    respiratory_rate = models.PositiveIntegerField(
        'Laju Pernapasan (/menit)',
        null=True,
        blank=True,
    )
    blood_glucose = models.FloatField(
        'Gula Darah (mg/dL)',
        null=True,
        blank=True,
    )
    weight = models.FloatField(
        'Berat Badan (kg)',
        null=True,
        blank=True,
    )
    steps = models.PositiveIntegerField(
        'Langkah',
        null=True,
        blank=True,
    )
    sleep_hours = models.FloatField(
        'Durasi Tidur (jam)',
        null=True,
        blank=True,
    )
    calories_burned = models.PositiveIntegerField(
        'Kalori Terbakar',
        null=True,
        blank=True,
    )

    is_anomaly = models.BooleanField(
        'Anomali',
        default=False,
        help_text='Apakah ada nilai yang tidak normal',
    )
    notes = models.TextField('Catatan', blank=True)

    recorded_at = models.DateTimeField('Waktu Record', default=timezone.now, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'vital_signs'
        verbose_name = 'Vital Sign'
        verbose_name_plural = 'Vital Signs'
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['user', '-recorded_at']),
            models.Index(fields=['is_anomaly', '-recorded_at']),
        ]

    def __str__(self):
        return f"Vitals - {self.user.email} @ {self.recorded_at:%Y-%m-%d %H:%M}"

    def check_anomaly(self):
        """Cek apakah ada nilai vital yang melewati threshold."""
        from django.conf import settings as dj_settings
        thresholds = dj_settings.HEALTH_THRESHOLDS
        anomaly = False

        if (self.heart_rate is not None and
                (self.heart_rate < thresholds['heart_rate']['min'] or
                 self.heart_rate > thresholds['heart_rate']['max'])):
            anomaly = True
        if (self.blood_pressure_systolic is not None and
                (self.blood_pressure_systolic < thresholds['blood_pressure_systolic']['min'] or
                 self.blood_pressure_systolic > thresholds['blood_pressure_systolic']['max'])):
            anomaly = True
        if (self.blood_pressure_diastolic is not None and
                (self.blood_pressure_diastolic < thresholds['blood_pressure_diastolic']['min'] or
                 self.blood_pressure_diastolic > thresholds['blood_pressure_diastolic']['max'])):
            anomaly = True
        if (self.oxygen_saturation is not None and
                self.oxygen_saturation < thresholds['oxygen_saturation']['min']):
            anomaly = True
        if (self.body_temperature is not None and
                (self.body_temperature < thresholds['temperature']['min'] or
                 self.body_temperature > thresholds['temperature']['max'])):
            anomaly = True

        self.is_anomaly = anomaly
        return anomaly


class HealthAlert(models.Model):
    """Alert/notifikasi ketika ada nilai yang abnormal."""
    ALERT_LEVEL_CHOICES = [
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='health_alerts',
        verbose_name='User',
    )

    alert_level = models.CharField(
        'Level Alert',
        max_length=10,
        choices=ALERT_LEVEL_CHOICES,
        default='warning',
    )
    title = models.CharField('Judul', max_length=200)
    message = models.TextField('Pesan')

    source_type = models.CharField(
        'Tipe Source',
        max_length=20,
        choices=[
            ('sensor', 'Sensor'),
            ('vital', 'Vital Sign'),
            ('system', 'System'),
        ],
        default='sensor',
    )
    source_id = models.PositiveIntegerField('Source ID', null=True, blank=True)

    is_read = models.BooleanField('Sudah Dibaca', default=False)
    is_resolved = models.BooleanField('Selesai', default=False)

    triggered_at = models.DateTimeField('Waktu Trigger', default=timezone.now)
    resolved_at = models.DateTimeField('Waktu Resolved', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'health_alerts'
        verbose_name = 'Health Alert'
        verbose_name_plural = 'Health Alerts'
        ordering = ['-triggered_at']
        indexes = [
            models.Index(fields=['user', '-triggered_at']),
            models.Index(fields=['is_read', '-triggered_at']),
            models.Index(fields=['alert_level', '-triggered_at']),
        ]

    def __str__(self):
        return f"[{self.alert_level.upper()}] {self.title}"