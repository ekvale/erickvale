# Tara Thai and Two Hearts: 2,000 sf above grade each (per owner).

from django.db import migrations


def apply(apps, schema_editor):
    Event = apps.get_model('dream_blue', 'BusinessCalendarEvent')
    KPI = apps.get_model('dream_blue', 'BusinessKPIEntry')
    LEASE = 'lease'

    Event.objects.filter(
        event_type=LEASE, property_label='401 A Beltrami Ave.'
    ).update(
        square_footage=2000,
        notes=(
            'Tara Thai (Tara Bemidji LLC). Corner location; premium foot traffic; commercial '
            'kitchen. 2,000 sf above grade. One of four rental units. Security deposit '
            '$3,300. Monthly rent $2,000.'
        ),
    )
    Event.objects.filter(
        event_type=LEASE, property_label='401 B Beltrami Ave.'
    ).update(
        square_footage=2000,
        notes=(
            'Two Hearts. Street-facing retail (not on corner); downtown Bemidji near the lake. '
            '2,000 sf above grade. One of four rental units. Deposit $1,750. '
            'Monthly rent $1,850. Lease ends Dec 2026.'
        ),
    )

    KPI.objects.filter(label='Total monthly lease income').update(
        detail=(
            'Occupied rents only (207 4th vacant from Apr 2026): '
            '211 4th — Tattoo Asylum — $1,193 (1,850 sf + 1,000 sf storage); '
            '401 A Beltrami — Tara Thai — $2,000 (corner, kitchen, 2,000 sf); '
            '401 B Beltrami — Two Hearts — $1,850 (2,000 sf street retail). '
            '207 4th — vacant — 2,150 sf + 2,000 sf storage; see digest suggested ask. '
            'Recalculate when a new lease is signed.'
        ),
        period_hint='Apr 2026 baseline (207 vacant)',
    )


def revert(apps, schema_editor):
    Event = apps.get_model('dream_blue', 'BusinessCalendarEvent')
    KPI = apps.get_model('dream_blue', 'BusinessKPIEntry')
    LEASE = 'lease'

    Event.objects.filter(
        event_type=LEASE, property_label='401 A Beltrami Ave.'
    ).update(
        square_footage=2200,
        notes=(
            'Tara Thai (Tara Bemidji LLC). Corner location; premium foot traffic; commercial '
            'kitchen. ~2,200 sf above grade. One of four rental units. Security deposit '
            '$3,300. Monthly rent $2,000.'
        ),
    )
    Event.objects.filter(
        event_type=LEASE, property_label='401 B Beltrami Ave.'
    ).update(
        square_footage=1950,
        notes=(
            'Two Hearts. Street-facing retail (not on corner); downtown Bemidji near the lake. '
            '~1,950 sf above grade. One of four rental units. Deposit $1,750. '
            'Monthly rent $1,850. Lease ends Dec 2026.'
        ),
    )
    KPI.objects.filter(label='Total monthly lease income').update(
        detail=(
            'Occupied rents only (207 4th vacant from Apr 2026): '
            '211 4th — Tattoo Asylum — $1,193 (1,850 sf + 1,000 sf storage); '
            '401 A Beltrami — Tara Thai — $2,000 (corner, kitchen, ~2,200 sf); '
            '401 B Beltrami — Two Hearts — $1,850 (~1,950 sf street retail). '
            '207 4th — vacant — 2,150 sf + 2,000 sf storage; see digest suggested ask. '
            'Recalculate when a new lease is signed.'
        ),
        period_hint='Apr 2026 baseline (207 vacant)',
    )


class Migration(migrations.Migration):
    dependencies = [
        ('dream_blue', '0013_lease_storage_sf_and_marketing_notes'),
    ]

    operations = [
        migrations.RunPython(apply, revert),
    ]
