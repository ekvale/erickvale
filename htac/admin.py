"""
htac/admin.py

Django admin registrations for all HTAC models.

Custom admin classes (per spec):
  HealthSystemAdmin       — patient_count annotation
  ConditionAdmin          — concept_code_count annotation, ConceptCode inline
  StudyRunAdmin           — run_queries + export_csv actions
  PrevalenceEstimateAdmin — list_filter, search_fields, all fields read-only
  DeduplicatedRosterAdmin — token_short (first 8 chars), flag columns
  DataQualityReportAdmin  — colored_flag method column

Remaining models are registered with lightweight ModelAdmin classes
sufficient for inspection and data QA.

Note: StudyRun.run_queries calls execute_condition_queries synchronously.
In production, delegate long-running runs to a Celery task instead.
"""

import csv
import io

from django.contrib import admin

from django.core.management import call_command
from django.db.models import Count
from django.http import HttpResponse
from django.utils.html import format_html

from htac.models import (
    ConditionOccurrence,
    Condition,
    ConceptCode,
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


# ── HealthSystem ──────────────────────────────────────────────────────────────

@admin.register(HealthSystem)
class HealthSystemAdmin(admin.ModelAdmin):
    list_display  = ["name", "short_code", "is_active", "patient_count", "created_at"]
    list_filter   = ["is_active"]
    search_fields = ["name", "short_code"]
    readonly_fields = ["created_at"]

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .annotate(patient_count=Count("persons", distinct=True))
        )

    @admin.display(description="Patients", ordering="patient_count")
    def patient_count(self, obj):
        return obj.patient_count


# ── Condition + ConceptCode inline ────────────────────────────────────────────

class ConceptCodeInline(admin.TabularInline):
    model           = ConceptCode
    extra           = 0
    fields          = [
        "concept_id", "concept_name", "domain",
        "vocabulary_id", "is_excluded", "notes",
    ]
    readonly_fields = ["added_date", "added_by"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("added_by")


@admin.register(Condition)
class ConditionAdmin(admin.ModelAdmin):
    list_display       = ["name", "slug", "htac_category", "is_active", "concept_code_count"]
    list_filter        = ["htac_category", "is_active"]
    search_fields      = ["name", "slug"]
    prepopulated_fields = {"slug": ["name"]}
    inlines            = [ConceptCodeInline]

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .annotate(concept_code_count=Count("concept_codes"))
        )

    @admin.display(description="Codes", ordering="concept_code_count")
    def concept_code_count(self, obj):
        return obj.concept_code_count


# ── StudyRun ──────────────────────────────────────────────────────────────────

@admin.register(StudyRun)
class StudyRunAdmin(admin.ModelAdmin):
    list_display     = ["name", "run_date", "roster_version", "status", "run_by", "estimate_count"]
    list_filter      = ["status"]
    search_fields    = ["name"]
    filter_horizontal = ["conditions"]
    readonly_fields  = ["run_by", "status"]
    actions          = ["action_run_queries", "action_export_csv"]

    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related("run_by")
            .annotate(estimate_count=Count("estimates"))
        )

    @admin.display(description="Estimates", ordering="estimate_count")
    def estimate_count(self, obj):
        return obj.estimate_count

    # ── Admin actions ─────────────────────────────────────────────────────────

    @admin.action(description="▶  Execute condition queries for selected runs")
    def action_run_queries(self, request, queryset):
        """
        Runs execute_condition_queries for each selected StudyRun.
        Only processes runs whose status is 'pending' or 'failed'.
        Uses the default study period (calendar year before run_date).

        Production note: replace call_command() with a Celery task
        to avoid blocking the HTTP response on long runs.
        """
        for study_run in queryset.order_by("run_date"):
            if study_run.status not in ("pending", "failed"):
                self.message_user(
                    request,
                    f"Skipped '{study_run.name}' — status is '{study_run.status}'.",
                    level="warning",
                )
                continue
            try:
                call_command(
                    "execute_condition_queries",
                    study_run_id=study_run.pk,
                    verbosity=1,
                )
                self.message_user(
                    request,
                    f"'{study_run.name}' completed successfully.",
                )
            except Exception as exc:
                self.message_user(
                    request,
                    f"'{study_run.name}' failed: {exc}",
                    level="error",
                )

    @admin.action(description="⬇  Export prevalence estimates to CSV")
    def action_export_csv(self, request, queryset):
        """
        Stream a CSV of all PrevalenceEstimate rows for the selected runs.
        Suppressed cells are included with blank count/rate columns.
        """
        run_ids = list(queryset.values_list("pk", flat=True))
        estimates = (
            PrevalenceEstimate.objects
            .filter(study_run_id__in=run_ids)
            .select_related("study_run", "condition", "health_system")
            .order_by(
                "study_run__run_date",
                "condition__slug",
                "geo_level",
                "geo_value",
                "stratifier",
                "stratifier_value",
            )
        )

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "study_run", "run_date",
            "condition_slug", "condition_name",
            "health_system",
            "geo_level", "geo_value",
            "stratifier", "stratifier_value",
            "numerator", "denominator", "prevalence_rate",
            "is_suppressed",
        ])

        for est in estimates.iterator(chunk_size=500):
            writer.writerow([
                est.study_run.name,
                est.study_run.run_date,
                est.condition.slug,
                est.condition.name,
                est.health_system.short_code if est.health_system else "statewide",
                est.geo_level,
                est.geo_value or "",
                est.stratifier,
                est.stratifier_value,
                est.numerator   if not est.is_suppressed else "",
                est.denominator if not est.is_suppressed else "",
                est.prevalence_rate if not est.is_suppressed else "",
                est.is_suppressed,
            ])

        suffix = "_".join(
            (r.name or "")[:15].replace(" ", "_")
            for r in queryset[:3]
        )
        response = HttpResponse(buf.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="htac_estimates_{suffix}.csv"'
        )
        return response


# ── PrevalenceEstimate ────────────────────────────────────────────────────────

@admin.register(PrevalenceEstimate)
class PrevalenceEstimateAdmin(admin.ModelAdmin):
    list_display  = [
        "condition", "health_system", "geo_level", "stratifier",
        "stratifier_value", "numerator", "denominator",
        "prevalence_rate", "is_suppressed",
    ]
    list_filter   = [
        "condition", "stratifier", "is_suppressed",
        "health_system", "geo_level",
    ]
    search_fields = ["geo_value", "stratifier_value"]
    readonly_fields = [
        "study_run", "condition", "health_system",
        "geo_level", "geo_value", "stratifier", "stratifier_value",
        "numerator", "denominator", "prevalence_rate",
        "is_suppressed", "created_at",
    ]
    list_select_related = ["condition", "health_system", "study_run"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# ── DeduplicatedRoster ────────────────────────────────────────────────────────

@admin.register(DeduplicatedRoster)
class DeduplicatedRosterAdmin(admin.ModelAdmin):
    list_display  = [
        "token_short", "canonical_site", "site_count",
        "medicaid_flag", "homeless_flag", "jail_flag",
        "prison_flag", "deceased_flag", "roster_version",
    ]
    list_filter   = [
        "canonical_site",
        "medicaid_flag", "homeless_flag",
        "jail_flag", "prison_flag", "deceased_flag",
        "roster_version",
    ]
    search_fields     = ["canonical_token"]
    readonly_fields   = ["canonical_token", "created_at", "updated_at"]
    list_select_related = ["canonical_site"]

    @admin.display(description="Token (first 8)")
    def token_short(self, obj):
        return f"{obj.canonical_token[:8]}…"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# ── DataQualityReport ─────────────────────────────────────────────────────────

@admin.register(DataQualityReport)
class DataQualityReportAdmin(admin.ModelAdmin):
    list_display  = [
        "health_system", "run_date", "metric_name",
        "metric_value", "colored_flag", "threshold",
    ]
    list_filter   = ["health_system", "flag", "run_date"]
    readonly_fields = [
        "health_system", "run_date", "metric_name",
        "metric_value", "flag", "threshold",
    ]
    list_select_related = ["health_system"]

    _FLAG_COLORS = {"pass": "#2a9d2a", "warn": "#d07000", "fail": "#c0392b"}

    @admin.display(description="Flag")
    def colored_flag(self, obj):
        color = self._FLAG_COLORS.get(obj.flag, "#333")
        return format_html(
            '<b style="color: {};">{}</b>',
            color,
            obj.flag.upper(),
        )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# ── Supporting models — lightweight registrations ─────────────────────────────

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display  = [
        "id", "health_system", "person_source_value",
        "gender_concept_id", "year_of_birth",
        "race_concept_id", "county_fips", "zip_code",
    ]
    list_filter   = ["health_system"]
    search_fields = ["person_source_value"]
    list_select_related = ["health_system"]
    readonly_fields = [f.name for f in Person._meta.fields]


@admin.register(VisitOccurrence)
class VisitOccurrenceAdmin(admin.ModelAdmin):
    list_display  = ["id", "person", "health_system", "visit_concept_id", "visit_start_date"]
    list_filter   = ["health_system"]
    list_select_related = ["person", "health_system"]
    readonly_fields = [f.name for f in VisitOccurrence._meta.fields]


@admin.register(ConditionOccurrence)
class ConditionOccurrenceAdmin(admin.ModelAdmin):
    list_display  = ["id", "person", "health_system", "condition_concept_id", "condition_start_date"]
    list_filter   = ["health_system"]
    search_fields = ["condition_concept_id"]
    list_select_related = ["person", "health_system"]
    readonly_fields = [f.name for f in ConditionOccurrence._meta.fields]


@admin.register(DrugExposure)
class DrugExposureAdmin(admin.ModelAdmin):
    list_display  = ["id", "person", "health_system", "drug_concept_id", "drug_exposure_start_date"]
    list_filter   = ["health_system"]
    list_select_related = ["person", "health_system"]
    readonly_fields = [f.name for f in DrugExposure._meta.fields]


@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    list_display  = ["id", "person", "health_system", "measurement_concept_id", "measurement_date"]
    list_filter   = ["health_system"]
    list_select_related = ["person", "health_system"]
    readonly_fields = [f.name for f in Measurement._meta.fields]


@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    list_display  = ["id", "person", "health_system", "observation_concept_id", "observation_date"]
    list_filter   = ["health_system"]
    list_select_related = ["person", "health_system"]
    readonly_fields = [f.name for f in Observation._meta.fields]


@admin.register(HashToken)
class HashTokenAdmin(admin.ModelAdmin):
    list_display  = ["id", "health_system", "person", "token_short", "generated_at"]
    list_filter   = ["health_system"]
    list_select_related = ["health_system", "person"]
    readonly_fields = [f.name for f in HashToken._meta.fields]

    @admin.display(description="Token (first 8)")
    def token_short(self, obj):
        return f"{obj.token[:8]}…"

    def has_add_permission(self, request):
        return False


@admin.register(MedicaidEnrollment)
class MedicaidEnrollmentAdmin(admin.ModelAdmin):
    list_display  = ["id", "token_hash_short", "effective_date", "end_date", "coverage_type", "loaded_at"]
    search_fields = ["token_hash"]

    @admin.display(description="Token hash")
    def token_hash_short(self, obj):
        return f"{obj.token_hash[:8]}…"


@admin.register(HMISRecord)
class HMISRecordAdmin(admin.ModelAdmin):
    list_display  = ["id", "token_hash_short", "service_type", "entry_date", "exit_date", "loaded_at"]
    list_filter   = ["service_type"]

    @admin.display(description="Token hash")
    def token_hash_short(self, obj):
        return f"{obj.token_hash[:8]}…"


@admin.register(DOCRecord)
class DOCRecordAdmin(admin.ModelAdmin):
    list_display  = ["id", "token_hash_short", "record_type", "admission_date", "facility_name", "loaded_at"]
    list_filter   = ["record_type"]

    @admin.display(description="Token hash")
    def token_hash_short(self, obj):
        return f"{obj.token_hash[:8]}…"


@admin.register(MIICRecord)
class MIICRecordAdmin(admin.ModelAdmin):
    list_display  = ["id", "token_hash_short", "vaccine_type", "vaccination_date", "cvx_code", "loaded_at"]
    list_filter   = ["vaccine_type"]

    @admin.display(description="Token hash")
    def token_hash_short(self, obj):
        return f"{obj.token_hash[:8]}…"


@admin.register(VitalStatisticsRecord)
class VitalStatisticsRecordAdmin(admin.ModelAdmin):
    list_display  = ["id", "token_hash_short", "death_date", "cause_of_death_icd10", "loaded_at"]

    @admin.display(description="Token hash")
    def token_hash_short(self, obj):
        return f"{obj.token_hash[:8]}…"


# ── Pipeline demonstration runs ───────────────────────────────────────────────


class PipelineStepInline(admin.TabularInline):
    model = PipelineStep
    extra = 0
    readonly_fields = (
        "step_number",
        "step_name",
        "status",
        "started_at",
        "completed_at",
        "narrative_headline",
        "metric_label",
        "metric_value",
    )
    can_delete = False


@admin.register(PipelineRun)
class PipelineRunAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "status",
        "started_at",
        "completed_at",
        "total_patients_raw",
        "total_patients_deduplicated",
        "created_at",
    ]
    list_filter = ["status"]
    readonly_fields = ["created_at"]
    inlines = [PipelineStepInline]
