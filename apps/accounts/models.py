"""
User & Profile models for HepaSense.

Custom User model using email as the unique identifier (no username).
Includes UserProfile for extended info and OTPDevice integration for 2FA.
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone


class UserManager(BaseUserManager):
    """
    Custom manager for User model.
    Email is the unique identifier (no username).
    """

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email wajib diisi')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser harus memiliki is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser harus memiliki is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom User Model untuk HepaSense. Login via email."""

    GENDER_CHOICES = [
        ('M', 'Laki-laki'),
        ('F', 'Perempuan'),
        ('O', 'Lainnya'),
    ]

    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Format nomor telepon: '+628123456789'. Maks 15 digit."
    )

    # Hapus field username default dari AbstractUser
    username = None

    email = models.EmailField(
        'Email Address',
        unique=True,
        error_messages={'unique': 'Email ini sudah terdaftar di sistem.'}
    )

    phone_number = models.CharField(
        'Nomor Telepon',
        max_length=20,
        validators=[phone_regex],
        blank=True,
        null=True,
        unique=True,
    )
    date_of_birth = models.DateField('Tanggal Lahir', blank=True, null=True)
    gender = models.CharField(
        'Jenis Kelamin',
        max_length=1,
        choices=GENDER_CHOICES,
        blank=True,
    )
    avatar = models.ImageField(
        'Foto Profil',
        upload_to='avatars/',
        blank=True,
        null=True,
    )

    is_patient = models.BooleanField('Pasien', default=True)
    is_doctor = models.BooleanField('Dokter', default=False)

    two_factor_enabled = models.BooleanField(
        '2FA Aktif',
        default=False,
        help_text='Apakah Two-Factor Authentication aktif'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return self.get_full_name() or self.email

    @property
    def age(self):
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None

    def get_full_name(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.email


class UserProfile(models.Model):
    """Extended user profile (alamat, kontak darurat, preferensi)."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='User',
    )

    address = models.TextField('Alamat Lengkap', blank=True)
    city = models.CharField('Kota', max_length=100, blank=True)
    province = models.CharField('Provinsi', max_length=100, blank=True)
    postal_code = models.CharField('Kode Pos', max_length=10, blank=True)

    emergency_contact_name = models.CharField(
        'Nama Kontak Darurat',
        max_length=100,
        blank=True,
    )
    emergency_contact_phone = models.CharField(
        'No. Telp Kontak Darurat',
        max_length=20,
        blank=True,
    )
    emergency_contact_relation = models.CharField(
        'Hubungan',
        max_length=50,
        blank=True,
        help_text='Contoh: Ayah, Ibu, Saudara, Teman'
    )

    LANGUAGE_CHOICES = [
        ('id', 'Bahasa Indonesia'),
        ('en', 'English'),
    ]
    preferred_language = models.CharField(
        'Bahasa Preferensi',
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default='id',
    )
    notification_preferences = models.JSONField(
        'Preferensi Notifikasi',
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'Profil User'
        verbose_name_plural = 'Profil Users'

    def __str__(self):
        return f"Profil - {self.user.email}"