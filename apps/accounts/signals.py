"""
Signal handlers: auto-create UserProfile when a User is created.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.accounts.models import User, UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Otomatis buat UserProfile saat User baru dibuat."""
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Pastikan profile selalu ter-save."""
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        UserProfile.objects.create(user=instance)