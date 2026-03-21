# Generated manually for EventPhoto gallery

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nomoar', '0011_discovery_start_filters'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventPhoto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'image',
                    models.ImageField(
                        help_text='JPEG, PNG, or WebP recommended',
                        upload_to='nomoar/event_photos/',
                    ),
                ),
                (
                    'caption',
                    models.CharField(
                        blank=True,
                        help_text='Optional caption shown under the image',
                        max_length=300,
                    ),
                ),
                (
                    'alt_text',
                    models.CharField(
                        blank=True,
                        help_text='Short description for screen readers (falls back to caption or title if empty)',
                        max_length=300,
                    ),
                ),
                ('order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                (
                    'event',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='photos',
                        to='nomoar.historicalevent',
                    ),
                ),
            ],
            options={
                'verbose_name': 'Event photo',
                'verbose_name_plural': 'Event photos',
                'ordering': ['order', 'pk'],
            },
        ),
    ]
