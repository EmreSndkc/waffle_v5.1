from django.apps import AppConfig


class OutcomesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'outcomes'
    verbose_name = 'Program Çıktıları'

    def ready(self):
        from . import signals  # noqa: F401  (tetikleyicileri kaydeder)
