"""
htac/services/enrichment.py

Enrichment services — one function per state data source.

Each function:
  1. Queries its staging table for all canonical tokens in *roster_qs*.
  2. Performs a complete refresh of its own flag / date fields on every
     roster row in *roster_qs* — matched rows get True, unmatched rows
     get False / None.  Fields owned by other sources are never touched.
  3. Uses bulk_update for efficiency (two DB round-trips per call regardless
     of roster size).
  4. Returns the count of roster records where the primary flag was set True.

All functions are idempotent: re-running with the same queryset and the same
staging data produces identical results.
"""

from django.db.models import Max, Min


def enrich_from_medicaid(roster_qs) -> int:
    """
    Populate ``medicaid_flag`` and ``medicaid_effective_date`` from
    ``MedicaidEnrollment``.

    ``medicaid_effective_date`` is the earliest effective_date across all
    enrollment periods for that token.

    Returns
    -------
    int — number of roster records where medicaid_flag was set True
    """
    from htac.models import DeduplicatedRoster, MedicaidEnrollment

    tokens = _token_list(roster_qs)

    matched: dict = {
        row["token_hash"]: row["earliest"]
        for row in (
            MedicaidEnrollment.objects
            .filter(token_hash__in=tokens)
            .values("token_hash")
            .annotate(earliest=Min("effective_date"))
        )
    }

    records = list(roster_qs.only("id", "canonical_token"))
    for rec in records:
        hit = matched.get(rec.canonical_token)
        rec.medicaid_flag = hit is not None
        rec.medicaid_effective_date = hit

    DeduplicatedRoster.objects.bulk_update(
        records, ["medicaid_flag", "medicaid_effective_date"]
    )
    return len(matched)


def enrich_from_hmis(roster_qs) -> int:
    """
    Populate ``homeless_flag`` and ``homeless_first_service_date`` from
    ``HMISRecord``.

    ``homeless_first_service_date`` is the earliest entry_date across all
    HMIS service records for that token, regardless of service type.

    Returns
    -------
    int — number of roster records where homeless_flag was set True
    """
    from htac.models import DeduplicatedRoster, HMISRecord

    tokens = _token_list(roster_qs)

    matched: dict = {
        row["token_hash"]: row["earliest"]
        for row in (
            HMISRecord.objects
            .filter(token_hash__in=tokens)
            .values("token_hash")
            .annotate(earliest=Min("entry_date"))
        )
    }

    records = list(roster_qs.only("id", "canonical_token"))
    for rec in records:
        hit = matched.get(rec.canonical_token)
        rec.homeless_flag = hit is not None
        rec.homeless_first_service_date = hit

    DeduplicatedRoster.objects.bulk_update(
        records, ["homeless_flag", "homeless_first_service_date"]
    )
    return len(matched)


def enrich_from_doc(roster_qs) -> int:
    """
    Populate jail and prison flags from ``DOCRecord``.

    Jail and prison are handled separately in two filtered queries so that
    a token appearing in both record types gets both flags set.

    - ``jail_flag`` / ``jail_admission_date``   — earliest jail admission
    - ``prison_flag`` / ``prison_admission_date`` — earliest prison admission

    Returns
    -------
    int — number of roster records where at least one DOC flag was set True
    """
    from htac.models import DeduplicatedRoster, DOCRecord

    tokens = _token_list(roster_qs)

    jail_matches: dict = {
        row["token_hash"]: row["earliest"]
        for row in (
            DOCRecord.objects
            .filter(token_hash__in=tokens, record_type="jail")
            .values("token_hash")
            .annotate(earliest=Min("admission_date"))
        )
    }

    prison_matches: dict = {
        row["token_hash"]: row["earliest"]
        for row in (
            DOCRecord.objects
            .filter(token_hash__in=tokens, record_type="prison")
            .values("token_hash")
            .annotate(earliest=Min("admission_date"))
        )
    }

    records = list(roster_qs.only("id", "canonical_token"))
    for rec in records:
        jail_hit = jail_matches.get(rec.canonical_token)
        prison_hit = prison_matches.get(rec.canonical_token)
        rec.jail_flag = jail_hit is not None
        rec.jail_admission_date = jail_hit
        rec.prison_flag = prison_hit is not None
        rec.prison_admission_date = prison_hit

    DeduplicatedRoster.objects.bulk_update(
        records,
        ["jail_flag", "jail_admission_date", "prison_flag", "prison_admission_date"],
    )
    return len(set(jail_matches) | set(prison_matches))


def enrich_from_miic(roster_qs) -> int:
    """
    Populate COVID and influenza vaccination flags from ``MIICRecord``.

    - ``covid_vaccinated_flag`` / ``covid_vaccine_date`` — earliest COVID-19
      vaccination date for that token
    - ``influenza_vaccinated_flag``                      — True if any
      influenza record exists (no date stored on the roster)

    Returns
    -------
    int — number of roster records where at least one vaccination flag was set True
    """
    from htac.models import DeduplicatedRoster, MIICRecord

    tokens = _token_list(roster_qs)

    covid_matches: dict = {
        row["token_hash"]: row["earliest"]
        for row in (
            MIICRecord.objects
            .filter(token_hash__in=tokens, vaccine_type="covid")
            .values("token_hash")
            .annotate(earliest=Min("vaccination_date"))
        )
    }

    flu_tokens: set = set(
        MIICRecord.objects
        .filter(token_hash__in=tokens, vaccine_type="influenza")
        .values_list("token_hash", flat=True)
        .distinct()
    )

    records = list(roster_qs.only("id", "canonical_token"))
    for rec in records:
        covid_hit = covid_matches.get(rec.canonical_token)
        rec.covid_vaccinated_flag = covid_hit is not None
        rec.covid_vaccine_date = covid_hit
        rec.influenza_vaccinated_flag = rec.canonical_token in flu_tokens

    DeduplicatedRoster.objects.bulk_update(
        records,
        ["covid_vaccinated_flag", "covid_vaccine_date", "influenza_vaccinated_flag"],
    )
    return len(set(covid_matches) | flu_tokens)


def enrich_from_vitals(roster_qs) -> int:
    """
    Populate ``deceased_flag`` and ``death_date`` from
    ``VitalStatisticsRecord``.

    If multiple death records exist for the same token (data quality issue),
    the latest death_date is used.

    Returns
    -------
    int — number of roster records where deceased_flag was set True
    """
    from htac.models import DeduplicatedRoster, VitalStatisticsRecord

    tokens = _token_list(roster_qs)

    matched: dict = {
        row["token_hash"]: row["latest"]
        for row in (
            VitalStatisticsRecord.objects
            .filter(token_hash__in=tokens)
            .values("token_hash")
            .annotate(latest=Max("death_date"))
        )
    }

    records = list(roster_qs.only("id", "canonical_token"))
    for rec in records:
        hit = matched.get(rec.canonical_token)
        rec.deceased_flag = hit is not None
        rec.death_date = hit

    DeduplicatedRoster.objects.bulk_update(
        records, ["deceased_flag", "death_date"]
    )
    return len(matched)


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _token_list(roster_qs) -> list:
    """Return a plain list of canonical_token strings from *roster_qs*."""
    return list(roster_qs.values_list("canonical_token", flat=True))
