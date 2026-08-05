import random
from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from mdh_publications.models import DocumentType, Publication, Tag


SAMPLE_TITLES = [
    "Minnesota Cancer Screening Access Snapshot",
    "Rural Health Workforce Capacity Brief",
    "Tobacco Prevention Program Outcomes",
    "Insurance Enrollment and Affordability Report",
    "Maternal and Infant Health Equity Dashboard",
    "Behavioral Health Service Utilization Trends",
    "Emergency Department Visit Pattern Analysis",
    "Public Health System Partnership Overview",
    "Long-Term Care Access and Cost Study",
    "Community Health Center Performance Summary",
    "Injury and Violence Prevention Data Review",
    "Prescription Drug Spending Trend Report",
]


class Command(BaseCommand):
    help = "Creates sample publications with facet and tag assignments for development/testing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=12,
            help="Number of sample publications to create (default: 12).",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing publications before creating samples.",
        )

    def handle(self, *args, **options):
        count = max(1, options["count"])
        should_reset = options["reset"]

        tags = list(Tag.objects.select_related("facet").all())
        document_types = list(DocumentType.objects.filter(is_active=True))

        if not tags:
            raise CommandError("No tags found. Run seed_mdh_publications_taxonomy first.")
        if not document_types:
            raise CommandError("No document types found. Run seed_mdh_publications_taxonomy first.")

        if should_reset:
            deleted_count, _ = Publication.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted_count} existing publication rows."))

        user_model = get_user_model()
        default_user = user_model.objects.filter(is_active=True).order_by("id").first()

        created = 0
        updated = 0
        today = date.today()

        for index in range(count):
            title = SAMPLE_TITLES[index % len(SAMPLE_TITLES)]
            if index >= len(SAMPLE_TITLES):
                title = f"{title} {index + 1}"

            status = random.choice([Publication.Status.DRAFT, Publication.Status.IN_REVIEW, Publication.Status.PUBLISHED])
            publication_date = today.replace(year=max(today.year - random.randint(0, 4), 2000))

            publication, was_created = Publication.objects.update_or_create(
                title=title,
                defaults={
                    "summary": f"Sample summary for {title}.",
                    "abstract": (
                        f"This is sample content for {title}. "
                        "It is generated to populate development data for filtering and search."
                    ),
                    "document_type": random.choice(document_types),
                    "publication_date": publication_date,
                    "status": status,
                    "is_featured": random.choice([True, False]),
                    "source_url": "",
                    "created_by": default_user,
                    "updated_by": default_user,
                },
            )

            chosen_tags = random.sample(tags, k=min(random.randint(3, 7), len(tags)))
            publication.tags.set(chosen_tags)
            publication.facets.set({tag.facet for tag in chosen_tags})

            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Sample publications ready. Created: {created}, Updated: {updated}, Total now: {Publication.objects.count()}."
            )
        )