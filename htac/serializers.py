"""
htac/serializers.py

Django REST Framework serializers for the HTAC API.

Hierarchy
---------
Brief serializers (id + key display fields only) are used for nested
representations inside larger objects.  Full serializers are used at
the top-level list / detail endpoints.

N+1 notes
---------
Callers that use nested serializers should apply the appropriate
select_related / prefetch_related in their queryset:
  - ConditionSerializer           → prefetch_related("concept_codes")
  - StudyRunSerializer            → prefetch_related("conditions")
                                    select_related("run_by")
  - PrevalenceEstimateSerializer  → select_related("study_run",
                                                   "condition",
                                                   "health_system")
"""

from rest_framework import serializers

from htac.models import (
    Condition,
    ConceptCode,
    HealthSystem,
    PrevalenceEstimate,
    StudyRun,
)


# ── Brief / nested serializers ────────────────────────────────────────────────

class HealthSystemBriefSerializer(serializers.ModelSerializer):
    """Minimal HealthSystem representation used as a nested field."""

    class Meta:
        model  = HealthSystem
        fields = ["id", "short_code", "name"]


class ConditionBriefSerializer(serializers.ModelSerializer):
    """Minimal Condition representation used as a nested field."""

    class Meta:
        model  = Condition
        fields = ["slug", "name", "htac_category"]


class StudyRunBriefSerializer(serializers.ModelSerializer):
    """Minimal StudyRun representation used inside PrevalenceEstimate."""

    class Meta:
        model  = StudyRun
        fields = ["id", "name", "run_date", "status"]


# ── Full serializers ──────────────────────────────────────────────────────────

class HealthSystemSerializer(serializers.ModelSerializer):
    """
    Full HealthSystem serializer.
    Intentionally excludes any patient-level or count fields.
    """

    class Meta:
        model  = HealthSystem
        fields = ["id", "name", "short_code", "is_active", "created_at"]


class ConceptCodeSerializer(serializers.ModelSerializer):
    """
    Full ConceptCode serializer — used for the
    GET /conditions/{slug}/codesets/ endpoint.
    """
    added_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model  = ConceptCode
        fields = [
            "id",
            "concept_id",
            "concept_name",
            "domain",
            "vocabulary_id",
            "is_excluded",
            "added_by",
            "added_date",
            "notes",
        ]


class ConditionSerializer(serializers.ModelSerializer):
    """
    Full Condition serializer — used for GET /conditions/.

    ``concept_code_count`` avoids an extra attribute query when the
    viewset annotates the queryset with::

        from django.db.models import Count
        qs.annotate(concept_code_count=Count("concept_codes"))

    If no annotation is present, it falls back to a per-object query via
    the ``SerializerMethodField``.
    """
    concept_code_count = serializers.SerializerMethodField()

    class Meta:
        model  = Condition
        fields = [
            "id",
            "name",
            "slug",
            "htac_category",
            "description",
            "is_active",
            "concept_code_count",
        ]

    def get_concept_code_count(self, obj) -> int:
        # Use the annotated value when available (avoids the extra query).
        if hasattr(obj, "concept_code_count"):
            return obj.concept_code_count
        return obj.concept_codes.count()


class StudyRunSerializer(serializers.ModelSerializer):
    """
    Full StudyRun serializer — used for GET /study-runs/.
    Conditions are rendered as brief objects (slug + name + category).
    """
    conditions = ConditionBriefSerializer(many=True, read_only=True)
    run_by     = serializers.StringRelatedField(read_only=True)

    class Meta:
        model  = StudyRun
        fields = [
            "id",
            "name",
            "description",
            "run_date",
            "roster_version",
            "status",
            "conditions",
            "run_by",
            "notes",
        ]


class PrevalenceEstimateSerializer(serializers.ModelSerializer):
    """
    Full PrevalenceEstimate serializer — used for:
      GET /study-runs/{id}/results/
      GET /prevalence/

    Suppressed cells are returned with ``is_suppressed=True`` and
    ``null`` numerator / denominator / prevalence_rate — clients must
    inspect ``is_suppressed`` before displaying counts.

    ``health_system`` is nullable (null = statewide aggregate).
    """
    condition    = ConditionBriefSerializer(read_only=True)
    health_system = HealthSystemBriefSerializer(read_only=True, allow_null=True)
    study_run    = StudyRunBriefSerializer(read_only=True)

    class Meta:
        model  = PrevalenceEstimate
        fields = [
            "id",
            "study_run",
            "condition",
            "health_system",
            "geo_level",
            "geo_value",
            "stratifier",
            "stratifier_value",
            "numerator",
            "denominator",
            "prevalence_rate",
            "is_suppressed",
            "created_at",
        ]
