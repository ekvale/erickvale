from django.urls import path

from . import views

app_name = 'dream_blue'

urlpatterns = [
    path(
        'grantscout/',
        views.grantscout_dashboard,
        name='grantscout_dashboard',
    ),
    path(
        'operations/calendar/',
        views.operations_calendar,
        name='operations_calendar',
    ),
    path(
        'operations/calendar.ics',
        views.operations_calendar_ics_feed,
        name='operations_calendar_ics',
    ),
    path(
        'operations/units/',
        views.units_dashboard,
        name='units_dashboard',
    ),
    path(
        'api/grantscout/latest.json',
        views.grantscout_latest_api,
        name='grantscout_latest_api',
    ),
    path(
        'api/operations/calendar-events.json',
        views.operations_calendar_events_api,
        name='operations_calendar_events_api',
    ),
    path(
        'api/operations/expense-summary.json',
        views.operations_expense_summary_api,
        name='operations_expense_summary_api',
    ),
]
