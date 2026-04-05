"""Shared braindump email helpers (owner user + recipient list)."""

from __future__ import annotations

from django.conf import settings
from django.contrib.auth import get_user_model

from dream_blue.emailing import parse_recipient_list


def get_braindump_owner():
    """Return the User configured as braindump owner, or None."""
    User = get_user_model()
    raw_id = getattr(settings, 'BRAINDUMP_OWNER_USER_ID', None)
    if raw_id is not None and str(raw_id).strip() != '':
        try:
            return User.objects.get(pk=int(str(raw_id).strip()))
        except (User.DoesNotExist, ValueError, TypeError):
            return None
    name = (getattr(settings, 'BRAINDUMP_OWNER_USERNAME', '') or '').strip()
    if name:
        return User.objects.filter(username=name).first()
    return None


def get_braindump_recipients(owner) -> list[str]:
    raw = (getattr(settings, 'BRAINDUMP_CALENDAR_EMAIL_RECIPIENTS', '') or '').strip()
    if raw:
        return parse_recipient_list(raw)
    if owner and owner.email:
        return [owner.email.strip()]
    return []
