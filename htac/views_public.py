"""
htac/views_public.py

Public-facing views for the HTAC app — no login required.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from django.db.models import Avg, Count, Max, Min
from django.urls import NoReverseMatch, reverse
from django.views.generic import TemplateView

from htac.models import (
    Condition,
    ConceptCode,
    ConditionOccurrence,
    DataQualityReport,
    DeduplicatedRoster,
    DOCRecord,
    DrugExposure,
    HashToken,
    HealthSystem,
    HMISRecord,
    Measurement,
    MedicaidEnrollment,
    MIICRecord,
    Observation,
    Person,
    PrevalenceEstimate,
    StudyRun,
    VitalStatisticsRecord,
    VisitOccurrence,
)
from htac.models_pipeline_run import PipelineRun, PipelineStep
from htac.pipeline_constants import DEMO_STUDY_NOTES_MARKER
from htac.pipeline_runner import person_source_prefix


class HTACAboutView(TemplateView):
    template_name = "htac/about.html"


# ── Pipeline step registry ─────────────────────────────────────────────────────

PIPELINE_STEPS = [
    {"num": 1, "label": "Clinical Data",      "url_name": "htac_pipeline_step1"},
    {"num": 2, "label": "PPRL Tokens",        "url_name": "htac_pipeline_step2"},
    {"num": 3, "label": "Deduplication",      "url_name": "htac_pipeline_step3"},
    {"num": 4, "label": "Enrichment",         "url_name": "htac_pipeline_step4"},
    {"num": 5, "label": "Cohort Queries",     "url_name": "htac_pipeline_step5"},
    {"num": 6, "label": "Suppression",        "url_name": "htac_pipeline_step6"},
    {"num": 7, "label": "Results",            "url_name": "htac_pipeline_step7"},
]


def _latest_completed_demo_run():
    return PipelineRun.objects.filter(status="complete").order_by("-completed_at").first()


def _demo_person_prefix_for_run(run):
    if not run:
        return None
    return person_source_prefix(run.pk)


def _resolve_steps(current_step: int) -> Tuple[List[Dict[str, Any]], Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Return (steps_with_urls, prev_step, next_step) for template context."""
    steps = []
    for s in PIPELINE_STEPS:
        step = dict(s)
        if s["url_name"]:
            try:
                step["url"] = reverse(s["url_name"])
            except NoReverseMatch:
                step["url"] = None
        else:
            step["url"] = None
        steps.append(step)

    prev_step = next((s for s in steps if s["num"] == current_step - 1), None)
    next_step = next((s for s in steps if s["num"] == current_step + 1), None)
    return steps, prev_step, next_step


# ── Step 1: Clinical Data in OMOP CDM ─────────────────────────────────────────

class PipelineStep1View(TemplateView):
    template_name = "htac/pipeline/step1_omop.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        steps, prev_step, next_step = _resolve_steps(1)
        ctx.update({"pipeline_steps": steps, "current_step": 1,
                    "prev_step": prev_step, "next_step": next_step})

        demo_run = _latest_completed_demo_run()
        demo_step = demo_run.steps.filter(step_number=1).first() if demo_run else None
        pfx = _demo_person_prefix_for_run(demo_run)

        active_sites = list(HealthSystem.objects.filter(is_active=True).order_by("name"))
        if pfx:
            site_stats = [
                {
                    "name":         site.name,
                    "persons":      Person.objects.filter(health_system=site, person_source_value__startswith=pfx).count(),
                    "visits":       VisitOccurrence.objects.filter(health_system=site, person__person_source_value__startswith=pfx).count(),
                    "conditions":   ConditionOccurrence.objects.filter(health_system=site, person__person_source_value__startswith=pfx).count(),
                    "drugs":        DrugExposure.objects.filter(health_system=site, person__person_source_value__startswith=pfx).count(),
                    "measurements": Measurement.objects.filter(health_system=site, person__person_source_value__startswith=pfx).count(),
                    "observations": Observation.objects.filter(health_system=site, person__person_source_value__startswith=pfx).count(),
                }
                for site in active_sites
            ]
        else:
            site_stats = [
                {
                    "name":         site.name,
                    "persons":      Person.objects.filter(health_system=site).count(),
                    "visits":       VisitOccurrence.objects.filter(health_system=site).count(),
                    "conditions":   ConditionOccurrence.objects.filter(health_system=site).count(),
                    "drugs":        DrugExposure.objects.filter(health_system=site).count(),
                    "measurements": Measurement.objects.filter(health_system=site).count(),
                    "observations": Observation.objects.filter(health_system=site).count(),
                }
                for site in active_sites
            ]
        ctx["site_stats"] = site_stats
        ctx["totals"] = {k: sum(s[k] for s in site_stats)
                         for k in ("persons", "visits", "conditions",
                                   "drugs", "measurements", "observations")}
        ctx["demo_run"] = demo_run
        ctx["demo_step"] = demo_step
        ctx["pipeline_demo_counts"] = bool(pfx)
        return ctx


# ── Step 2: PPRL Token Generation ─────────────────────────────────────────────

class PipelineStep2View(TemplateView):
    template_name = "htac/pipeline/step2_pprl.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        steps, prev_step, next_step = _resolve_steps(2)
        ctx.update({"pipeline_steps": steps, "current_step": 2,
                    "prev_step": prev_step, "next_step": next_step})

        demo_run = _latest_completed_demo_run()
        demo_step = demo_run.steps.filter(step_number=2).first() if demo_run else None
        pfx = _demo_person_prefix_for_run(demo_run)

        active_sites = list(HealthSystem.objects.filter(is_active=True).order_by("name"))
        if pfx:
            token_stats = [
                {
                    "name": site.name,
                    "tokens": HashToken.objects.filter(
                        health_system=site, person__person_source_value__startswith=pfx
                    ).count(),
                }
                for site in active_sites
            ]
            cross_site_count = (
                HashToken.objects.filter(
                    person__person_source_value__startswith=pfx,
                    health_system__is_active=True,
                )
                .values("token")
                .annotate(n_sites=Count("health_system", distinct=True))
                .filter(n_sites__gt=1)
                .count()
            )
        else:
            token_stats = [
                {"name": site.name,
                 "tokens": HashToken.objects.filter(health_system=site).count()}
                for site in active_sites
            ]
            cross_site_count = (
                HashToken.objects.filter(health_system__is_active=True)
                .values("token")
                .annotate(n_sites=Count("health_system", distinct=True))
                .filter(n_sites__gt=1)
                .count()
            )
        total_tokens = sum(s["tokens"] for s in token_stats)

        ctx.update({
            "token_stats":       token_stats,
            "total_tokens":      total_tokens,
            "cross_site_count":  cross_site_count,
            "demo_run":          demo_run,
            "demo_step":         demo_step,
            "pipeline_demo_counts": bool(pfx),
        })
        return ctx


# ── Step 3: Cross-Site Deduplication ──────────────────────────────────────────

class PipelineStep3View(TemplateView):
    template_name = "htac/pipeline/step3_dedup.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        steps, prev_step, next_step = _resolve_steps(3)
        ctx.update({"pipeline_steps": steps, "current_step": 3,
                    "prev_step": prev_step, "next_step": next_step})

        demo_run = _latest_completed_demo_run()
        demo_step = demo_run.steps.filter(step_number=3).first() if demo_run else None
        pfx = _demo_person_prefix_for_run(demo_run)
        if pfx:
            demo_tokens = HashToken.objects.filter(
                person__person_source_value__startswith=pfx
            ).values_list("token", flat=True)
            r = DeduplicatedRoster.objects.filter(canonical_token__in=demo_tokens)
        else:
            r = DeduplicatedRoster.objects

        roster_total = r.count()
        multi_site   = r.filter(site_count__gt=1).count()
        single_site  = roster_total - multi_site
        agg = r.aggregate(
            max_sites=Max("site_count"),
            avg_sites=Avg("site_count"),
        )

        site_count_dist = list(
            r.values("site_count")
            .annotate(n=Count("id"))
            .order_by("site_count")
        )

        ctx.update({
            "roster_total":      roster_total,
            "multi_site":        multi_site,
            "single_site":       single_site,
            "max_sites":         agg["max_sites"] or 0,
            "avg_sites":         round(agg["avg_sites"] or 1, 2),
            "site_count_dist":   site_count_dist,
            "demo_run":          demo_run,
            "demo_step":         demo_step,
            "pipeline_demo_counts": bool(pfx),
        })
        return ctx


# ── Step 4: State Data Enrichment ─────────────────────────────────────────────

class PipelineStep4View(TemplateView):
    template_name = "htac/pipeline/step4_enrichment.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        steps, prev_step, next_step = _resolve_steps(4)
        ctx.update({"pipeline_steps": steps, "current_step": 4,
                    "prev_step": prev_step, "next_step": next_step})

        demo_run = _latest_completed_demo_run()
        demo_step = demo_run.steps.filter(step_number=4).first() if demo_run else None
        pfx = _demo_person_prefix_for_run(demo_run)
        if pfx:
            toks = HashToken.objects.filter(
                person__person_source_value__startswith=pfx
            ).values_list("token", flat=True)
            r = DeduplicatedRoster.objects.filter(canonical_token__in=toks)
        else:
            r = DeduplicatedRoster.objects

        roster_total = r.count()
        ctx.update({
            "roster_total":   roster_total,
            "enrichment_flags": {
                "Medicaid enrolled":      r.filter(medicaid_flag=True).count(),
                "Homeless / unstably housed": r.filter(homeless_flag=True).count(),
                "Jailed":                 r.filter(jail_flag=True).count(),
                "Incarcerated (prison)":  r.filter(prison_flag=True).count(),
                "COVID vaccinated":       r.filter(covid_vaccinated_flag=True).count(),
                "Influenza vaccinated":   r.filter(influenza_vaccinated_flag=True).count(),
                "Deceased":               r.filter(deceased_flag=True).count(),
            },
            "staging_counts": {
                "MedicaidEnrollment": MedicaidEnrollment.objects.count(),
                "HMISRecord":         HMISRecord.objects.count(),
                "DOCRecord":          DOCRecord.objects.count(),
                "MIICRecord":         MIICRecord.objects.count(),
                "VitalStatisticsRecord": VitalStatisticsRecord.objects.count(),
            },
            "demo_run": demo_run,
            "demo_step": demo_step,
            "pipeline_demo_counts": bool(pfx),
        })
        return ctx


# ── Step 5: Condition Cohort Queries ──────────────────────────────────────────

class PipelineStep5View(TemplateView):
    template_name = "htac/pipeline/step5_cohorts.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        steps, prev_step, next_step = _resolve_steps(5)
        ctx.update({"pipeline_steps": steps, "current_step": 5,
                    "prev_step": prev_step, "next_step": next_step})

        conditions = list(
            Condition.objects
            .filter(is_active=True)
            .prefetch_related("concept_codes")
            .order_by("htac_category", "name")
        )
        condition_rows = []
        for cond in conditions:
            codes = cond.concept_codes.all()
            domain_counts = {d: 0 for d, _ in ConceptCode.DOMAIN_CHOICES}
            for cc in codes:
                domain_counts[cc.domain] = domain_counts.get(cc.domain, 0) + 1
            condition_rows.append({
                "name":      cond.name,
                "category":  cond.get_htac_category_display(),
                "total":     codes.count(),
                "condition": domain_counts.get("condition", 0),
                "drug":      domain_counts.get("drug", 0),
                "measurement": domain_counts.get("measurement", 0),
                "observation": domain_counts.get("observation", 0),
            })

        total_codes = ConceptCode.objects.count()
        domain_totals = {
            d_label: ConceptCode.objects.filter(domain=d_code).count()
            for d_code, d_label in ConceptCode.DOMAIN_CHOICES
        }

        ctx.update({
            "condition_rows": condition_rows,
            "total_codes":    total_codes,
            "domain_totals":  domain_totals,
            "condition_count": len(condition_rows),
        })
        demo_run = _latest_completed_demo_run()
        demo_step = demo_run.steps.filter(step_number=5).first() if demo_run else None
        ctx["demo_run"] = demo_run
        ctx["demo_step"] = demo_step
        ctx["pipeline_demo_cohorts"] = (
            (demo_step.site_data or {}).get("cohorts") if demo_step else None
        )
        return ctx


# ── Step 6: Stratification & Suppression ──────────────────────────────────────

class PipelineStep6View(TemplateView):
    template_name = "htac/pipeline/step6_suppression.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        steps, prev_step, next_step = _resolve_steps(6)
        ctx.update({"pipeline_steps": steps, "current_step": 6,
                    "prev_step": prev_step, "next_step": next_step})

        demo_run = _latest_completed_demo_run()
        demo_step = demo_run.steps.filter(step_number=6).first() if demo_run else None
        pfx = _demo_person_prefix_for_run(demo_run)
        demo_study = (
            StudyRun.objects.filter(notes=DEMO_STUDY_NOTES_MARKER).order_by("-id").first()
        )
        if demo_study:
            est_q = PrevalenceEstimate.objects.filter(study_run=demo_study)
        else:
            est_q = PrevalenceEstimate.objects

        estimate_count   = est_q.count()
        suppressed_count = est_q.filter(is_suppressed=True).count()
        published_count  = estimate_count - suppressed_count

        ctx.update({
            "estimate_count":   estimate_count,
            "suppressed_count": suppressed_count,
            "published_count":  published_count,
            "suppression_pct":  round(suppressed_count / estimate_count * 100, 1) if estimate_count else 0,
            "stratifiers":      PrevalenceEstimate.STRATIFIER_CHOICES,
            "geo_levels":       PrevalenceEstimate.GEO_LEVEL_CHOICES,
            "demo_run":         demo_run,
            "demo_step":        demo_step,
            "pipeline_demo_counts": bool(pfx),
        })
        return ctx


# ── Step 7: Prevalence Results ────────────────────────────────────────────────

class PipelineStep7View(TemplateView):
    template_name = "htac/pipeline/step7_results.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        steps, prev_step, next_step = _resolve_steps(7)
        ctx.update({"pipeline_steps": steps, "current_step": 7,
                    "prev_step": prev_step, "next_step": next_step})

        demo_run = _latest_completed_demo_run()
        demo_step = demo_run.steps.filter(step_number=7).first() if demo_run else None
        pfx = _demo_person_prefix_for_run(demo_run)
        demo_study = (
            StudyRun.objects.filter(notes=DEMO_STUDY_NOTES_MARKER).order_by("-id").first()
        )
        if demo_study:
            est_q = PrevalenceEstimate.objects.filter(study_run=demo_study)
        else:
            est_q = PrevalenceEstimate.objects

        estimate_count   = est_q.count()
        suppressed_count = est_q.filter(is_suppressed=True).count()
        study_runs       = list(StudyRun.objects.order_by("-run_date"))
        dq_count         = DataQualityReport.objects.count()

        condition_counts = list(
            est_q.values("condition__name")
            .annotate(n=Count("id"))
            .order_by("-n")[:10]
        ) if estimate_count else []

        ctx.update({
            "estimate_count":   estimate_count,
            "suppressed_count": suppressed_count,
            "published_count":  estimate_count - suppressed_count,
            "study_runs":       study_runs,
            "dq_count":         dq_count,
            "condition_counts": condition_counts,
            "demo_run":         demo_run,
            "demo_step":        demo_step,
            "pipeline_demo_counts": bool(pfx),
        })
        return ctx
