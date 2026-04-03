# Leases: addresses, tenants, deposits, monthly rent, term → calendar + KPI.

from datetime import date
from decimal import Decimal

from django.db import migrations


LEASE_EVENT_TYPE = 'lease'


def seed_leases_and_kpi(apps, schema_editor):
    BusinessCalendarEvent = apps.get_model('dream_blue', 'BusinessCalendarEvent')
    BusinessKPIEntry = apps.get_model('dream_blue', 'BusinessKPIEntry')

    specs = [
        {
            'property_label': '211 4th St.',
            'title': 'Tattoo Asylum / Cervidea',
            'due_date': date(2024, 3, 1),
            'end_date': date(2027, 3, 1),
            'amount': Decimal('1193.00'),
            'notes': 'Monthly rent $1,193.',
            'sort_order': 10,
        },
        {
            'property_label': '401 A Beltrami Ave.',
            'title': 'Tara Thai (Tara Bemidji LLC)',
            'due_date': date(2021, 6, 30),
            'end_date': date(2026, 6, 30),
            'amount': Decimal('2000.00'),
            'notes': 'Security deposit $3,300. Monthly rent $2,000.',
            'sort_order': 20,
        },
        {
            'property_label': '401 B Beltrami Ave.',
            'title': 'Two Hearts',
            'due_date': date(2024, 12, 10),
            'end_date': date(2026, 12, 31),
            'amount': Decimal('1850.00'),
            'notes': 'Deposit $1,750. Monthly rent $1,850. Lease ends Dec 2026.',
            'sort_order': 30,
        },
        {
            'property_label': '207 4th St. (unit)',
            'title': 'Annual lease (1 year)',
            'due_date': date(2025, 4, 1),
            'end_date': date(2026, 4, 1),
            'amount': Decimal('1600.00'),
            'notes': 'Monthly rent $1,600. Term 4/1/25–4/1/26.',
            'sort_order': 40,
        },
    ]

    for spec in specs:
        BusinessCalendarEvent.objects.update_or_create(
            property_label=spec['property_label'],
            event_type=LEASE_EVENT_TYPE,
            due_date=spec['due_date'],
            defaults={
                'title': spec['title'],
                'end_date': spec['end_date'],
                'amount': spec['amount'],
                'notes': spec['notes'],
                'is_active': True,
                'sort_order': spec['sort_order'],
            },
        )

    BusinessKPIEntry.objects.update_or_create(
        label='Total monthly lease income',
        defaults={
            'value_display': '$6,643',
            'detail': (
                'Approximate sum of monthly rents for active roster: '
                '211 4th ($1,193) + 401 A ($2,000) + 401 B ($1,850) + 207 4th unit ($1,600). '
                'Adjust when rates or occupancy change.'
            ),
            'period_hint': 'Jan baseline / current schedule',
            'is_active': True,
            'sort_order': 5,
        },
    )


def unseed_leases_and_kpi(apps, schema_editor):
    BusinessCalendarEvent = apps.get_model('dream_blue', 'BusinessCalendarEvent')
    BusinessKPIEntry = apps.get_model('dream_blue', 'BusinessKPIEntry')

    props = [
        '211 4th St.',
        '401 A Beltrami Ave.',
        '401 B Beltrami Ave.',
        '207 4th St. (unit)',
    ]
    BusinessCalendarEvent.objects.filter(
        event_type=LEASE_EVENT_TYPE,
        property_label__in=props,
    ).delete()
    BusinessKPIEntry.objects.filter(label='Total monthly lease income').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('dream_blue', '0004_business_calendar_kpi_report_sections'),
    ]

    operations = [
        migrations.RunPython(seed_leases_and_kpi, unseed_leases_and_kpi),
    ]
