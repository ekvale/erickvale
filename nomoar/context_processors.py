from django.conf import settings


def nomoar_banner(request):
    """Editorial / corrections context for NOMOAR routes only."""
    path = getattr(request, 'path', '') or ''
    if not path.startswith('/apps/nomoar'):
        return {}
    return {
        'nomoar_corrections_email': getattr(settings, 'NOMOAR_CORRECTIONS_EMAIL', '') or '',
    }
