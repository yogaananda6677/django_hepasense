"""
Management command: seed demo data untuk health monitoring.

Usage:
    python manage.py seed_demo_data
    python manage.py seed_demo_data --email=test@example.com
"""

import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import User
from apps.devices.models import Device
from apps.health_monitor.models import SensorReading, VitalSign


class Command(BaseCommand):
    help = 'Seed demo data sensor readings & vital signs untuk testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            default='demo@hepasense.com',
            help='Email user untuk demo data',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Jumlah hari ke belakang untuk generate data',
        )

    def handle(self, *args, **options):
        email = options['email']
        days = options['days']

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': 'Demo',
                'last_name': 'User',
                'is_active': True,
            },
        )
        if created:
            user.set_password('demo123456')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'User demo dibuat: {email} / demo123456'))
        else:
            self.stdout.write(f'User demo sudah ada: {email}')

        # Buat dummy device kalau belum ada
        device, _ = Device.objects.get_or_create(
            user=user,
            serial_number='DEMO-DEVICE-001',
            defaults={
                'device_type': 'apple_watch',
                'device_name': 'Demo Apple Watch',
                'device_model': 'Series 9',
                'connection_status': 'connected',
                'battery_level': 85,
            },
        )

        # Generate sensor readings (NH3, temperature, humidity)
        now = timezone.now()
        sensor_data = []
        for day in range(days):
            for hour in [0, 6, 12, 18]:
                ts = now - timedelta(days=day, hours=24 - hour)
                # NH3: 5-30 ppm (normal < 25)
                nh3 = round(random.uniform(5, 35), 2)
                sensor_data.append(SensorReading(
                    user=user, device=device,
                    sensor_type='nh3', value=nh3, unit='ppm',
                    location='Ruang Tidur',
                    recorded_at=ts,
                ))
                # Temperature: 22-30°C
                temp = round(random.uniform(22, 30), 1)
                sensor_data.append(SensorReading(
                    user=user, device=device,
                    sensor_type='temperature', value=temp, unit='°C',
                    location='Ruang Tidur',
                    recorded_at=ts,
                ))
                # Humidity: 40-80%
                hum = round(random.uniform(40, 80), 1)
                sensor_data.append(SensorReading(
                    user=user, device=device,
                    sensor_type='humidity', value=hum, unit='%',
                    location='Ruang Tidur',
                    recorded_at=ts,
                ))

        # Apply threshold check
        for reading in sensor_data:
            reading.check_threshold()
        SensorReading.objects.bulk_create(sensor_data, ignore_conflicts=True)

        # Generate vital signs
        vital_data = []
        for day in range(days):
            ts = now - timedelta(days=day)
            vital_data.append(VitalSign(
                user=user, device=device,
                heart_rate=random.randint(60, 100),
                blood_pressure_systolic=random.randint(110, 135),
                blood_pressure_diastolic=random.randint(70, 85),
                oxygen_saturation=round(random.uniform(95, 100), 1),
                body_temperature=round(random.uniform(36.2, 37.0), 1),
                steps=random.randint(3000, 12000),
                sleep_hours=round(random.uniform(5, 9), 1),
                calories_burned=random.randint(1500, 2500),
                recorded_at=ts,
            ))

        for vital in vital_data:
            vital.check_anomaly()
        VitalSign.objects.bulk_create(vital_data, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(
            f'\nSelesai! {len(sensor_data)} sensor readings & '
            f'{len(vital_data)} vital signs untuk {email}'
        ))