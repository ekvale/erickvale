# Annual fire sprinkler (Dec 18) and fire alarm (Jan 8) inspections through 2036.

from datetime import date

from django.db import migrations


def seed_inspections(apps, schema_editor):
    Event = apps.get_model('dream_blue', 'BusinessCalendarEvent')
    T_MAINT = 'maintenance'
    years = range(2026, 2037)  # inclusive 2026–2036
    for y in years:
        Event.objects.create(
            title='Fire sprinkler inspection (annual)',
            event_type=T_MAINT,
            due_date=date(y, 12, 18),
            end_date=None,
            amount=None,
            property_label='401 Beltrami Ave',
            notes='Annual inspection; schedule with LNC.',
            contact_info='LNC',
            account_reference='',
            is_active=True,
            sort_order=520,
        )
        Event.objects.create(
            title='Fire alarm system inspection (annual)',
            event_type=T_MAINT,
            due_date=date(y, 1, 8),
            end_date=None,
            amount=None,
            property_label='401 Beltrami Ave',
            notes='Annual inspection; schedule with Bonded Lock and Key.',
            contact_info='Bonded Lock and Key — Bemidji',
            account_reference='',
            is_active=True,
            sort_order=521,
        )


def unseed_inspections(apps, schema_editor):
    Event = apps.get_model('dream_blue', 'BusinessCalendarEvent')
    Event.objects.filter(
        title__in=(
            'Fire sprinkler inspection (annual)',
            'Fire alarm system inspection (annual)',
        ),
        event_type='maintenance',
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('dream_blue', '0009_loan_payoff_refinance_fields'),
    ]

    operations = [
        migrations.RunPython(seed_inspections, unseed_inspections),
    ]
