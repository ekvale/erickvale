import ast
import csv
import json
import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import slugify

from mdh_publications.models import DocumentType, Facet, Tag, TopicGroup


def humanize_slug(value):
    return value.replace("-", " ").replace("_", " ").title()


class Command(BaseCommand):
    help = "Imports MDH Publications taxonomy facets, topic groups, tags, and document types from CSV files."

    def add_arguments(self, parser):
        parser.add_argument(
            "--base-dir",
            dest="base_dir",
            default=None,
            help="Directory containing the taxonomy CSV files. Defaults to the Django project base directory.",
        )

    def handle(self, *args, **options):
        from django.conf import settings

        base_dir = Path(options["base_dir"] or settings.BASE_DIR)
        facets_path = base_dir / "facets.csv"
        tags_by_facet_path = base_dir / "tags_by_facet.csv"
        tags_path = base_dir / "tags.csv"
        document_types_path = base_dir / "document_types.csv"
        markdown_path = base_dir / "mdh_taxonomy_hierarchical.md"

        required_files = [facets_path, tags_by_facet_path, tags_path, document_types_path]
        if all(path.exists() for path in required_files):
            facets = self._import_facets(facets_path)
            topic_groups = self._import_topic_groups(tags_by_facet_path)
            tags = self._import_tags(tags_path)
            document_types = self._import_document_types(document_types_path)
        elif markdown_path.exists():
            facets, topic_groups, tags, document_types = self._import_from_markdown(markdown_path)
        else:
            missing_files = [str(path) for path in required_files]
            raise CommandError(
                f"Missing required CSV files: {', '.join(missing_files)}. "
                f"No markdown fallback found at {markdown_path}."
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {facets} facets, {topic_groups} topic groups, {tags} tags, and {document_types} document types."
            )
        )

    def _import_facets(self, path):
        count = 0
        with path.open(newline="", encoding="utf-8-sig") as csv_file:
            reader = csv.DictReader(csv_file)
            for index, row in enumerate(reader, start=1):
                Facet.objects.update_or_create(
                    code=row["facet_code"].strip(),
                    defaults={
                        "name": row["facet_name"].strip(),
                        "description": row.get("description", "").strip(),
                        "sort_order": index,
                    },
                )
                count += 1

        return count

    def _import_topic_groups(self, path):
        count = 0
        seen_groups = set()
        with path.open(newline="", encoding="utf-8-sig") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                facet_code = row["facet_code"].strip()
                parent_category = row["parent_category"].strip()
                key = (facet_code, parent_category)
                if key in seen_groups:
                    continue

                facet = Facet.objects.get(code=facet_code)
                TopicGroup.objects.update_or_create(
                    facet=facet,
                    slug=slugify(parent_category),
                    defaults={
                        "name": humanize_slug(parent_category),
                        "description": "",
                    },
                )
                seen_groups.add(key)
                count += 1

        return count

    def _import_tags(self, path):
        count = 0
        with path.open(newline="", encoding="utf-8-sig") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                facet = Facet.objects.get(code=row["facet_code"].strip())
                topic_group, _ = TopicGroup.objects.get_or_create(
                    facet=facet,
                    slug=slugify(row["parent"].strip()),
                    defaults={
                        "name": humanize_slug(row["parent"].strip()),
                        "description": "",
                    },
                )

                Tag.objects.update_or_create(
                    slug=slugify(row["tag"].strip()),
                    defaults={
                        "facet": facet,
                        "topic_group": topic_group,
                        "name": humanize_slug(row["tag"].strip()),
                        "description": row.get("description", "").strip(),
                        "examples": self._parse_examples(row.get("examples", "[]")),
                    },
                )
                count += 1

        return count

    def _import_document_types(self, path):
        count = 0
        with path.open(newline="", encoding="utf-8-sig") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                name = row["document_type"].strip()
                DocumentType.objects.update_or_create(
                    slug=slugify(name),
                    defaults={"name": name, "is_active": True},
                )
                count += 1

        return count

    def _parse_examples(self, raw_examples):
        raw_examples = (raw_examples or "[]").strip()
        if not raw_examples:
            return []

        try:
            parsed = json.loads(raw_examples)
        except json.JSONDecodeError:
            try:
                parsed = ast.literal_eval(raw_examples)
            except (ValueError, SyntaxError):
                return [raw_examples]

        return parsed if isinstance(parsed, list) else [str(parsed)]

    def _import_from_markdown(self, markdown_path):
        facet_count = 0
        topic_group_count = 0
        tag_count = 0
        document_type_count = 0

        facet_pattern = re.compile(r"^###\s+FACET\s+([A-Z]):\s+(.+)$")
        topic_group_pattern = re.compile(r"^####\s+(.+)$")
        tag_pattern = re.compile(r"^\s*-\s+\*\*([a-z0-9\-]+)\*\*:\s+(.+)$")

        current_facet = None
        current_topic_group = None
        in_types_section = False

        with markdown_path.open(encoding="utf-8") as markdown_file:
            for raw_line in markdown_file:
                line = raw_line.strip()

                if line.startswith("## LEVEL 2: TYPES"):
                    in_types_section = True
                    continue

                if line.startswith("## LEVEL 3: TAGS"):
                    in_types_section = False
                    continue

                if in_types_section and line.startswith("- "):
                    type_name = line[2:].strip()
                    if type_name:
                        DocumentType.objects.update_or_create(
                            slug=slugify(type_name),
                            defaults={"name": type_name, "is_active": True},
                        )
                        document_type_count += 1
                    continue

                facet_match = facet_pattern.match(line)
                if facet_match:
                    code, name = facet_match.groups()
                    current_facet, _ = Facet.objects.update_or_create(
                        code=code,
                        defaults={
                            "name": name.strip().title(),
                            "description": "",
                            "sort_order": ord(code) - ord("A") + 1,
                        },
                    )
                    facet_count += 1
                    current_topic_group = None
                    continue

                topic_group_match = topic_group_pattern.match(line)
                if topic_group_match and current_facet is not None:
                    group_name = topic_group_match.group(1).strip()
                    current_topic_group, _ = TopicGroup.objects.update_or_create(
                        facet=current_facet,
                        slug=slugify(group_name),
                        defaults={"name": group_name, "description": ""},
                    )
                    topic_group_count += 1
                    continue

                tag_match = tag_pattern.match(raw_line)
                if tag_match and current_facet is not None and current_topic_group is not None:
                    tag_slug, description = tag_match.groups()
                    Tag.objects.update_or_create(
                        slug=tag_slug,
                        defaults={
                            "facet": current_facet,
                            "topic_group": current_topic_group,
                            "name": humanize_slug(tag_slug),
                            "description": description.strip(),
                            "examples": [],
                        },
                    )
                    tag_count += 1

        return facet_count, topic_group_count, tag_count, document_type_count