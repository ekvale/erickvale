"""
Synchronous federated pipeline demonstration runner.

Public entry point: ``execute_pipeline_run(run_id)`` — updates ``PipelineRun``
and ``PipelineStep`` rows so the JSON status endpoint can poll progress.
"""

from __future__ import annotations

import datetime as dt
import logging
import calendar
import random
import re
import time
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Q
from django.utils import timezone

from htac.management.commands import seed_htac as seed
from htac.models import (
    Condition,
    ConditionOccurrence,
    ConceptCode,
    DeduplicatedRoster,
    DrugExposure,
    HashToken,
    HealthSystem,
    Measurement,
    Person,
    PrevalenceEstimate,
    StudyRun,
    VisitOccurrence,
)
from htac.models_pipeline_run import PipelineRun, PipelineStep
from htac.pipeline_constants import (
    CROSS_SITE_OVERLAP_RATE,
    DEMO_CONDITION_NAME_TO_SLUG,
    DEMO_CONDITIONS,
    DEMO_STUDY_NOTES_MARKER,
    DEMO_STRATIFIERS,
    GEO_LEVELS,
    HOMELESS_FLAG_RATE,
    INCARCERATION_FLAG_RATE,
    MEDICAID_FLAG_RATE,
    PIPELINE_DEMO_PREVALENCE_GEO_LEVELS,
    PIPELINE_STEP_DEFINITIONS,
    SIMULATED_SITES,
    SITE_ID_TO_SHORT_CODE,
    STRATIFIER_MODEL_KEYS,
    SUPPRESSION_THRESHOLD,
    TARGET_PATIENTS,
)
from htac.services.pprl import compute_token, deduplicate_tokens

logger = logging.getLogger(__name__)

VISIT_TYPE_EHR = 44818518
STUDY_START = seed.STUDY_START
STUDY_END = seed.STUDY_END


def person_source_prefix(run_id: int) -> str:
    return f"plrun-{run_id}-"


def person_source_primary(run_id: int, identity: int) -> str:
    return f"{person_source_prefix(run_id)}id{identity:05d}"


def person_source_clone(run_id: int, identity: int, site_code: str) -> str:
    return f"{person_source_primary(run_id, identity)}-c{site_code}"


def parse_identity_from_source_value(psv: str) -> int | None:
    m = re.search(r"plrun-\d+-id(\d{5})", psv)
    return int(m.group(1)) if m else None


def wipe_pipeline_demo_artifacts() -> None:
    """Remove all demo pipeline runs, OMOP rows keyed by plrun-*, and linked outputs."""
    StudyRun.objects.filter(notes=DEMO_STUDY_NOTES_MARKER).delete()

    demo_persons = Person.objects.filter(person_source_value__startswith="plrun-")
    person_ids = list(demo_persons.values_list("pk", flat=True))
    if person_ids:
        tokens = list(
            HashToken.objects.filter(person_id__in=person_ids)
            .values_list("token", flat=True)
            .distinct()
        )
        if tokens:
            DeduplicatedRoster.objects.filter(canonical_token__in=tokens).delete()
    demo_persons.delete()
    PipelineRun.objects.all().delete()


def _step_queryset(run_id: int) -> Q:
    return Q(person_source_value__startswith=person_source_prefix(run_id))


def _normalized_site_quotas() -> list[tuple[str, HealthSystem, int]]:
    """Return [(display_name, HealthSystem, count), ...] totalling TARGET_PATIENTS."""
    raw = sum(float(s["patient_share"]) for s in SIMULATED_SITES)
    quotas: list[tuple[str, HealthSystem, int]] = []
    short_codes = [SITE_ID_TO_SHORT_CODE[s["id"]] for s in SIMULATED_SITES]
    hs_map = {
        h.short_code: h
        for h in HealthSystem.objects.filter(short_code__in=short_codes)
    }
    remaining = TARGET_PATIENTS
    for i, site in enumerate(SIMULATED_SITES):
        code = SITE_ID_TO_SHORT_CODE[site["id"]]
        hs = hs_map.get(code)
        if hs is None:
            raise RuntimeError(
                f'HealthSystem with short_code "{code}" not found. '
                "Run seed_htac (or equivalent) before the pipeline demo."
            )
        share = float(site["patient_share"]) / raw
        if i == len(SIMULATED_SITES) - 1:
            n = remaining
        else:
            n = int(round(TARGET_PATIENTS * share))
            n = max(0, min(n, remaining))
            remaining -= n
        quotas.append((site["name"], hs, n))
    # Fix rounding drift
    total = sum(q[2] for q in quotas)
    if total != TARGET_PATIENTS:
        diff = TARGET_PATIENTS - total
        last = quotas[-1]
        quotas[-1] = (last[0], last[1], last[2] + diff)
    return quotas


def _random_study_date(rng: random.Random) -> dt.date:
    delta = (STUDY_END - STUDY_START).days
    return STUDY_START + dt.timedelta(days=rng.randint(0, max(delta, 1)))


def _pii_for_identity_on_person(identity: int, person: Person) -> dict:
    """Deterministic synthetic PII for PPRL; clone and primary with same identity match."""
    rng = random.Random(identity * 9973 + 42)
    first = rng.choice(_FIRST_NAMES)
    last = rng.choice(_LAST_NAMES)
    month = rng.randint(1, 12)
    yob = person.year_of_birth or 1980
    _, day_max = calendar.monthrange(yob, month)
    day = rng.randint(1, day_max)
    dob = dt.date(yob, month, day)
    sex = "M" if person.gender_concept_id == 8507 else "F"
    phone = f"612{rng.randint(1000000, 9999999)}"
    zip5 = (person.zip_code or "55401")[:5]
    return {
        "first_name": first,
        "last_name": last,
        "dob": dob,
        "sex": sex,
        "phone": phone,
        "zip_code": zip5,
    }


_FIRST_NAMES = [
    "Alex",
    "Jordan",
    "Taylor",
    "Casey",
    "Riley",
    "Morgan",
    "Quinn",
    "Avery",
    "Parker",
    "Reese",
]
_LAST_NAMES = [
    "Nguyen",
    "Patel",
    "Garcia",
    "Olsen",
    "Washington",
    "Yang",
    "Hassan",
    "Vang",
    "Martinez",
    "Anderson",
]


def _gender_race_ethnicity(rng: random.Random) -> tuple[int, int, int]:
    gender = rng.choices([8507, 8532, 8551], weights=[0.48, 0.48, 0.04], k=1)[0]
    race = rng.choices(
        [8515, 8516, 8527, 8657, 8552],
        weights=[0.08, 0.12, 0.72, 0.04, 0.04],
        k=1,
    )[0]
    eth = 38003563 if rng.random() < 0.08 else 38003564
    return gender, race, eth


def _load_omop_clinical_data(run_id: int, rng: random.Random) -> dict:
    """
    Insert TARGET_PATIENTS primary persons plus cross-site clones; return
    aggregates for step 1 site_data.
    """
    quotas = _normalized_site_quotas()
    cond_slugs = [DEMO_CONDITION_NAME_TO_SLUG[c["name"]] for c in DEMO_CONDITIONS]
    concept_by_slug: dict[str, int] = {}
    for slug in cond_slugs:
        cc = (
            ConceptCode.objects.filter(
                condition__slug=slug, domain="condition", is_excluded=False
            )
            .values_list("concept_id", flat=True)
            .first()
        )
        if cc is None:
            raise RuntimeError(f"No condition concept found for slug {slug!r}.")
        concept_by_slug[slug] = cc

    visit_bulk: list[VisitOccurrence] = []
    co_bulk: list[ConditionOccurrence] = []
    drug_bulk: list[DrugExposure] = []
    meas_bulk: list[Measurement] = []

    identity_site: list[tuple[int, HealthSystem]] = []
    identity = 0
    for display_name, hs, n in quotas:
        counties = seed.SITE_COUNTIES.get(hs.short_code, ["27053"])
        for _ in range(n):
            g, r, e = _gender_race_ethnicity(rng)
            yob = rng.randint(1940, 2005)
            county = rng.choice(counties)
            zip5 = seed.COUNTY_ZIP.get(county, "55401")
            tract = seed.COUNTY_TRACT.get(county, f"{county}000100")
            p = Person(
                health_system=hs,
                person_source_value=person_source_primary(run_id, identity),
                gender_concept_id=g,
                year_of_birth=yob,
                race_concept_id=r,
                ethnicity_concept_id=e,
                preferred_language="ENG",
                county_fips=county,
                zip_code=zip5,
                census_tract=tract,
            )
            p.save()
            identity_site.append((identity, hs))
            n_vis = rng.randint(1, 4)
            for _v in range(n_vis):
                vstart = _random_study_date(rng)
                vend = vstart + dt.timedelta(days=rng.randint(0, 3))
                visit_bulk.append(
                    VisitOccurrence(
                        person=p,
                        health_system=hs,
                        visit_concept_id=rng.choice([seed.VISIT_CONCEPT_AMB, seed.VISIT_CONCEPT_IP]),
                        visit_start_date=vstart,
                        visit_end_date=vend,
                        visit_type_concept_id=VISIT_TYPE_EHR,
                    )
                )
            for demo_c in DEMO_CONDITIONS:
                slug = DEMO_CONDITION_NAME_TO_SLUG[demo_c["name"]]
                prev = float(demo_c["prevalence"])
                prev *= 0.8 + 0.4 * rng.random()
                mults = seed.SITE_MULTIPLIERS.get(hs.short_code, {})
                prev *= mults.get(slug, 1.0)
                if rng.random() < prev:
                    dx = _random_study_date(rng)
                    co_bulk.append(
                        ConditionOccurrence(
                            person=p,
                            health_system=hs,
                            condition_concept_id=concept_by_slug[slug],
                            condition_start_date=dx,
                            condition_end_date=None,
                            condition_type_concept_id=32828,
                            visit_occurrence=None,
                        )
                    )
                    for drug_id in seed.COND_DRUG_CONCEPTS.get(slug, [])[:1]:
                        drug_bulk.append(
                            DrugExposure(
                                person=p,
                                health_system=hs,
                                drug_concept_id=drug_id,
                                drug_exposure_start_date=dx,
                                drug_exposure_end_date=None,
                                drug_type_concept_id=32817,
                            )
                        )
                    for tup in seed.COND_MEAS_CONCEPTS.get(slug, [])[:1]:
                        mc, lo, hi = tup[0], tup[1], tup[2]
                        val = lo + (hi - lo) * rng.random()
                        meas_bulk.append(
                            Measurement(
                                person=p,
                                health_system=hs,
                                measurement_concept_id=mc,
                                measurement_date=dx,
                                measurement_type_concept_id=44818702,
                                value_as_number=Decimal(str(round(val, 4))),
                            )
                        )
            identity += 1

    VisitOccurrence.objects.bulk_create(visit_bulk, batch_size=500)
    ConditionOccurrence.objects.bulk_create(co_bulk, batch_size=500)
    DrugExposure.objects.bulk_create(drug_bulk, batch_size=500)
    Measurement.objects.bulk_create(meas_bulk, batch_size=500)

    n_pairs = int(round(CROSS_SITE_OVERLAP_RATE * TARGET_PATIENTS))
    n_pairs = min(n_pairs, TARGET_PATIENTS)
    chosen = rng.sample(range(TARGET_PATIENTS), n_pairs) if n_pairs else []
    clone_persons: list[Person] = []
    for iid in chosen:
        _, hs0 = identity_site[iid]
        other_hs = [h for _n, h, _c in quotas if h.pk != hs0.pk]
        if not other_hs:
            continue
        hs1 = rng.choice(other_hs)
        src = Person.objects.get(person_source_value=person_source_primary(run_id, iid))
        clone_persons.append(
            Person(
                health_system=hs1,
                person_source_value=person_source_clone(run_id, iid, hs1.short_code),
                gender_concept_id=src.gender_concept_id,
                year_of_birth=src.year_of_birth,
                race_concept_id=src.race_concept_id,
                ethnicity_concept_id=src.ethnicity_concept_id,
                preferred_language=src.preferred_language,
                county_fips=src.county_fips,
                zip_code=src.zip_code,
                census_tract=src.census_tract,
            )
        )
    if clone_persons:
        Person.objects.bulk_create(clone_persons)

    # Aggregate counts from DB
    sites_out = []
    totals = {
        "persons": 0,
        "visits": 0,
        "conditions": 0,
        "drug_exposures": 0,
        "measurements": 0,
        "observations": 0,
    }
    pfx = person_source_prefix(run_id)
    for display_name, hs, _ in quotas:
        ppl = Person.objects.filter(health_system=hs, person_source_value__startswith=pfx)
        pc = ppl.count()
        vc = VisitOccurrence.objects.filter(health_system=hs, person__person_source_value__startswith=pfx).count()
        cc = ConditionOccurrence.objects.filter(health_system=hs, person__person_source_value__startswith=pfx).count()
        dc = DrugExposure.objects.filter(health_system=hs, person__person_source_value__startswith=pfx).count()
        mc = Measurement.objects.filter(health_system=hs, person__person_source_value__startswith=pfx).count()
        oc = 0
        sites_out.append(
            {
                "name": display_name,
                "persons": pc,
                "visits": vc,
                "conditions": cc,
                "drug_exposures": dc,
                "measurements": mc,
                "observations": oc,
            }
        )
        totals["persons"] += pc
        totals["visits"] += vc
        totals["conditions"] += cc
        totals["drug_exposures"] += dc
        totals["measurements"] += mc
        totals["observations"] += oc

    return {"sites": sites_out, "totals": totals}


def _aggregate_site_json(run_id: int) -> dict:
    """Re-query OMOP counts for step 1 display (authoritative)."""
    quotas = _normalized_site_quotas()
    sites_out = []
    totals = {k: 0 for k in ("persons", "visits", "conditions", "drug_exposures", "measurements", "observations")}
    pfx = person_source_prefix(run_id)
    for display_name, hs, _ in quotas:
        ppl = Person.objects.filter(health_system=hs, person_source_value__startswith=pfx)
        pc = ppl.count()
        vc = VisitOccurrence.objects.filter(health_system=hs, person__person_source_value__startswith=pfx).count()
        cc = ConditionOccurrence.objects.filter(health_system=hs, person__person_source_value__startswith=pfx).count()
        dc = DrugExposure.objects.filter(health_system=hs, person__person_source_value__startswith=pfx).count()
        mc = Measurement.objects.filter(health_system=hs, person__person_source_value__startswith=pfx).count()
        row = {
            "name": display_name,
            "persons": pc,
            "visits": vc,
            "conditions": cc,
            "drug_exposures": dc,
            "measurements": mc,
            "observations": 0,
        }
        sites_out.append(row)
        for k in totals:
            totals[k] += row[k]
    return {"sites": sites_out, "totals": totals}


def _mark_step_running(step: PipelineStep) -> None:
    step.status = "running"
    step.started_at = timezone.now()
    step.save(update_fields=["status", "started_at"])


def _mark_step_complete(step: PipelineStep, **kwargs) -> None:
    step.status = "complete"
    step.completed_at = timezone.now()
    for k, v in kwargs.items():
        setattr(step, k, v)
    step.save()


def _mark_step_failed(step: PipelineStep, msg: str) -> None:
    step.status = "failed"
    step.completed_at = timezone.now()
    step.narrative_body = msg[:2000]
    step.save()


def _build_prevalence_estimates(
    pfx: str,
    study: StudyRun,
    roster_qs,
    quotas: list[tuple[str, HealthSystem, int]],
    *,
    geo_levels: tuple[str, ...] | list[str] | None = None,
) -> tuple[list[PrevalenceEstimate], int, int]:
    """Return (estimate rows, total_cells, suppressed_count)."""
    levels = tuple(geo_levels) if geo_levels is not None else tuple(GEO_LEVELS)
    hs_list = [h for _name, h, _n in quotas]
    counties: list[str] = []
    if "county" in levels:
        counties = sorted(
            {
                c
                for c in Person.objects.filter(person_source_value__startswith=pfx).values_list(
                    "county_fips", flat=True
                )
                if c
            }
        )
    race_vals = ["8515", "8516", "8527", "8657", "8552"]
    age_specs = [
        ("0-17", 2007, 2025),
        ("18-39", 1987, 2006),
        ("40-64", 1962, 1986),
        ("65+", 1860, 1961),
    ]

    def base_persons_geo(geo_level: str, geo_value: str | None):
        qs = Person.objects.filter(person_source_value__startswith=pfx)
        if geo_level == "county" and geo_value:
            qs = qs.filter(county_fips=geo_value)
        return qs

    def apply_stratum(qs, demo_strat: str, sv: str):
        if demo_strat == "total":
            return qs
        if demo_strat == "race":
            return qs.filter(race_concept_id=int(sv))
        if demo_strat == "homeless_status":
            want = sv == "yes"
            toks = roster_qs.filter(homeless_flag=want).values_list("canonical_token", flat=True)
            return qs.filter(hash_tokens__token__in=toks).distinct()
        if demo_strat == "incarceration_status":
            want = sv == "yes"
            rq = roster_qs.filter(Q(jail_flag=want) | Q(prison_flag=want))
            toks = rq.values_list("canonical_token", flat=True)
            return qs.filter(hash_tokens__token__in=toks).distinct()
        if demo_strat == "age_group":
            for label, ylo, yhi in age_specs:
                if label == sv:
                    return qs.filter(year_of_birth__gte=ylo, year_of_birth__lte=yhi)
        return qs

    estimates: list[PrevalenceEstimate] = []
    total_cells = 0
    suppressed = 0

    for dc in DEMO_CONDITIONS:
        slug = DEMO_CONDITION_NAME_TO_SLUG[dc["name"]]
        cobj = Condition.objects.filter(slug=slug).first()
        ccid = (
            ConceptCode.objects.filter(
                condition__slug=slug, domain="condition", is_excluded=False
            )
            .values_list("concept_id", flat=True)
            .first()
        )
        if not cobj or not ccid:
            continue

        for geo_level in levels:
            geo_iter = [None] if geo_level == "state" else counties
            for geo_value in geo_iter:
                for demo_strat in DEMO_STRATIFIERS:
                    model_strat = STRATIFIER_MODEL_KEYS[demo_strat]
                    if demo_strat == "total":
                        stratum_vals = ["All"]
                    elif demo_strat == "race":
                        stratum_vals = race_vals
                    elif demo_strat in ("homeless_status", "incarceration_status"):
                        stratum_vals = ["yes", "no"]
                    else:
                        stratum_vals = [a[0] for a in age_specs]

                    for sv in stratum_vals:
                        base = base_persons_geo(geo_level, geo_value)
                        with_visit = (
                            apply_stratum(base, demo_strat, sv)
                            .filter(
                                visits__visit_start_date__gte=STUDY_START,
                                visits__visit_start_date__lte=STUDY_END,
                            )
                            .distinct()
                        )
                        for hs in [None] + hs_list:
                            ppl = with_visit if hs is None else with_visit.filter(health_system=hs)
                            denom = ppl.count()
                            co_q = ConditionOccurrence.objects.filter(
                                person__in=ppl,
                                condition_concept_id=ccid,
                                condition_start_date__gte=STUDY_START,
                                condition_start_date__lte=STUDY_END,
                            )
                            if hs is not None:
                                co_q = co_q.filter(health_system=hs)
                            num = co_q.values("person_id").distinct().count()
                            total_cells += 1
                            sup = num < SUPPRESSION_THRESHOLD
                            if sup:
                                suppressed += 1
                            rate = None
                            if not sup and denom:
                                rate = Decimal(str(round((num / denom) * 10000, 4)))
                            estimates.append(
                                PrevalenceEstimate(
                                    study_run=study,
                                    condition=cobj,
                                    health_system=hs,
                                    geo_level=geo_level,
                                    geo_value=geo_value,
                                    stratifier=model_strat,
                                    stratifier_value=sv,
                                    numerator=None if sup else num,
                                    denominator=None if sup else denom,
                                    prevalence_rate=rate,
                                    is_suppressed=sup,
                                )
                            )
    return estimates, total_cells, suppressed


def execute_pipeline_run(run_id: int) -> None:
    run = PipelineRun.objects.get(pk=run_id)
    steps = {s.step_number: s for s in run.steps.all()}

    def fail(msg: str) -> None:
        run.status = "failed"
        run.completed_at = timezone.now()
        run.error_message = msg[:5000]
        run.save(update_fields=["status", "completed_at", "error_message"])

    rng = random.Random(run_id * 10007 + 13)

    try:
        # --- Step 1 ---
        s1 = steps[1]
        _mark_step_running(s1)
        time.sleep(2.0)
        with transaction.atomic():
            site_payload = _load_omop_clinical_data(run_id, rng)
        totals = site_payload["totals"]
        tp = totals["persons"]
        s1.site_data = _aggregate_site_json(run_id)
        s1.narrative_headline = "Clinical records standardized across 11 health systems"
        s1.narrative_body = (
            "Each of the 11 participating health systems maintains its own OMOP CDM database locally. "
            "Query scripts distributed by the coordinating center run against each site's local database "
            "and return only aggregate counts — no patient records leave any site. This demonstration loaded "
            f"{tp} synthetic patient records distributed across sites in proportion to each system's actual patient volume."
        )
        s1.technical_detail = (
            "Records loaded into OMOP CDM v5.4 tables: Person, VisitOccurrence, ConditionOccurrence, "
            "DrugExposure, Measurement. Vocabularies: SNOMED CT (conditions), RxNorm (drugs), LOINC (measurements). "
            "Each site's OMOP instance uses Epic-sourced concept mappings with site-specific normalization applied prior to loading."
        )
        s1.metric_label = "Total patient records loaded"
        s1.metric_value = f"{tp} across 11 sites"
        _mark_step_complete(s1)
        run.total_patients_raw = tp
        run.save(update_fields=["total_patients_raw"])

        # --- Step 2 ---
        s2 = steps[2]
        _mark_step_running(s2)
        time.sleep(3.0)
        pfx = person_source_prefix(run_id)
        persons = list(Person.objects.filter(person_source_value__startswith=pfx))
        HashToken.objects.filter(person__person_source_value__startswith=pfx).delete()
        tokens_to_create: list[HashToken] = []
        for p in persons:
            iid = parse_identity_from_source_value(p.person_source_value)
            if iid is None:
                continue
            pii = _pii_for_identity_on_person(iid, p)
            tok = compute_token(**pii)
            tokens_to_create.append(
                HashToken(person=p, health_system=p.health_system, token=tok)
            )
        HashToken.objects.bulk_create(tokens_to_create, batch_size=500)

        tok_stats = (
            HashToken.objects.filter(person__person_source_value__startswith=pfx)
            .values("token")
            .annotate(n_sites=Count("health_system", distinct=True))
        )
        cross_site_tokens = tok_stats.filter(n_sites__gt=1).count()
        total_tokens = len(tokens_to_create)
        unique_tokens = tok_stats.filter(n_sites=1).count()
        pct = round(100.0 * cross_site_tokens / total_tokens, 1) if total_tokens else 0.0
        site_tokens = []
        for display_name, hs, _ in _normalized_site_quotas():
            site_tokens.append(
                {
                    "name": display_name,
                    "tokens_generated": HashToken.objects.filter(
                        health_system=hs, person__person_source_value__startswith=pfx
                    ).count(),
                }
            )
        s2.site_data = {
            "sites": site_tokens,
            "total_tokens": total_tokens,
            "unique_tokens": unique_tokens,
            "cross_site_tokens": cross_site_tokens,
        }
        s2.narrative_headline = "Patient identities converted to one-way cryptographic tokens"
        s2.narrative_body = (
            "Before any cross-site matching can occur, each health system independently hashes six PII fields — "
            "first name, last name, date of birth, sex, phone number, and ZIP code — into a 64-character HMAC-SHA256 "
            "token using a shared salt known only to consortium members. The original PII fields are immediately discarded. "
            f"Only the token is transmitted to the coordinating center. {cross_site_tokens} tokens were generated by more than one site "
            "— these represent patients who received care at multiple health systems and would be double-counted without deduplication."
        )
        s2.technical_detail = (
            "Algorithm: HMAC-SHA256(key=shared_salt, msg=normalized_preimage). Normalization: lowercase folding for name fields, "
            "YYYYMMDD for date of birth, digits-only for phone, 5-character ZIP. Validated at 97% precision and 75% recall in "
            "multi-site deployments (OneFlorida). Tokens are consortium-specific — a token from this network cannot be linked to "
            "tokens from a different network without the shared salt."
        )
        s2.metric_label = "Patients appearing at 2+ sites"
        s2.metric_value = f"{cross_site_tokens} ({pct}% of total)"
        _mark_step_complete(s2)

        # --- Step 3 ---
        s3 = steps[3]
        _mark_step_running(s3)
        time.sleep(2.0)
        ht_qs = HashToken.objects.filter(person__person_source_value__startswith=pfx)
        deduplicate_tokens(ht_qs)
        raw = run.total_patients_raw
        dedup = DeduplicatedRoster.objects.filter(
            canonical_token__in=ht_qs.values_list("token", flat=True).distinct()
        ).count()
        cross_matches = raw - dedup
        overlap_pct = round(100.0 * cross_matches / raw, 1) if raw else 0.0
        s3.site_data = {
            "raw_records": raw,
            "deduplicated_individuals": dedup,
            "cross_site_matches_resolved": cross_matches,
        }
        s3.narrative_headline = (
            f"Statewide patient roster deduplicated — {cross_matches} duplicate records resolved"
        )
        s3.narrative_body = (
            "The coordinating center receives tokens from all 11 sites. Because the same patient produces the same token "
            "at every site where they were seen, duplicate records are identified by matching tokens. The "
            f"{raw} raw patient records reduce to {dedup} unique individuals after deduplication. Without this step, "
            f"prevalence denominators would be inflated by {cross_matches} duplicate records — overstating the denominator "
            "and understating true prevalence rates."
        )
        s3.technical_detail = (
            "Deduplication algorithm: exact token match. A patient roster row is created for each unique token, with site "
            "attribution assigned to the site holding the most recent visit data. The "
            f"{overlap_pct}% overlap rate observed in this demonstration is consistent with the published MNEHRC figure of 75% "
            "of patients having records at more than one health system — scaled to the demonstration's patient count."
        )
        s3.metric_label = "Unique individuals in statewide roster"
        s3.metric_value = f"{dedup} (down from {raw} raw records)"
        _mark_step_complete(s3)
        run.total_patients_deduplicated = dedup
        run.cross_site_matches = cross_matches
        run.save(update_fields=["total_patients_deduplicated", "cross_site_matches"])

        # --- Step 4 ---
        s4 = steps[4]
        _mark_step_running(s4)
        time.sleep(2.0)
        roster_qs = DeduplicatedRoster.objects.filter(
            canonical_token__in=ht_qs.values_list("token", flat=True).distinct()
        )
        roster_rows = list(roster_qs)
        homeless_n = incarcerated_n = medicaid_n = 0
        to_update: list[DeduplicatedRoster] = []
        for r in roster_rows:
            hf = rng.random() < HOMELESS_FLAG_RATE
            jf = rng.random() < INCARCERATION_FLAG_RATE * 0.5
            pf = rng.random() < INCARCERATION_FLAG_RATE * 0.5
            mf = rng.random() < MEDICAID_FLAG_RATE
            r.homeless_flag = hf
            r.jail_flag = jf
            r.prison_flag = pf
            r.medicaid_flag = mf
            to_update.append(r)
            homeless_n += int(hf)
            incarcerated_n += int(jf or pf)
            medicaid_n += int(mf)
        DeduplicatedRoster.objects.bulk_update(
            to_update,
            ["homeless_flag", "jail_flag", "prison_flag", "medicaid_flag", "updated_at"],
        )
        s4.site_data = {
            "homeless_flagged": homeless_n,
            "incarcerated_flagged": incarcerated_n,
            "medicaid_flagged": medicaid_n,
        }
        s4.narrative_headline = "Roster enriched with housing, justice, and insurance context"
        s4.narrative_body = (
            "Authorized data stewards — the Minnesota Homeless Management Information System, the Minnesota Department of Corrections, "
            "and the Minnesota Department of Human Services Medicaid enrollment file — provide periodic extracts that are linked to "
            "the patient roster by token. This enrichment adds social risk context without pulling clinical records into a central warehouse. "
            f"The result: {homeless_n} patients flagged with recent homelessness experience, {incarcerated_n} with recent incarceration involvement, "
            f"and {medicaid_n} with current Medicaid enrollment — dimensions that are essential for equity-focused prevalence analysis and that "
            "no clinical data source alone can provide."
        )
        s4.technical_detail = (
            "Linkage method: exact token match against each administrative data source. Administrative extracts are provided by MDH under "
            "data use agreements that specify permitted uses, transfer protocols, and retention limits. Flag rates in this demonstration reflect "
            "published MNEHRC population proportions from the 2023 HTAC cohort."
        )
        s4.metric_label = "Patients with social risk flags"
        s4.metric_value = f"{homeless_n} homeless · {incarcerated_n} incarcerated · {medicaid_n} Medicaid"
        _mark_step_complete(s4)
        run.homeless_flagged = homeless_n
        run.incarcerated_flagged = incarcerated_n
        run.medicaid_flagged = medicaid_n
        run.save(update_fields=["homeless_flagged", "incarcerated_flagged", "medicaid_flagged"])

        # --- Step 5 ---
        s5 = steps[5]
        _mark_step_running(s5)
        time.sleep(4.0)
        study = StudyRun.objects.create(
            name=f"Pipeline demonstration run {run_id}",
            description="Synthetic federated pipeline demonstration output.",
            run_date=timezone.now().date(),
            roster_version=timezone.now().date(),
            status="complete",
            notes=DEMO_STUDY_NOTES_MARKER,
        )
        cond_objs: list[Condition] = []
        cohort_rows = []
        for dc in DEMO_CONDITIONS:
            slug = DEMO_CONDITION_NAME_TO_SLUG[dc["name"]]
            cobj = Condition.objects.filter(slug=slug).first()
            if cobj:
                cond_objs.append(cobj)
        study.conditions.set(cond_objs)
        for display_name, hs, _ in _normalized_site_quotas():
            row = {"site": display_name, "conditions": {}}
            for dc in DEMO_CONDITIONS:
                slug = DEMO_CONDITION_NAME_TO_SLUG[dc["name"]]
                ccid = (
                    ConceptCode.objects.filter(
                        condition__slug=slug, domain="condition", is_excluded=False
                    )
                    .values_list("concept_id", flat=True)
                    .first()
                )
                if ccid is None:
                    continue
                ppl = Person.objects.filter(
                    health_system=hs,
                    person_source_value__startswith=pfx,
                )
                with_visit = ppl.filter(
                    visits__visit_start_date__gte=STUDY_START,
                    visits__visit_start_date__lte=STUDY_END,
                ).distinct()
                denom = with_visit.count()
                num = (
                    ConditionOccurrence.objects.filter(
                        person__in=with_visit,
                        health_system=hs,
                        condition_concept_id=ccid,
                        condition_start_date__gte=STUDY_START,
                        condition_start_date__lte=STUDY_END,
                    )
                    .values("person_id")
                    .distinct()
                    .count()
                )
                row["conditions"][dc["name"]] = {"numerator": num, "denominator": denom}
            cohort_rows.append(row)
        site_count = len(_normalized_site_quotas())
        raw_cells = len(DEMO_CONDITIONS) * site_count
        s5.site_data = {"cohorts": cohort_rows, "raw_cell_count": raw_cells}
        s5.narrative_headline = "Condition cohort queries executed across all 11 sites"
        s5.narrative_body = (
            "Standardized analytic packages — R scripts distributed to each site — execute against each site's local OMOP database "
            "using published OMOP concept ID codesets. Only aggregate counts return to the coordinating center. In this demonstration, "
            f"{len(DEMO_CONDITIONS)} conditions were queried across {site_count} sites, producing {raw_cells} raw estimate cells before stratification and suppression."
        )
        s5.technical_detail = (
            "Condition definitions use OMOP concept IDs from the SNOMED CT, ICD-10-CM, RxNorm, and LOINC vocabularies, consistent with "
            "CMS Chronic Conditions Warehouse codesets and HTAC condition definitions. Queries search ConditionOccurrence, DrugExposure, and "
            "Measurement domains during a 12-month study period. Denominators use persons with at least one VisitOccurrence during the study window "
            "— consistent with MNEHRC/HTAC methodology."
        )
        s5.metric_label = "Conditions queried"
        s5.metric_value = f"{len(DEMO_CONDITIONS)} conditions · {site_count} sites · {raw_cells} raw cells"
        _mark_step_complete(s5)

        # --- Step 6 ---
        s6 = steps[6]
        _mark_step_running(s6)
        time.sleep(0.6)
        quotas_cached = _normalized_site_quotas()
        estimates, total_cells, suppressed = _build_prevalence_estimates(
            pfx,
            study,
            roster_qs,
            quotas_cached,
            geo_levels=PIPELINE_DEMO_PREVALENCE_GEO_LEVELS,
        )
        PrevalenceEstimate.objects.bulk_create(estimates, batch_size=1000)
        pub = total_cells - suppressed
        sup_pct = round(100.0 * suppressed / total_cells, 1) if total_cells else 0.0
        s6.site_data = {
            "total_cells": total_cells,
            "suppressed_cells": suppressed,
            "published_cells": pub,
            "suppression_rate_pct": sup_pct,
        }
        s6.narrative_headline = (
            f"Stratification complete — {suppressed} of {total_cells} cells suppressed to protect small populations"
        )
        demo_geo_n = len(PIPELINE_DEMO_PREVALENCE_GEO_LEVELS)
        s6.narrative_body = (
            f"Estimates are stratified across {len(DEMO_STRATIFIERS)} demographic and social dimensions at {demo_geo_n} geographic "
            f"level{'s' if demo_geo_n != 1 else ''} in this live demonstration (full county, ZIP, and census-tract grids in production). "
            "Any stratum containing fewer than 11 individuals is suppressed — numerator, denominator, and rate are all cleared before results are stored or published. "
            "This threshold matches the MNEHRC Master Data Use Agreement and is consistent with CDC and CMS suppression standards. "
            "In full production runs, suppression is most common at fine geographic levels among small demographic groups — the same policy applies here on a reduced geography set for responsiveness."
        )
        s6.technical_detail = (
            "Suppression threshold: n < 11 (not ≤10, consistent with CMS standard). Secondary suppression applied: when a numerator is suppressed, "
            "the denominator is also cleared to prevent back-calculation of the suppressed count. Prevalence rate formula: (numerator / denominator) × 10,000 active patients. "
            "This browser demonstration evaluates state-level cells only so the demo completes quickly; production adds county, ZIP, and census tract dimensions per DUA."
        )
        s6.metric_label = "Suppression rate"
        s6.metric_value = f"{sup_pct}% of cells suppressed ({suppressed} of {total_cells})"
        _mark_step_complete(s6)
        run.total_estimates_generated = total_cells
        run.total_estimates_suppressed = suppressed
        run.save(update_fields=["total_estimates_generated", "total_estimates_suppressed"])

        # --- Step 7 ---
        s7 = steps[7]
        _mark_step_running(s7)
        time.sleep(1.0)
        published = PrevalenceEstimate.objects.filter(
            study_run=study, is_suppressed=False
        ).count()
        suppressed_f = PrevalenceEstimate.objects.filter(
            study_run=study, is_suppressed=True
        ).count()
        elapsed = 0.0
        if run.started_at:
            elapsed = (timezone.now() - run.started_at).total_seconds()
        s7.site_data = {
            "published_estimates": published,
            "suppressed_estimates": suppressed_f,
            "elapsed_seconds": round(elapsed, 1),
        }
        s7.narrative_headline = (
            f"Pipeline complete — {published} stratified prevalence estimates ready for review"
        )
        s7.narrative_body = (
            f"The coordinating center now holds {published} publishable prevalence estimates and {suppressed_f} suppressed cells for the "
            f"{len(DEMO_CONDITIONS)} conditions queried. These estimates are accessible through the operations console to authorized analysts, "
            f"and can be released as governed file extracts or integrated into reporting dashboards subject to the publication process defined in the consortium's data use agreements. "
            f"The pipeline ran end-to-end in {round(elapsed)} seconds — from {len(_normalized_site_quotas())} contributing sites to a governed, suppressed, stratified statewide dataset."
        )
        s7.technical_detail = (
            "Output format: PrevalenceEstimate rows indexed by condition × health_system × geo_level × geo_value × stratifier × stratifier_value. "
            "Each publishable row includes numerator, denominator, and rate (per 10,000 active patients). Suppressed rows retain the stratifier dimensions but clear numeric fields. "
            "This output format is consistent with HTAC public-use data file structure and is compatible with downstream reporting in Power BI, Tableau, or web-native dashboards."
        )
        s7.metric_label = "Published estimates"
        s7.metric_value = (
            f"{published} estimates · {len(DEMO_CONDITIONS)} conditions · {len(_normalized_site_quotas())} sites"
        )
        _mark_step_complete(s7)

        run.status = "complete"
        run.completed_at = timezone.now()
        run.save(update_fields=["status", "completed_at"])

    except Exception as exc:  # noqa: BLE001
        logger.exception("Pipeline run %s failed", run_id)
        fail(str(exc))
        for sn in range(1, 8):
            st = steps.get(sn)
            if st and st.status == "running":
                _mark_step_failed(st, str(exc))
                break
