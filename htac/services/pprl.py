"""
htac/services/pprl.py

Privacy-Preserving Record Linkage (PPRL) services.

Public API
----------
compute_token(first_name, last_name, dob, sex, phone, zip_code) -> str
    Pure function. Derives a SHA-256 token from six PII fields.
    No I/O. No database access. PII never leaves the caller's scope.

deduplicate_tokens(queryset) -> int
    ORM-based cross-site matching. Accepts a HashToken queryset,
    produces / updates DeduplicatedRoster rows, and returns the
    total number of rows upserted.
"""

import datetime
import hashlib
import hmac
import re

from django.conf import settings


# ─── Internal normalisation helpers ──────────────────────────────────────────

def _digits_only(value: str) -> str:
    """Strip every non-digit character from *value*."""
    return re.sub(r"\D", "", value)


def _format_dob(dob) -> str:
    """
    Normalise a date-of-birth value to the 8-char string 'YYYYMMDD'.

    Accepts:
      - a ``datetime.date`` / ``datetime.datetime`` object
      - a string in 'YYYY-MM-DD', 'MM/DD/YYYY', or already 'YYYYMMDD' form
        (any non-digit separators are stripped after the string is cast)
    """
    if hasattr(dob, "strftime"):
        return dob.strftime("%Y%m%d")
    return re.sub(r"\D", "", str(dob))


# ─── Public API ──────────────────────────────────────────────────────────────

def compute_token(
    first_name: str,
    last_name: str,
    dob,
    sex: str,
    phone: str,
    zip_code: str,
    salt: str | None = None,
) -> str:
    """
    Return the lowercase hex HMAC-SHA256 digest of:

        lower(first_name) || lower(last_name) || dob_yyyymmdd
        || sex_char || digits_only(phone) || zip5

    keyed with *salt* (the shared PPRL site-group secret).  The salt is read
    from ``settings.HTAC_PPRL_SALT`` when not supplied explicitly.  Without
    the salt, tokens from one site group cannot be linked to tokens from
    another — this is the privacy guarantee provided by HMAC over plain SHA-256.

    The six source PII fields must NEVER be persisted to the database; they
    exist only transiently in the caller's scope (CSV row / stdin line).

    Parameters
    ----------
    first_name : str
    last_name  : str
    dob        : str or date — date of birth; normalised to YYYYMMDD internally
    sex        : str — first character is used (e.g. 'M', 'F', 'U')
    phone      : str — any format; only digits are included in the hash input
    zip_code   : str — first 5 characters are used
    salt       : str | None — shared secret; defaults to settings.HTAC_PPRL_SALT

    Returns
    -------
    str — 64-character lowercase hexadecimal HMAC-SHA256 digest
    """
    if salt is None:
        salt = getattr(settings, "HTAC_PPRL_SALT", "htac-dev-pprl-salt-change-in-production")

    preimage = (
        first_name.lower()
        + last_name.lower()
        + _format_dob(dob)
        + sex[:1].lower()
        + _digits_only(phone)
        + zip_code[:5]
    )
    return hmac.new(
        salt.encode("utf-8"),
        preimage.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def deduplicate_tokens(queryset) -> int:
    """
    Cross-site PPRL deduplication.

    For every unique token value present in *queryset*:

    1. Count the number of distinct HealthSystems that hold that token
       (``site_count``).
    2. Select the canonical site: the HealthSystem whose Person record had
       the most recent VisitOccurrence across all persons sharing that token.
       Falls back to the first site found when no visits exist.
    3. Upsert one DeduplicatedRoster row keyed on ``canonical_token``.

    The operation is **idempotent** — re-running with the same queryset
    updates existing rows rather than creating duplicates.

    Enrichment flags (medicaid_flag, homeless_flag, …) are intentionally
    left at their existing / default values here; populate them separately
    via ``enrich_roster`` management command / ``enrichment.py`` services.

    Parameters
    ----------
    queryset : QuerySet[HashToken]
        May be pre-filtered (e.g. a single site); the function only touches
        tokens visible in this queryset.

    Returns
    -------
    int — number of DeduplicatedRoster rows created or updated
    """
    # Deferred import avoids any circular-import risk at module load time.
    from django.db.models import Count
    from htac.models import DeduplicatedRoster, VisitOccurrence

    # One pass to get every distinct token and its cross-site count.
    token_stats = (
        queryset
        .values("token")
        .annotate(site_count=Count("health_system", distinct=True))
        .order_by()  # remove any inherited ordering so grouping is clean
    )

    roster_version = datetime.date.today()
    upserted = 0

    for stat in token_stats:
        token_val: str = stat["token"]
        site_count: int = stat["site_count"]

        # All person PKs that carry this token across any site.
        person_ids = list(
            queryset
            .filter(token=token_val)
            .values_list("person_id", flat=True)
        )

        # Canonical site = site with the most recent visit among those persons.
        # Using select_related so health_system is fetched in the same query.
        latest_visit = (
            VisitOccurrence.objects
            .filter(person_id__in=person_ids)
            .select_related("health_system")
            .order_by("-visit_start_date")
            .first()
        )

        if latest_visit is not None:
            canonical_site = latest_visit.health_system
        else:
            # No visit records exist for any person sharing this token.
            # Use whichever site's HashToken row comes first.
            first_rec = (
                queryset
                .filter(token=token_val)
                .select_related("health_system")
                .first()
            )
            canonical_site = first_rec.health_system

        DeduplicatedRoster.objects.update_or_create(
            canonical_token=token_val,
            defaults={
                "canonical_site": canonical_site,
                "site_count": site_count,
                "roster_version": roster_version,
            },
        )
        upserted += 1

    return upserted
