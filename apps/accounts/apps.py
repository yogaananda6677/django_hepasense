from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    label = 'accounts'
    verbose_name = 'User Accounts'

    def ready(self):
        # Import signal handlers
        try:
            from apps.accounts import signals  # noqa: F401
        except ImportError:
            pass