from django.apps import AppConfig


class DreamBlueConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dream_blue'
    verbose_name = 'Dream Blue'

    def ready(self):
        from . import signals  # noqa: F401
