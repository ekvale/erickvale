from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('dream_blue', '0007_seed_loans_utilities_expenses'),
    ]

    operations = [
        migrations.CreateModel(
            name='LeaseCompResearchRun',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('draft', 'Draft'),
                            ('completed', 'Completed'),
                            ('failed', 'Failed'),
                        ],
                        default='draft',
                        max_length=20,
                    ),
                ),
                ('coverage_summary', models.TextField(blank=True)),
                (
                    'search_query_log',
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text='Queries or topics the agent used',
                    ),
                ),
                (
                    'compiled_report',
                    models.TextField(
                        blank=True,
                        help_text='Plain-text memo for email and review',
                    ),
                ),
                (
                    'agent_snapshot',
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text='Normalized agent payload',
                    ),
                ),
                ('error_message', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Lease comp research run',
                'verbose_name_plural': 'Lease comp research runs',
                'ordering': ['-created_at'],
            },
        ),
    ]
