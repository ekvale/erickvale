"""
Public HTAC federated pipeline demonstration — narrative + polling API.
"""

from __future__ import annotations

import threading
from types import SimpleNamespace

from django.conf import settings
from django.db import close_old_connections
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from htac.models_pipeline_run import PipelineRun, PipelineStep
from htac.pipeline_constants import PIPELINE_STEP_DEFINITIONS
from htac.pipeline_runner import execute_pipeline_run, wipe_pipeline_demo_artifacts


def _step_duration_seconds(step: PipelineStep) -> float | None:
    if step.started_at and step.completed_at:
        return round((step.completed_at - step.started_at).total_seconds(), 2)
    return None


def _run_pipeline_thread(run_id: int) -> None:
    close_old_connections()
    try:
        execute_pipeline_run(run_id)
    finally:
        close_old_connections()


@ensure_csrf_cookie
def pipeline_demo(request):
    latest = (
        PipelineRun.objects.prefetch_related("steps")
        .order_by("-created_at")
        .first()
    )
    steps_display = []
    if latest and latest.steps.exists():
        steps_display = list(latest.steps.order_by("step_number"))
        for s in steps_display:
            s.display_duration = _step_duration_seconds(s)
    else:
        for num, name in PIPELINE_STEP_DEFINITIONS:
            steps_display.append(
                SimpleNamespace(
                    step_number=num,
                    step_name=name,
                    status="pending",
                    started_at=None,
                    completed_at=None,
                    metric_label="",
                    metric_value="",
                    narrative_headline="",
                    narrative_body="",
                    technical_detail="",
                    site_data={},
                    display_duration=None,
                )
            )
    wall_secs = None
    if latest and latest.started_at and latest.completed_at:
        wall_secs = int((latest.completed_at - latest.started_at).total_seconds())
    status_url_tpl = reverse("htac_pipeline_run_status", kwargs={"run_id": 999999999})
    return render(
        request,
        "htac/pipeline_demo.html",
        {
            "run": latest,
            "steps_display": steps_display,
            "status_url_tpl": status_url_tpl,
            "run_wall_seconds": wall_secs,
        },
    )


@require_POST
def pipeline_run_start(request):
    if PipelineRun.objects.filter(status="running").exists():
        return JsonResponse(
            {"error": "A pipeline run is already in progress"},
            status=409,
        )
    wipe_pipeline_demo_artifacts()
    run = PipelineRun.objects.create(status="pending")
    for num, name in PIPELINE_STEP_DEFINITIONS:
        PipelineStep.objects.create(run=run, step_number=num, step_name=name)
    run.status = "running"
    run.started_at = timezone.now()
    run.save(update_fields=["status", "started_at"])
    threading.Thread(target=_run_pipeline_thread, args=(run.id,), daemon=True).start()
    return JsonResponse({"run_id": run.id})


def pipeline_run_status(request, run_id: int):
    run = get_object_or_404(PipelineRun, pk=run_id)
    elapsed = 0.0
    if run.started_at:
        end = run.completed_at or timezone.now()
        elapsed = round((end - run.started_at).total_seconds(), 1)
    steps_out = []
    for st in run.steps.all().order_by("step_number"):
        steps_out.append(
            {
                "step_number": st.step_number,
                "step_name": st.step_name,
                "status": st.status,
                "narrative_headline": st.narrative_headline,
                "narrative_body": st.narrative_body,
                "technical_detail": st.technical_detail,
                "metric_label": st.metric_label,
                "metric_value": st.metric_value,
                "site_data": st.site_data,
                "duration_seconds": _step_duration_seconds(st),
            }
        )
    return JsonResponse(
        {
            "run_id": run.id,
            "status": run.status,
            "elapsed_seconds": elapsed,
            "error_message": run.error_message,
            "steps": steps_out,
            "summary": {
                "total_patients_raw": run.total_patients_raw,
                "total_patients_deduplicated": run.total_patients_deduplicated,
                "cross_site_matches": run.cross_site_matches,
                "homeless_flagged": run.homeless_flagged,
                "incarcerated_flagged": run.incarcerated_flagged,
                "medicaid_flagged": run.medicaid_flagged,
                "total_estimates_generated": run.total_estimates_generated,
                "total_estimates_suppressed": run.total_estimates_suppressed,
            },
        }
    )


@require_POST
def pipeline_reset(request):
    configured = getattr(settings, "HTAC_PIPELINE_DEMO_RESET_SECRET", None)
    if configured:
        if request.POST.get("secret") != configured:
            return JsonResponse({"error": "Invalid or missing secret."}, status=403)
    else:
        if not request.user.is_authenticated or not request.user.is_staff:
            return JsonResponse(
                {"error": "Staff login required, or set HTAC_PIPELINE_DEMO_RESET_SECRET."},
                status=403,
            )
    wipe_pipeline_demo_artifacts()
    return JsonResponse({"status": "reset"})
