"""
htac/views_admin.py

Custom admin-area views for HTAC.  These are regular Django views
protected by @staff_member_required so they participate in the admin
login flow without requiring a custom AdminSite subclass.
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from htac.models import HealthSystem, DeduplicatedRoster, StudyRun


@staff_member_required(login_url="admin:login")
def about(request):
    active_sites  = HealthSystem.objects.filter(is_active=True).count()
    inactive_sites = HealthSystem.objects.filter(is_active=False).count()
    roster_count  = DeduplicatedRoster.objects.count()
    run_count     = StudyRun.objects.count()

    context = {
        "title":         "About HTAC",
        "active_sites":  active_sites,
        "inactive_sites": inactive_sites,
        "roster_count":  roster_count,
        "run_count":     run_count,
        "has_permission": request.user.is_active and request.user.is_staff,
    }
    return render(request, "admin/htac/about.html", context)
