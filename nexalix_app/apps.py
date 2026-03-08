from django.apps import AppConfig


class NexalixAppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "nexalix_app"

    def ready(self):
        from . import signals  # noqa: F401
