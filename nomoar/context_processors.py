from django.conf import settings


def nomoar_banner(request):
    """Editorial / corrections context for NOMOAR routes only."""
    path = getattr(request, 'path', '') or ''
    if not path.startswith('/apps/nomoar'):
        return {}
    return {
        'nomoar_corrections_email': getattr(settings, 'NOMOAR_CORRECTIONS_EMAIL', '') or '',
    }


def nomoar_engagement(request):
    """Donation / support copy from admin (singleton) on NOMOAR routes."""
    path = getattr(request, 'path', '') or ''
    if not path.startswith('/apps/nomoar'):
        return {}
    from .models import EngagementConfig

    return {'nomoar_engagement': EngagementConfig.get_solo()}
