from django.urls import path

from . import views

# All URL patterns for this app live in this single module so we use one application
# namespace ("projects") while serving /projects/, /contacts/, /calendar/, and /notifications/
# from the site root (Django does not allow duplicate app_name includes).
app_name = 'projects'

urlpatterns = [
    path('projects/', views.project_list, name='project_list'),
    path('projects/create/', views.project_create, name='project_create'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/<int:pk>/edit/', views.project_edit, name='project_edit'),
    path('projects/<int:pk>/tasks/', views.task_list, name='task_list'),
    path('projects/<int:pk>/tasks/create/', views.task_create, name='task_create'),
    path('projects/<int:pk>/tasks/<int:task_pk>/', views.task_detail, name='task_detail'),
    path('projects/<int:pk>/tasks/<int:task_pk>/edit/', views.task_edit, name='task_edit'),
    path('projects/<int:pk>/documents/', views.document_list, name='document_list'),
    path('projects/<int:pk>/documents/upload/', views.document_upload, name='document_upload'),
    path('projects/<int:pk>/members/', views.member_list, name='member_list'),
    path('contacts/', views.contact_list, name='contact_list'),
    path('contacts/create/', views.contact_create, name='contact_create'),
    path('contacts/<int:pk>/', views.contact_detail, name='contact_detail'),
    path('contacts/<int:pk>/edit/', views.contact_edit, name='contact_edit'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('calendar/events/create/', views.event_create, name='event_create'),
    path('calendar/events/<int:pk>/edit/', views.event_edit, name='event_edit'),
    path('calendar/events/json/', views.event_json, name='event_json'),
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/mark-read/', views.notification_mark_read, name='notification_mark_read'),
]
