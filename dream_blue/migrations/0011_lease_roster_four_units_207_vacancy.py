# Four-unit roster: 207 4th vacant from Apr 2026; refresh tenant notes + lease-income KPI.

from datetime import date
from decimal import Decimal

from django.db import migrations


LEASE = 'lease'


def apply(apps, schema_editor):
    Event = apps.get_model('dream_blue', 'BusinessCalendarEvent')
    KPI = apps.get_model('dream_blue', 'BusinessKPIEntry')

    Event.objects.filter(
        event_type=LEASE,
        property_label__in=('207 4th St. (unit)', '207 4th St.'),
        title__in=('Annual lease (1 year)', 'Vacant — available'),
    ).delete()

    Event.objects.create(
        event_type=LEASE,
        property_label='207 4th St.',
        title='Vacant — available',
        due_date=date(2026, 4, 1),
        end_date=None,
        amount=None,
        notes=(
            'Vacancy effective April 2026. ~2,200+ sq ft, above- and below-grade space. '
            'One of four commercial rental units in the portfolio (with 211 4th, '
            '401 A / Tara Thai, 401 B / Two Hearts).'
        ),
        is_active=True,
        sort_order=40,
    )

    Event.objects.filter(
        event_type=LEASE,
        property_label='211 4th St.',
        title='Tattoo Asylum / Cervidea',
    ).update(
        notes=(
            'Tattoo Asylum / Cervidea. One of four rental units. Monthly rent $1,193.'
        ),
    )
    Event.objects.filter(
        event_type=LEASE,
        property_label='401 A Beltrami Ave.',
        title='Tara Thai (Tara Bemidji LLC)',
    ).update(
        notes=(
            'Restaurant at 401 Beltrami (Tara Bemidji LLC). One of four rental units. '
            'Security deposit $3,300. Monthly rent $2,000.'
        ),
    )
    Event.objects.filter(
        event_type=LEASE,
        property_label='401 B Beltrami Ave.',
        title='Two Hearts',
    ).update(
        notes=(
            'Two Hearts at 401 B Beltrami. One of four rental units. '
            'Deposit $1,750. Monthly rent $1,850. Lease ends Dec 2026.'
        ),
    )

    KPI.objects.update_or_create(
        label='Total monthly lease income',
        defaults={
            'value_display': '$5,043',
            'detail': (
                'Occupied rents only (207 4th vacant from Apr 2026): '
                '211 4th — Tattoo Asylum / Cervidea — $1,193; '
                '401 A Beltrami — Tara Thai (Tara Bemidji LLC) — $2,000; '
                '401 B Beltrami — Two Hearts — $1,850. '
                '207 4th — ~2,200+ sf above/below grade — marketing / TBD. '
                'Recalculate when a new lease is signed.'
            ),
            'period_hint': 'Apr 2026 baseline (207 vacant)',
            'is_active': True,
            'sort_order': 5,
        },
    )


def revert(apps, schema_editor):
    Event = apps.get_model('dream_blue', 'BusinessCalendarEvent')
    KPI = apps.get_model('dream_blue', 'BusinessKPIEntry')

    Event.objects.filter(
        event_type=LEASE,
        property_label='207 4th St.',
        title='Vacant — available',
        due_date=date(2026, 4, 1),
    ).delete()
    Event.objects.create(
        event_type=LEASE,
        property_label='207 4th St. (unit)',
        title='Annual lease (1 year)',
        due_date=date(2025, 4, 1),
        end_date=date(2026, 4, 1),
        amount=Decimal('1600.00'),
        notes='Monthly rent $1,600. Term 4/1/25–4/1/26.',
        is_active=True,
        sort_order=40,
    )
    KPI.objects.filter(label='Total monthly lease income').update(
        value_display='$6,643',
        detail=(
            'Approximate sum of monthly rents for active roster: '
            '211 4th ($1,193) + 401 A ($2,000) + 401 B ($1,850) + 207 4th unit ($1,600). '
            'Adjust when rates or occupancy change.'
        ),
        period_hint='Jan baseline / current schedule',
    )


class Migration(migrations.Migration):
    dependencies = [
        ('dream_blue', '0010_annual_fire_sprinkler_alarm_inspections'),
    ]

    operations = [
        migrations.RunPython(apply, revert),
    ]
