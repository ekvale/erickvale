from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('braindump', '0007_contact_scheduled_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='captureitem',
            name='calendar_time',
            field=models.TimeField(
                blank=True,
                help_text='Optional start time on calendar_date (timed event in ICS/Google).',
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='captureitem',
            name='calendar_end_time',
            field=models.TimeField(
                blank=True,
                help_text='Optional end time; ICS defaults to one hour after start if unset.',
                null=True,
            ),
        ),
    ]
