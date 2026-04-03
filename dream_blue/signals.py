"""Append-only rent roll log when lease amounts or sf change."""

from decimal import Decimal

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import BusinessCalendarEvent, BusinessCalendarEventType, LeaseRentRollChange


@receiver(pre_save, sender=BusinessCalendarEvent)
def _cache_calendar_event_before_save(sender, instance, **kwargs):
    if not instance.pk:
        instance._dream_blue_pre_save_snapshot = None
        return
    try:
        instance._dream_blue_pre_save_snapshot = BusinessCalendarEvent.objects.get(pk=instance.pk)
    except BusinessCalendarEvent.DoesNotExist:
        instance._dream_blue_pre_save_snapshot = None


@receiver(post_save, sender=BusinessCalendarEvent)
def _log_lease_rent_roll_change(sender, instance, created, **kwargs):
    if instance.event_type != BusinessCalendarEventType.LEASE:
        return
    if created:
        return
    old = getattr(instance, '_dream_blue_pre_save_snapshot', None)
    if old is None:
        return

    def _eq_dec(a, b):
        if a is None and b is None:
            return True
        if a is None or b is None:
            return False
        return Decimal(str(a)) == Decimal(str(b))

    changed = (
        not _eq_dec(old.amount, instance.amount)
        or old.square_footage != instance.square_footage
        or old.square_footage_storage != instance.square_footage_storage
    )
    if not changed:
        return

    LeaseRentRollChange.objects.create(
        event=instance,
        amount_before=old.amount,
        amount_after=instance.amount,
        square_footage_before=old.square_footage,
        square_footage_after=instance.square_footage,
        square_footage_storage_before=old.square_footage_storage,
        square_footage_storage_after=instance.square_footage_storage,
        source='admin',
    )
