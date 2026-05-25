"""Parse uploaded contact files (vCard, LinkedIn CSV, Facebook JSON)."""

from __future__ import annotations

import csv
import io
import json
import re
from dataclasses import dataclass
from datetime import date, datetime

from .models import ContactSource


@dataclass
class ParsedContactRow:
    first_name: str = ''
    last_name: str = ''
    display_name: str = ''
    email: str = ''
    phone: str = ''
    company: str = ''
    title: str = ''
    birthday: date | None = None
    notes: str = ''
    source: str = ContactSource.MANUAL
    source_id: str = ''


def _split_name(full: str) -> tuple[str, str]:
    full = (full or '').strip()
    if not full:
        return '', ''
    parts = full.split(None, 1)
    return parts[0], parts[1] if len(parts) > 1 else ''


def _parse_date(raw: str) -> date | None:
    raw = (raw or '').strip()
    if not raw:
        return None
    for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y'):
        try:
            return datetime.strptime(raw[:10], fmt).date()
        except ValueError:
            continue
    return None


def parse_vcf(content: str | bytes) -> list[ParsedContactRow]:
    import vobject

    if isinstance(content, bytes):
        content = content.decode('utf-8', errors='replace')
    rows: list[ParsedContactRow] = []
    for card in vobject.readComponents(content):
        if card.name.lower() != 'vcard':
            continue
        fn = ''
        if hasattr(card, 'fn'):
            fn = str(card.fn.value).strip()
        first, last = _split_name(fn)
        email = ''
        for em in card.contents.get('email', []):
            email = str(em.value).strip()
            break
        phone = ''
        for tel in card.contents.get('tel', []):
            phone = str(tel.value).strip()
            break
        org = ''
        if hasattr(card, 'org'):
            org = str(card.org.value).strip()
        uid = ''
        if hasattr(card, 'uid'):
            uid = str(card.uid.value).strip()
        rows.append(
            ParsedContactRow(
                first_name=first,
                last_name=last,
                display_name=fn,
                email=email,
                phone=phone,
                company=org,
                source=ContactSource.PHONE,
                source_id=uid,
            )
        )
    return rows


def parse_linkedin_csv(content: str | bytes) -> list[ParsedContactRow]:
    if isinstance(content, bytes):
        content = content.decode('utf-8-sig', errors='replace')
    reader = csv.DictReader(io.StringIO(content))
    rows: list[ParsedContactRow] = []
    for i, row in enumerate(reader):
        first = (row.get('First Name') or row.get('First name') or '').strip()
        last = (row.get('Last Name') or row.get('Last name') or '').strip()
        email = (row.get('Email Address') or row.get('Email') or '').strip()
        company = (row.get('Company') or '').strip()
        title = (row.get('Position') or row.get('Title') or '').strip()
        connected = (row.get('Connected On') or '').strip()
        notes = f'LinkedIn connected: {connected}' if connected else ''
        rows.append(
            ParsedContactRow(
                first_name=first,
                last_name=last,
                display_name=f'{first} {last}'.strip(),
                email=email,
                company=company,
                title=title,
                notes=notes,
                source=ContactSource.LINKEDIN,
                source_id=email or f'linkedin-row-{i}',
            )
        )
    return rows


def _facebook_friend_row(obj: dict, index: int) -> ParsedContactRow | None:
    name = (obj.get('name') or obj.get('title') or '').strip()
    if not name:
        return None
    first, last = _split_name(name)
    email = (obj.get('email') or obj.get('contact_email') or '').strip()
    phone = (obj.get('phone') or obj.get('contact_phone_number') or '').strip()
    slug = re.sub(r'\W+', '-', name.lower())[:80]
    return ParsedContactRow(
        first_name=first,
        last_name=last,
        display_name=name,
        email=email,
        phone=phone,
        source=ContactSource.FACEBOOK,
        source_id=email or f'facebook-{index}-{slug}',
    )


def parse_facebook_json(content: str | bytes) -> list[ParsedContactRow]:
    if isinstance(content, bytes):
        content = content.decode('utf-8', errors='replace')
    data = json.loads(content)
    friends = None
    if isinstance(data, list):
        friends = data
    elif isinstance(data, dict):
        friends = data.get('friends') or data.get('friend_requests')
        if friends is None and 'label_values' in data:
            friends = [data]
    if not friends:
        return []
    rows: list[ParsedContactRow] = []
    for i, item in enumerate(friends):
        if not isinstance(item, dict):
            continue
        parsed = _facebook_friend_row(item, i)
        if parsed:
            rows.append(parsed)
    return rows


def parse_uploaded_file(filename: str, raw: bytes) -> list[ParsedContactRow]:
    lower = (filename or '').lower()
    if lower.endswith('.vcf') or lower.endswith('.vcard'):
        return parse_vcf(raw)
    if lower.endswith('.csv'):
        return parse_linkedin_csv(raw)
    if lower.endswith('.json'):
        return parse_facebook_json(raw)
    raise ValueError('Unsupported file type. Use .vcf, .csv, or .json.')
