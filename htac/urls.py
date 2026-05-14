"""
htac/urls.py

DRF router registration for the HTAC API.

All routes are mounted under /api/htac/v1/ by the project-level urls.py:

    path("api/htac/v1/", include("htac.urls")),

Generated URL patterns
----------------------
  GET  /api/htac/v1/conditions/
  GET  /api/htac/v1/conditions/{slug}/
  GET  /api/htac/v1/conditions/{slug}/codesets/
  GET  /api/htac/v1/health-systems/
  GET  /api/htac/v1/health-systems/{id}/
  GET  /api/htac/v1/study-runs/
  GET  /api/htac/v1/study-runs/{id}/
  GET  /api/htac/v1/study-runs/{id}/results/
  GET  /api/htac/v1/prevalence/
  GET  /api/htac/v1/prevalence/{id}/

The router also exposes a browsable API root at /api/htac/v1/.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from htac.views import (
    ConditionViewSet,
    HealthSystemViewSet,
    PrevalenceEstimateViewSet,
    StudyRunViewSet,
)

router = DefaultRouter()
router.register(r"conditions",     ConditionViewSet,          basename="htac-condition")
router.register(r"health-systems", HealthSystemViewSet,       basename="htac-health-system")
router.register(r"study-runs",     StudyRunViewSet,           basename="htac-study-run")
router.register(r"prevalence",     PrevalenceEstimateViewSet, basename="htac-prevalence")

urlpatterns = [
    path("", include(router.urls)),
]
