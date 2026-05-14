"""
htac/views.py

Django REST Framework ViewSets for the HTAC API.

All endpoints are read-only (GET only).  Permission is set to
IsAuthenticatedOrReadOnly by default — tighten to IsAuthenticated in
production by adding DEFAULT_PERMISSION_CLASSES to settings.py.

Endpoints
---------
GET  /api/htac/v1/conditions/
GET  /api/htac/v1/conditions/{slug}/codesets/
GET  /api/htac/v1/health-systems/
GET  /api/htac/v1/study-runs/
GET  /api/htac/v1/study-runs/{id}/results/
GET  /api/htac/v1/prevalence/

Filtering (query params)
------------------------
Shared params (all estimate endpoints):
  condition       — Condition.slug            e.g. ?condition=diabetes
  geo_level       — state|county|zip|census_tract
  geo_value       — FIPS / ZIP / tract string
  stratifier      — race|ethnicity|language|sex|age_group|
                    homeless|incarceration|medicaid|total
  health_system   — HealthSystem.short_code   e.g. ?health_system=ALLINA
  is_suppressed   — true|false

Additional params for /prevalence/ only:
  run_date_after  — YYYY-MM-DD (inclusive)
  run_date_before — YYYY-MM-DD (inclusive)
  study_run       — StudyRun.id

Pagination
----------
Default page size: 100 rows.  Override with ?page_size=N (max 1 000).
"""

from django.db.models import Count
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from htac.models import (
    Condition,
    HealthSystem,
    PrevalenceEstimate,
    StudyRun,
)
from htac.serializers import (
    ConditionSerializer,
    ConceptCodeSerializer,
    HealthSystemSerializer,
    PrevalenceEstimateSerializer,
    StudyRunSerializer,
)


# ── Pagination ────────────────────────────────────────────────────────────────

class HtacPagination(PageNumberPagination):
    page_size              = 100
    page_size_query_param  = "page_size"
    max_page_size          = 1000


# ── Shared filter helper ──────────────────────────────────────────────────────

def _filter_estimates(qs, params):
    """
    Apply common query-param filters to a PrevalenceEstimate queryset.
    Unknown / blank values are silently ignored so clients can pass
    empty params without error.
    """
    if slug := params.get("condition", "").strip():
        qs = qs.filter(condition__slug=slug)

    if geo_level := params.get("geo_level", "").strip():
        qs = qs.filter(geo_level=geo_level)

    if geo_value := params.get("geo_value", "").strip():
        qs = qs.filter(geo_value=geo_value)

    if stratifier := params.get("stratifier", "").strip():
        qs = qs.filter(stratifier=stratifier)

    if hs_code := params.get("health_system", "").strip():
        qs = qs.filter(health_system__short_code=hs_code)

    is_sup = params.get("is_suppressed", "").strip().lower()
    if is_sup == "true":
        qs = qs.filter(is_suppressed=True)
    elif is_sup == "false":
        qs = qs.filter(is_suppressed=False)

    return qs


# ── ViewSets ──────────────────────────────────────────────────────────────────

class ConditionViewSet(ReadOnlyModelViewSet):
    """
    GET /conditions/
        List all 22 HTAC conditions with slug, name, category, and
        concept_code_count.

    GET /conditions/{slug}/codesets/
        List all ConceptCode rows for the condition identified by *slug*.
    """
    serializer_class   = ConditionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field       = "slug"
    pagination_class   = None   # 22 conditions — no pagination needed

    def get_queryset(self):
        return (
            Condition.objects
            .filter(is_active=True)
            .annotate(concept_code_count=Count("concept_codes"))
            .prefetch_related("concept_codes")
            .order_by("name")
        )

    @action(
        detail=True,
        methods=["get"],
        url_path="codesets",
        url_name="codesets",
    )
    def codesets(self, request, slug=None):
        """Return all concept codes for a single condition."""
        condition = self.get_object()
        codes = (
            condition.concept_codes
            .select_related("added_by")
            .order_by("domain", "vocabulary_id", "concept_id")
        )
        serializer = ConceptCodeSerializer(codes, many=True)
        return Response(serializer.data)


class HealthSystemViewSet(ReadOnlyModelViewSet):
    """
    GET /health-systems/
        List all active MNEHRC health systems.
        No patient-level data or counts are exposed.
    """
    serializer_class   = HealthSystemSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class   = None   # 11 sites — no pagination needed

    def get_queryset(self):
        return (
            HealthSystem.objects
            .filter(is_active=True)
            .order_by("name")
        )


class StudyRunViewSet(ReadOnlyModelViewSet):
    """
    GET /study-runs/
        List all study runs with name, run_date, roster_version, status,
        and the conditions included in each run.

    GET /study-runs/{id}/results/
        Paginated PrevalenceEstimate rows for a single study run.

        Query params: condition, geo_level, geo_value, stratifier,
                      health_system, is_suppressed
    """
    serializer_class   = StudyRunSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class   = HtacPagination

    def get_queryset(self):
        return (
            StudyRun.objects
            .prefetch_related("conditions")
            .select_related("run_by")
            .order_by("-run_date")
        )

    @action(
        detail=True,
        methods=["get"],
        url_path="results",
        url_name="results",
    )
    def results(self, request, pk=None):
        """
        Paginated PrevalenceEstimate records for one StudyRun.

        Suppressed cells are included in the response with
        is_suppressed=True and null numerator / denominator /
        prevalence_rate — clients decide how to render them.
        """
        study_run = self.get_object()

        qs = (
            PrevalenceEstimate.objects
            .filter(study_run=study_run)
            .select_related("condition", "health_system", "study_run")
            .order_by(
                "condition__slug",
                "geo_level",
                "geo_value",
                "stratifier",
                "stratifier_value",
            )
        )
        qs = _filter_estimates(qs, request.query_params)

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = PrevalenceEstimateSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = PrevalenceEstimateSerializer(qs, many=True)
        return Response(serializer.data)


class PrevalenceEstimateViewSet(ReadOnlyModelViewSet):
    """
    GET /prevalence/
        Query prevalence estimates across all study runs.

        Query params (in addition to the shared estimate params):
          study_run       — StudyRun.id
          run_date_after  — YYYY-MM-DD  (study_run__run_date >=)
          run_date_before — YYYY-MM-DD  (study_run__run_date <=)
    """
    serializer_class   = PrevalenceEstimateSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class   = HtacPagination

    def get_queryset(self):
        qs = (
            PrevalenceEstimate.objects
            .select_related("condition", "health_system", "study_run")
            .order_by(
                "-study_run__run_date",
                "condition__slug",
                "stratifier",
                "stratifier_value",
            )
        )

        params = self.request.query_params
        qs = _filter_estimates(qs, params)

        # /prevalence/-specific filters
        if study_run_id := params.get("study_run", "").strip():
            try:
                qs = qs.filter(study_run_id=int(study_run_id))
            except ValueError:
                pass   # ignore malformed int; return unfiltered

        if after := params.get("run_date_after", "").strip():
            qs = qs.filter(study_run__run_date__gte=after)

        if before := params.get("run_date_before", "").strip():
            qs = qs.filter(study_run__run_date__lte=before)

        return qs
