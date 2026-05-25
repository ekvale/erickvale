"""Gmail contact extraction (shared by view and management command)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from django.conf import settings

from .import_parsers import ParsedContactRow
from .models import Contact, ContactSource


EMAIL_RE = re.compile(r'[\w.+-]+@[\w.-]+\.\w+', re.IGNORECASE)


@dataclass
class GmailImportResult:
    added: int = 0
    skipped_existing: int = 0
    error: str | None = None


def gmail_oauth_configured() -> bool:
    token_path = (getattr(settings, 'GMAIL_TOKEN_PATH', '') or '').strip()
    creds_path = (getattr(settings, 'GMAIL_CREDENTIALS_PATH', '') or '').strip()
    return bool(token_path and creds_path)


def _load_gmail_service():
    # TODO: configure Gmail OAuth — set GMAIL_CREDENTIALS_PATH and GMAIL_TOKEN_PATH in .env
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request
    import os

    creds_path = settings.GMAIL_CREDENTIALS_PATH
    token_path = settings.GMAIL_TOKEN_PATH
    scopes = getattr(
        settings,
        'GMAIL_SCOPES',
        ['https://www.googleapis.com/auth/gmail.readonly'],
    )
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, scopes)
            creds = flow.run_local_server(port=0)
        with open(token_path, 'w', encoding='utf-8') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds, cache_discovery=False)


def _addresses_from_headers(headers: list[dict]) -> set[str]:
    emails: set[str] = set()
    for header in headers:
        name = (header.get('name') or '').lower()
        if name not in ('from', 'to', 'cc', 'bcc'):
            continue
        value = header.get('value') or ''
        for match in EMAIL_RE.findall(value):
            emails.add(match.lower())
    return emails


def _display_name_for_email(email: str, headers: list[dict]) -> str:
    for header in headers:
        value = header.get('value') or ''
        if email.lower() in value.lower():
            if '<' in value:
                return value.split('<')[0].strip().strip('"')
            return ''
    local = email.split('@')[0]
    return local.replace('.', ' ').replace('_', ' ').title()


def fetch_gmail_contact_rows(max_messages: int = 500) -> list[ParsedContactRow]:
    service = _load_gmail_service()
    rows_by_email: dict[str, ParsedContactRow] = {}
    page_token = None
    fetched = 0
    while fetched < max_messages:
        batch_size = min(100, max_messages - fetched)
        resp = (
            service.users()
            .messages()
            .list(userId='me', labelIds=['SENT'], maxResults=batch_size, pageToken=page_token)
            .execute()
        )
        for ref in resp.get('messages', []):
            if fetched >= max_messages:
                break
            msg = (
                service.users()
                .messages()
                .get(userId='me', id=ref['id'], format='metadata')
                .execute()
            )
            headers = msg.get('payload', {}).get('headers', [])
            for email in _addresses_from_headers(headers):
                if email in rows_by_email:
                    continue
                display = _display_name_for_email(email, headers)
                first, last = '', ''
                if display:
                    parts = display.split(None, 1)
                    first = parts[0]
                    last = parts[1] if len(parts) > 1 else ''
                rows_by_email[email] = ParsedContactRow(
                    first_name=first,
                    last_name=last,
                    display_name=display or email,
                    email=email,
                    source=ContactSource.GMAIL,
                    source_id=email,
                )
            fetched += 1
        page_token = resp.get('nextPageToken')
        if not page_token:
            break
    return list(rows_by_email.values())


def import_gmail_contacts(max_messages: int = 500) -> GmailImportResult:
    if not gmail_oauth_configured():
        return GmailImportResult(
            error=(
                'Gmail OAuth is not configured. Set GMAIL_CREDENTIALS_PATH and '
                'GMAIL_TOKEN_PATH in your environment.'
            )
        )
    try:
        parsed_rows = fetch_gmail_contact_rows(max_messages=max_messages)
    except Exception as exc:
        return GmailImportResult(error=str(exc))

    added = 0
    skipped = 0
    for row in parsed_rows:
        email = (row.email or '').strip().lower()
        if not email:
            continue
        if Contact.objects.filter(email__iexact=email).exists():
            skipped += 1
            continue
        if row.source_id and Contact.objects.filter(
            source=ContactSource.GMAIL, source_id=row.source_id
        ).exists():
            skipped += 1
            continue
        Contact.objects.create(
            first_name=row.first_name,
            last_name=row.last_name,
            display_name=row.display_name,
            email=email,
            source=ContactSource.GMAIL,
            source_id=row.source_id or email,
        )
        added += 1
    return GmailImportResult(added=added, skipped_existing=skipped)
