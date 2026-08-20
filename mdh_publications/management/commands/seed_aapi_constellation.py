"""Seed the AAPI metadata constellation onto Asian / NHPI tags.

    python manage.py seed_aapi_constellation
    python manage.py seed_aapi_constellation --reset

Requires seed_mdh_publications_taxonomy first (asian-populations and
pacific-islander tags must exist).
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.template.defaultfilters import slugify

from mdh_publications.data.aapi_constellation import (
    LANGUAGE_LANDING_PAGES,
    MDH_SPACES,
    PUBLICATIONS,
    RESOURCE_GROUPS,
    STATUTES_POLICY,
    describe,
    publication_date,
)
from mdh_publications.models import (
    DocumentType,
    Publication,
    Tag,
    TagConstellationItem,
)


ASIAN_SLUG = "asian-populations"
NHPI_SLUG = "pacific-islander"


class Command(BaseCommand):
    help = "Seed AAPI constellation items and related publications for Asian and NHPI tags."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Clear constellation items on Asian/NHPI tags before reseeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        try:
            asian = Tag.objects.get(slug=ASIAN_SLUG)
            nhpi = Tag.objects.get(slug=NHPI_SLUG)
        except Tag.DoesNotExist as exc:
            raise CommandError(
                "Asian / NHPI tags missing. Run seed_mdh_publications_taxonomy first."
            ) from exc

        language_access = Tag.objects.filter(slug="language-access").first()

        if options["reset"]:
            deleted, _ = TagConstellationItem.objects.filter(
                tag__in=[asian, nhpi]
            ).delete()
            self.stdout.write(self.style.WARNING(f"Cleared {deleted} constellation items."))

        tags_by_scope = {
            "asian": [asian],
            "nhpi": [nhpi],
            "both": [asian, nhpi],
        }

        item_count = 0
        for order, (title, url) in enumerate(MDH_SPACES):
            for tag in (asian, nhpi):
                item_count += self._upsert_item(
                    tag,
                    TagConstellationItem.Kind.MDH_SPACE,
                    title,
                    url=url,
                    sort_order=order,
                )

        for order, (title, note, url) in enumerate(STATUTES_POLICY):
            for tag in (asian, nhpi):
                item_count += self._upsert_item(
                    tag,
                    TagConstellationItem.Kind.STATUTE_POLICY,
                    title,
                    note=note,
                    url=url,
                    sort_order=order,
                )

        for order, (title, url, scope) in enumerate(RESOURCE_GROUPS):
            for tag in tags_by_scope[scope]:
                item_count += self._upsert_item(
                    tag,
                    TagConstellationItem.Kind.RESOURCE_GROUP,
                    title,
                    url=url,
                    sort_order=order,
                )

        pub_created = pub_updated = 0
        for order, (title, year, url, scope, type_name, extra_slugs) in enumerate(PUBLICATIONS):
            document_type, _ = DocumentType.objects.get_or_create(
                slug=slugify(type_name),
                defaults={"name": type_name, "is_active": True},
            )
            if document_type.name != type_name:
                document_type.name = type_name
                document_type.is_active = True
                document_type.save(update_fields=["name", "is_active"])

            publication, created = Publication.objects.update_or_create(
                title=title,
                defaults={
                    "description": describe(title, year),
                    "document_type": document_type,
                    "publication_date": publication_date(year),
                    "source_url": url,
                    "status": Publication.Status.PUBLISHED,
                    "language": "hmn" if "Hmong)" in title else "en",
                    "is_translated": "Hmong)" in title,
                },
            )
            race_tags = tags_by_scope[scope]
            extra = list(Tag.objects.filter(slug__in=extra_slugs))
            if "Hmong)" in title and language_access:
                extra.append(language_access)
            all_tags = list({*race_tags, *extra})
            publication.tags.set(all_tags)
            publication.facets.set({t.facet for t in all_tags})

            for tag in race_tags:
                item_count += self._upsert_item(
                    tag,
                    TagConstellationItem.Kind.PUBLICATION_REF,
                    title,
                    url=url,
                    publication=publication,
                    sort_order=1000 + order,
                )

            pub_created += created
            pub_updated += not created

        for order, (lang_code, title, url) in enumerate(LANGUAGE_LANDING_PAGES):
            document_type, _ = DocumentType.objects.get_or_create(
                slug="guidance-document",
                defaults={"name": "Guidance Document", "is_active": True},
            )
            publication, created = Publication.objects.update_or_create(
                title=title,
                defaults={
                    "description": describe(title, None),
                    "document_type": document_type,
                    "source_url": url,
                    "status": Publication.Status.PUBLISHED,
                    "language": lang_code,
                    "is_translated": True,
                },
            )
            landing_tags = [t for t in (language_access,) if t]
            publication.tags.set(landing_tags)
            publication.facets.set({t.facet for t in landing_tags})

            for tag in (asian, nhpi):
                item_count += self._upsert_item(
                    tag,
                    TagConstellationItem.Kind.MDH_SPACE,
                    title,
                    note="MDH translated-materials landing page for this language. "
                    "Not a race/ethnicity tag by itself — set Publication Language on "
                    "individual translated files.",
                    url=url,
                    publication=publication,
                    sort_order=500 + order,
                )
            pub_created += created
            pub_updated += not created

        self.stdout.write(
            self.style.SUCCESS(
                f"AAPI constellation ready. Upserted {item_count} constellation rows; "
                f"publications created {pub_created}, updated {pub_updated}."
            )
        )

    def _upsert_item(self, tag, kind, title, note="", url="", publication=None, sort_order=0):
        _, created = TagConstellationItem.objects.update_or_create(
            tag=tag,
            kind=kind,
            title=title,
            defaults={
                "note": note,
                "url": url,
                "publication": publication,
                "sort_order": sort_order,
            },
        )
        return 1 if created else 0
