from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("mdh_publications", "0005_add_pdf_text"),
    ]

    operations = [
        migrations.CreateModel(
            name="AccessRequest",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("email", models.EmailField(blank=True, max_length=254)),
                (
                    "request_type",
                    models.CharField(
                        choices=[("access", "Request Access"), ("suggestion", "Suggest a Change")],
                        default="access",
                        max_length=20,
                    ),
                ),
                ("reason", models.TextField()),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
                ("is_resolved", models.BooleanField(default=False)),
            ],
            options={
                "ordering": ["-submitted_at"],
            },
        ),
    ]
