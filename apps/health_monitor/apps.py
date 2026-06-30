from django.apps import AppConfig


class HealthMonitorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.health_monitor'
    label = 'health_monitor'
    verbose_name = 'Health Monitor (NH3, Suhu, Kelembapan)'