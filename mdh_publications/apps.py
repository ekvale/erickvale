from django.apps import AppConfig
from django.db.models.signals import post_migrate


class MdhPublicationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mdh_publications"
    verbose_name = "MDH Publications Library"

    def ready(self):
        from . import signals  # noqa: F401
        # Defer DB access to post_migrate so it never runs during app
        # initialisation (which causes RuntimeWarning on worker startup).
        post_migrate.connect(_bootstrap_groups, sender=self)


def _bootstrap_groups(sender, **kwargs):
    """Create/update MDH Publications permission groups after migrations."""
    try:
        from .permissions import bootstrap_publication_groups
        bootstrap_publication_groups()
    except Exception:
        # Swallow errors during the very first migration when the
        # auth/contenttypes tables may not yet exist.
        pass