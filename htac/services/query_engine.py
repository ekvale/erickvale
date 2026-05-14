"""
htac/services/query_engine.py

Condition cohort query and stratification engine.

Public API
----------
get_condition_cohort(condition, health_system, study_period) -> QuerySet[Person]
    Applies a condition's ConceptCode include/exclude list across all four
    OMOP clinical domains and returns qualifying Person records for one site.

stratify_cohort(cohort_qs, stratifier, roster_qs, study_period=None) -> dict
    Counts numerators (cohort) and denominators for each value of a
    stratification dimension.  When study_period is supplied the denominator
    is restricted to persons with ≥ 1 visit in that period (active-enrollment definition);
    otherwise it falls back to all persons at the site.
    Returns {stratifier_value: {"numerator": int, "denominator": int}}.

apply_suppression(results_dict, threshold=11) -> dict
    Adds prevalence_rate and is_suppressed keys; nulls counts for cells
    below the suppression threshold.

Raw SQL policy
--------------
All logic below uses the Django ORM.  Raw SQL is not needed at simulation
scale (≤ 500 persons, 11 sites).  If this engine is ported to a production
OMOP database with millions of rows, the age-group bucketing loop in
_stratify_age_group and the person→roster flag joins in
_build_person_flag_map would be the first candidates for raw SQL or
database-side CASE expressions.
"""

import datetime
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Count, Q


# ── OMOP standard concept ID → human-readable label ──────────────────────────
# Covers the concepts used by HTAC seed data; unknown IDs fall through to
# "Concept:<id>" so nothing is silently dropped.

_GENDER_LABELS: dict[int, str] = {
    8507: "Male",
    8532: "Female",
    8521: "Unknown",
}

_RACE_LABELS: dict[int, str] = {
    8515: "Asian",
    8516: "Black or African American",
    8527: "White",
    8557: "Native Hawaiian or Other Pacific Islander",
    8657: "American Indian or Alaska Native",
    8522: "Other Race",
    0:    "Unknown",
}

_ETHNICITY_LABELS: dict[int, str] = {
    38003563: "Hispanic or Latino",
    38003564: "Not Hispanic or Latino",
    0:        "Unknown",
}

_AGE_BUCKETS: list[tuple[int, int, str]] = [
    (0,  17,  "0-17"),
    (18, 34,  "18-34"),
    (35, 49,  "35-49"),
    (50, 64,  "50-64"),
    (65, 999, "65+"),
]


def _gender_label(concept_id: int) -> str:
    return _GENDER_LABELS.get(concept_id, f"Concept:{concept_id}")


def _race_label(concept_id: int) -> str:
    return _RACE_LABELS.get(concept_id, f"Concept:{concept_id}")


def _ethnicity_label(concept_id: int) -> str:
    return _ETHNICITY_LABELS.get(concept_id, f"Concept:{concept_id}")


def _age_group(year_of_birth: int, reference_year: int) -> str:
    age = reference_year - year_of_birth
    for lo, hi, label in _AGE_BUCKETS:
        if lo <= age <= hi:
            return label
    return "Unknown"


# ── Public API ─────────────────────────────────────────────────────────────────

def get_condition_cohort(condition, health_system, study_period):
    """
    Return a Person QuerySet for *health_system* meeting *condition*'s
    codeset criteria within *study_period*.

    Algorithm
    ---------
    1. Partition the condition's ConceptCodes into included and excluded
       sets, keyed by OMOP domain (condition / drug / measurement / observation).
    2. Build an OR filter across all included domains: a Person qualifies if
       they have at least one matching clinical event in any domain within the
       study period.
    3. Exclude any Person who also has a matching excluded concept code event.

    Parameters
    ----------
    condition     : htac.models.Condition
    health_system : htac.models.HealthSystem
    study_period  : tuple[date, date] — (start_date, end_date) inclusive

    Returns
    -------
    QuerySet[Person] — lazy; evaluated by the caller
    """
    from htac.models import (
        ConditionOccurrence,
        DrugExposure,
        Measurement,
        Observation,
        Person,
    )

    start_date, end_date = study_period

    included: dict[str, list[int]] = defaultdict(list)
    excluded: dict[str, list[int]] = defaultdict(list)

    for cc in condition.concept_codes.all():
        target = excluded if cc.is_excluded else included
        target[cc.domain].append(cc.concept_id)

    # ── Inclusion (OR across all domains) ─────────────────────────────────────
    inclusion_q = Q()

    if included["condition"]:
        inclusion_q |= Q(id__in=ConditionOccurrence.objects.filter(
            health_system=health_system,
            condition_concept_id__in=included["condition"],
            condition_start_date__range=(start_date, end_date),
        ).values("person_id"))

    if included["drug"]:
        inclusion_q |= Q(id__in=DrugExposure.objects.filter(
            health_system=health_system,
            drug_concept_id__in=included["drug"],
            drug_exposure_start_date__range=(start_date, end_date),
        ).values("person_id"))

    if included["measurement"]:
        inclusion_q |= Q(id__in=Measurement.objects.filter(
            health_system=health_system,
            measurement_concept_id__in=included["measurement"],
            measurement_date__range=(start_date, end_date),
        ).values("person_id"))

    if included["observation"]:
        inclusion_q |= Q(id__in=Observation.objects.filter(
            health_system=health_system,
            observation_concept_id__in=included["observation"],
            observation_date__range=(start_date, end_date),
        ).values("person_id"))

    if not inclusion_q:
        return Person.objects.none()

    qs = Person.objects.filter(health_system=health_system).filter(inclusion_q)

    # ── Exclusion (OR across all domains) ─────────────────────────────────────
    exclusion_q = Q()

    if excluded["condition"]:
        exclusion_q |= Q(id__in=ConditionOccurrence.objects.filter(
            health_system=health_system,
            condition_concept_id__in=excluded["condition"],
            condition_start_date__range=(start_date, end_date),
        ).values("person_id"))

    if excluded["drug"]:
        exclusion_q |= Q(id__in=DrugExposure.objects.filter(
            health_system=health_system,
            drug_concept_id__in=excluded["drug"],
            drug_exposure_start_date__range=(start_date, end_date),
        ).values("person_id"))

    if excluded["measurement"]:
        exclusion_q |= Q(id__in=Measurement.objects.filter(
            health_system=health_system,
            measurement_concept_id__in=excluded["measurement"],
            measurement_date__range=(start_date, end_date),
        ).values("person_id"))

    if excluded["observation"]:
        exclusion_q |= Q(id__in=Observation.objects.filter(
            health_system=health_system,
            observation_concept_id__in=excluded["observation"],
            observation_date__range=(start_date, end_date),
        ).values("person_id"))

    if exclusion_q:
        qs = qs.exclude(exclusion_q)

    return qs


def stratify_cohort(cohort_qs, stratifier: str, roster_qs, study_period=None) -> dict:
    """
    Count numerators and denominators for each value of *stratifier*.

    Parameters
    ----------
    cohort_qs    : QuerySet[Person] — persons WITH the condition (numerator pool);
                   must already be filtered to a single HealthSystem
    stratifier   : str — one of the PrevalenceEstimate.STRATIFIER_CHOICES values
    roster_qs    : QuerySet[DeduplicatedRoster] — used to resolve enrichment
                   flags for the homeless / incarceration / medicaid stratifiers
    study_period : tuple[date, date] | None — (start_date, end_date) inclusive.
                   When supplied, the denominator is persons with ≥ 1 visit in
                   the period (active-enrollment definition).  When None, all persons at
                   the site are used as the denominator.

    Returns
    -------
    dict  {stratifier_value: {"numerator": int, "denominator": int}}

    Numerator   = count of cohort_qs persons in the stratum
    Denominator = count of persons with ≥ 1 visit in study_period (if provided)
                  OR all Person records at the HealthSystem (fallback)
    """
    from htac.models import Person, VisitOccurrence

    # Infer health_system from the pre-filtered cohort queryset.
    hs_ids = list(
        cohort_qs.values_list("health_system_id", flat=True).distinct()
    )
    if not hs_ids:
        return {}

    health_system_id = hs_ids[0]

    if study_period is not None:
        start_date, end_date = study_period
        active_ids = (
            VisitOccurrence.objects
            .filter(
                health_system_id=health_system_id,
                visit_start_date__range=(start_date, end_date),
            )
            .values_list("person_id", flat=True)
            .distinct()
        )
        denom_qs = Person.objects.filter(
            health_system_id=health_system_id,
            id__in=active_ids,
        )
    else:
        denom_qs = Person.objects.filter(health_system_id=health_system_id)

    reference_year = datetime.date.today().year

    dispatch = {
        "total":        lambda: _stratify_total(cohort_qs, denom_qs),
        "race":         lambda: _stratify_person_field(cohort_qs, denom_qs, "race_concept_id", _race_label),
        "ethnicity":    lambda: _stratify_person_field(cohort_qs, denom_qs, "ethnicity_concept_id", _ethnicity_label),
        "language":     lambda: _stratify_person_field(cohort_qs, denom_qs, "preferred_language", lambda v: v or "Unknown"),
        "sex":          lambda: _stratify_person_field(cohort_qs, denom_qs, "gender_concept_id", _gender_label),
        "age_group":    lambda: _stratify_age_group(cohort_qs, denom_qs, reference_year),
        "homeless":     lambda: _stratify_roster_flag(cohort_qs, denom_qs, "homeless", roster_qs),
        "incarceration":lambda: _stratify_roster_flag(cohort_qs, denom_qs, "incarceration", roster_qs),
        "medicaid":     lambda: _stratify_roster_flag(cohort_qs, denom_qs, "medicaid", roster_qs),
    }

    handler = dispatch.get(stratifier)
    return handler() if handler else {}


def apply_suppression(results_dict: dict, threshold: int = 11) -> dict:
    """
    Apply small-cell suppression to a ``stratify_cohort`` result.

    Cells where numerator < *threshold* are suppressed: numerator,
    denominator, and prevalence_rate are set to None and is_suppressed
    is set to True.  Cells at or above threshold get a computed
    prevalence_rate rounded to 4 decimal places.

    Parameters
    ----------
    results_dict : dict — {stratifier_value: {"numerator": int, "denominator": int}}
    threshold    : int  — suppression floor (default 11, per HTAC policy)

    Returns
    -------
    dict — {stratifier_value: {
                "numerator":       int | None,
                "denominator":     int | None,
                "prevalence_rate": Decimal | None,
                "is_suppressed":   bool,
            }}
    """
    out = {}
    for stratum, counts in results_dict.items():
        numerator   = counts["numerator"]
        denominator = counts["denominator"]

        if numerator < threshold:
            out[stratum] = {
                "numerator":       None,
                "denominator":     None,
                "prevalence_rate": None,
                "is_suppressed":   True,
            }
        else:
            if denominator > 0:
                rate = (
                    Decimal(numerator) * Decimal(10000) / Decimal(denominator)
                ).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            else:
                rate = None

            out[stratum] = {
                "numerator":       numerator,
                "denominator":     denominator,
                "prevalence_rate": rate,
                "is_suppressed":   False,
            }
    return out


# ── Private stratification helpers ────────────────────────────────────────────

def _stratify_total(cohort_qs, denom_qs) -> dict:
    return {
        "All": {
            "numerator":   cohort_qs.count(),
            "denominator": denom_qs.count(),
        }
    }


def _stratify_person_field(cohort_qs, denom_qs, field: str, label_fn) -> dict:
    """Group by a Person model field using database-side COUNT."""
    numerators = {
        row[field]: row["n"]
        for row in cohort_qs.values(field).annotate(n=Count("id"))
    }
    denominators = {
        row[field]: row["n"]
        for row in denom_qs.values(field).annotate(n=Count("id"))
    }

    result = {}
    for raw_val in set(numerators) | set(denominators):
        label = label_fn(raw_val)
        cell = result.setdefault(label, {"numerator": 0, "denominator": 0})
        cell["numerator"]   += numerators.get(raw_val, 0)
        cell["denominator"] += denominators.get(raw_val, 0)
    return result


def _stratify_age_group(cohort_qs, denom_qs, reference_year: int) -> dict:
    """
    Bucket persons into age groups using year_of_birth.
    Fetches only the year_of_birth column; bucketing runs in Python.
    At simulation scale this is fast; at production scale push the CASE
    expression to SQL.
    """
    def count_groups(qs) -> dict:
        groups: dict[str, int] = defaultdict(int)
        for yob in qs.values_list("year_of_birth", flat=True).iterator():
            groups[_age_group(yob, reference_year)] += 1
        return groups

    numerators   = count_groups(cohort_qs)
    denominators = count_groups(denom_qs)

    result = {}
    for grp in set(numerators) | set(denominators):
        result[grp] = {
            "numerator":   numerators.get(grp, 0),
            "denominator": denominators.get(grp, 0),
        }
    return result


def _build_person_flag_map(person_qs, roster_qs, flag_attr: str) -> dict[int, bool]:
    """
    Return {person_id: flag_value} by joining Person → HashToken → DeduplicatedRoster.

    For the "incarceration" pseudo-flag, *flag_attr* is the sentinel string
    "incarceration" and the value is derived from (jail_flag OR prison_flag).
    """
    from htac.models import HashToken

    # Step 1: build token → flag from roster (one DB query)
    if flag_attr == "incarceration":
        token_to_flag: dict[str, bool] = {
            r.canonical_token: (r.jail_flag or r.prison_flag)
            for r in roster_qs.only("canonical_token", "jail_flag", "prison_flag").iterator()
        }
    else:
        token_to_flag = {
            r.canonical_token: getattr(r, flag_attr)
            for r in roster_qs.only("canonical_token", flag_attr).iterator()
        }

    # Step 2: map person_id → flag via HashToken (one DB query)
    person_ids = list(person_qs.values_list("id", flat=True))
    pid_to_flag: dict[int, bool] = {}
    for ht in HashToken.objects.filter(person_id__in=person_ids).only("person_id", "token").iterator():
        flag_val = token_to_flag.get(ht.token)
        if flag_val is not None:
            pid_to_flag[ht.person_id] = flag_val

    return pid_to_flag


def _stratify_roster_flag(cohort_qs, denom_qs, stratifier: str, roster_qs) -> dict:
    """
    Stratify by an enrichment flag stored on DeduplicatedRoster.
    Joins Person → HashToken → DeduplicatedRoster to resolve the flag.
    Returns {"True": {...}, "False": {...}}.
    """
    flag_attr = {
        "homeless":     "homeless_flag",
        "incarceration": "incarceration",   # special-cased in _build_person_flag_map
        "medicaid":     "medicaid_flag",
    }[stratifier]

    cohort_flags = _build_person_flag_map(cohort_qs, roster_qs, flag_attr)
    denom_flags  = _build_person_flag_map(denom_qs,  roster_qs, flag_attr)

    num_true  = sum(1 for v in cohort_flags.values() if v)
    num_false = sum(1 for v in cohort_flags.values() if not v)
    den_true  = sum(1 for v in denom_flags.values()  if v)
    den_false = sum(1 for v in denom_flags.values()  if not v)

    return {
        "True":  {"numerator": num_true,  "denominator": den_true},
        "False": {"numerator": num_false, "denominator": den_false},
    }
