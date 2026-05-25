"""Bulk create contacts from parsed rows with deduplication."""

from __future__ import annotations

from dataclasses import dataclass

from django.db.models import Q

from .import_parsers import ParsedContactRow
from .models import Contact


@dataclass
class FileImportResult:
    added: int = 0
    skipped_existing: int = 0


def _normalize_email(email: str) -> str:
    return (email or '').strip().lower()


def _name_key(row: ParsedContactRow) -> str:
    name = (
        row.display_name
        or f'{row.first_name} {row.last_name}'.strip()
    ).strip().lower()
    return name


def import_parsed_rows(rows: list[ParsedContactRow]) -> FileImportResult:
    added = 0
    skipped = 0
    for row in rows:
        email = _normalize_email(row.email)
        if email and Contact.objects.filter(email__iexact=email).exists():
            skipped += 1
            continue
        if row.source_id:
            exists = Contact.objects.filter(
                source=row.source,
                source_id=row.source_id,
            ).exists()
            if exists:
                skipped += 1
                continue
        name_key = _name_key(row)
        if not email and name_key:
            exists = Contact.objects.filter(
                Q(display_name__iexact=name_key)
                | (
                    Q(first_name__iexact=row.first_name)
                    & Q(last_name__iexact=row.last_name)
                )
            ).exists()
            if exists:
                skipped += 1
                continue
        if not email and not name_key:
            skipped += 1
            continue
        Contact.objects.create(
            first_name=row.first_name,
            last_name=row.last_name,
            display_name=row.display_name,
            email=email,
            phone=row.phone,
            birthday=row.birthday,
            company=row.company,
            title=row.title,
            notes=row.notes,
            source=row.source,
            source_id=row.source_id,
        )
        added += 1
    return FileImportResult(added=added, skipped_existing=skipped)
