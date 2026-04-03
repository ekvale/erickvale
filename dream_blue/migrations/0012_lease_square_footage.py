from django.db import migrations, models


def set_lease_sqft(apps, schema_editor):
    Event = apps.get_model('dream_blue', 'BusinessCalendarEvent')
    pairs = (
        ('211 4th St.', 2000),
        ('401 A Beltrami Ave.', 2000),
        ('401 B Beltrami Ave.', 2000),
        ('207 4th St.', 2200),
    )
    for prop, sf in pairs:
        Event.objects.filter(event_type='lease', property_label=prop).update(
            square_footage=sf,
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('dream_blue', '0011_lease_roster_four_units_207_vacancy'),
    ]

    operations = [
        migrations.AddField(
            model_name='businesscalendarevent',
            name='square_footage',
            field=models.PositiveIntegerField(
                blank=True,
                help_text='Leasable sq ft (leases) — used for $/sf economics in digest',
                null=True,
            ),
        ),
        migrations.RunPython(set_lease_sqft, noop),
    ]
