# Below-grade storage sf + above-grade refresh; marketing notes for each unit.

from django.db import migrations, models


def apply(apps, schema_editor):
    Event = apps.get_model('dream_blue', 'BusinessCalendarEvent')
    KPI = apps.get_model('dream_blue', 'BusinessKPIEntry')
    LEASE = 'lease'

    specs = (
        (
            '211 4th St.',
            1850,
            1000,
            (
                'Tattoo Asylum / Cervidea. 1,850 sf above grade + 1,000 sf below-grade storage '
                '(storage at modest rates in rent model). One of four rental units. '
                'Monthly rent $1,193.'
            ),
        ),
        (
            '207 4th St.',
            2150,
            2000,
            (
                'Vacant — available April 2026. 2,150 sf above grade + 2,000 sf below-grade '
                'storage (below grade fire-zoned for storage only). Downtown Bemidji near the '
                'lake. One of four commercial units (with 211 4th, 401 A Tara Thai, 401 B Two Hearts).'
            ),
        ),
        (
            '401 A Beltrami Ave.',
            2200,
            None,
            (
                'Tara Thai (Tara Bemidji LLC). Corner location; premium foot traffic; commercial '
                'kitchen. ~2,200 sf above grade. One of four rental units. Security deposit '
                '$3,300. Monthly rent $2,000.'
            ),
        ),
        (
            '401 B Beltrami Ave.',
            1950,
            None,
            (
                'Two Hearts. Street-facing retail (not on corner); downtown Bemidji near the lake. '
                '~1,950 sf above grade. One of four rental units. Deposit $1,750. '
                'Monthly rent $1,850. Lease ends Dec 2026.'
            ),
        ),
    )

    for prop, above, below, notes in specs:
        qs = Event.objects.filter(event_type=LEASE, property_label=prop)
        upd = {'square_footage': above, 'notes': notes}
        if below is not None:
            upd['square_footage_storage'] = below
        else:
            upd['square_footage_storage'] = None
        qs.update(**upd)

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


def revert(apps, schema_editor):
    Event = apps.get_model('dream_blue', 'BusinessCalendarEvent')
    KPI = apps.get_model('dream_blue', 'BusinessKPIEntry')
    LEASE = 'lease'

    Event.objects.filter(event_type=LEASE, property_label='211 4th St.').update(
        square_footage=2000,
        square_footage_storage=None,
        notes=(
            'Tattoo Asylum / Cervidea. One of four rental units. Monthly rent $1,193.'
        ),
    )
    Event.objects.filter(event_type=LEASE, property_label='207 4th St.').update(
        square_footage=2200,
        square_footage_storage=None,
        notes=(
            'Vacancy effective April 2026. ~2,200+ sq ft, above- and below-grade space. '
            'One of four commercial rental units in the portfolio (with 211 4th, '
            '401 A / Tara Thai, 401 B / Two Hearts).'
        ),
    )
    Event.objects.filter(event_type=LEASE, property_label='401 A Beltrami Ave.').update(
        square_footage=2000,
        square_footage_storage=None,
        notes=(
            'Restaurant at 401 Beltrami (Tara Bemidji LLC). One of four rental units. '
            'Security deposit $3,300. Monthly rent $2,000.'
        ),
    )
    Event.objects.filter(event_type=LEASE, property_label='401 B Beltrami Ave.').update(
        square_footage=2000,
        square_footage_storage=None,
        notes=(
            'Two Hearts at 401 B Beltrami. One of four rental units. '
            'Deposit $1,750. Monthly rent $1,850. Lease ends Dec 2026.'
        ),
    )
    KPI.objects.filter(label='Total monthly lease income').update(
        detail=(
            'Occupied rents only (207 4th vacant from Apr 2026): '
            '211 4th — Tattoo Asylum / Cervidea — $1,193; '
            '401 A Beltrami — Tara Thai (Tara Bemidji LLC) — $2,000; '
            '401 B Beltrami — Two Hearts — $1,850. '
            '207 4th — ~2,200+ sf above/below grade — marketing / TBD. '
            'Recalculate when a new lease is signed.'
        ),
        period_hint='Apr 2026 baseline (207 vacant)',
    )


class Migration(migrations.Migration):
    dependencies = [
        ('dream_blue', '0012_lease_square_footage'),
    ]

    operations = [
        migrations.AddField(
            model_name='businesscalendarevent',
            name='square_footage_storage',
            field=models.PositiveIntegerField(
                blank=True,
                help_text='Below-grade / storage sq ft (leases); priced at storage $/sf in suggestions',
                null=True,
            ),
        ),
        migrations.RunPython(apply, revert),
    ]
