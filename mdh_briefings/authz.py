"""Eric-only access for MDH leadership briefings."""

from __future__ import annotations

from django.conf import settings


def is_mdh_briefings_owner(user) -> bool:
    if not user.is_authenticated:
        return False
    raw_id = getattr(settings, 'MDH_BRIEFINGS_OWNER_USER_ID', None)
    if raw_id is not None and str(raw_id).strip() != '':
        try:
            return user.pk == int(str(raw_id).strip())
        except (TypeError, ValueError):
            return False
    name = (getattr(settings, 'MDH_BRIEFINGS_OWNER_USERNAME', '') or '').strip()
    if name:
        return user.username == name
    return False


def mdh_briefings_configured() -> bool:
    raw_id = getattr(settings, 'MDH_BRIEFINGS_OWNER_USER_ID', None)
    if raw_id is not None and str(raw_id).strip() != '':
        return True
    return bool((getattr(settings, 'MDH_BRIEFINGS_OWNER_USERNAME', '') or '').strip())
