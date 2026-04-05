from django.urls import path

from . import contact_views, views

app_name = 'braindump'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('calendar/', views.calendar_redirect, name='calendar'),
    path(
        'calendar/<int:year>/<int:month>/',
        views.calendar_month,
        name='calendar_month',
    ),
    path('contacts/', contact_views.contact_list, name='contact_list'),
    path('contacts/new/', contact_views.contact_create, name='contact_create'),
    path(
        'contacts/email/scheduled/',
        contact_views.contact_scheduled_email_list,
        name='contact_scheduled_emails',
    ),
    path(
        'contacts/email/scheduled/<int:sched_pk>/cancel/',
        contact_views.contact_scheduled_email_cancel,
        name='contact_scheduled_email_cancel',
    ),
    path('contacts/<int:pk>/', contact_views.contact_detail, name='contact_detail'),
    path(
        'contacts/<int:pk>/email/send/',
        contact_views.contact_email_send_now,
        name='contact_email_send',
    ),
    path(
        'contacts/<int:pk>/email/schedule/',
        contact_views.contact_email_schedule,
        name='contact_email_schedule',
    ),
    path('contacts/<int:pk>/edit/', contact_views.contact_edit, name='contact_edit'),
    path('contacts/<int:pk>/delete/', contact_views.contact_delete, name='contact_delete'),
    path(
        'contacts/<int:pk>/attach/',
        contact_views.contact_attachment_add,
        name='contact_attachment_add',
    ),
    path(
        'contacts/<int:pk>/files/<int:att_pk>/delete/',
        contact_views.contact_attachment_delete,
        name='contact_attachment_delete',
    ),
    path(
        'morning-digest/send/',
        views.morning_digest_send_now,
        name='morning_digest_send_now',
    ),
    path('recurring/create/', views.recurring_create, name='recurring_create'),
    path(
        'recurring/<int:pk>/toggle/',
        views.recurring_toggle,
        name='recurring_toggle',
    ),
    path(
        'recurring/<int:pk>/delete/',
        views.recurring_delete,
        name='recurring_delete',
    ),
    path('capture/', views.capture_create, name='capture_create'),
    path('item/<int:pk>/status/', views.item_status, name='item_status'),
    path('item/<int:pk>/calendar/', views.item_calendar_date, name='item_calendar_date'),
    path('item/<int:pk>/meta/', views.item_update_meta, name='item_update_meta'),
    path('item/<int:pk>/archive/', views.item_archive, name='item_archive'),
    path('item/<int:pk>/recategorize/', views.recategorize, name='recategorize'),
]
