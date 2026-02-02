"""
URL configuration for All Minnesota app.
Namespace: allminnesota
"""
from django.urls import path
from . import views

app_name = 'allminnesota'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    # Contacts
    path('contacts/', views.contact_list, name='contact_list'),
    path('contacts/export/', views.contact_export_csv, name='contact_export'),
    path('contacts/<int:pk>/', views.contact_detail, name='contact_detail'),
    path('contacts/create/', views.contact_create, name='contact_create'),
    path('contacts/<int:pk>/edit/', views.contact_edit, name='contact_edit'),
    # Distribution Sites
    path('sites/', views.site_list, name='site_list'),
    path('sites/<int:pk>/', views.site_detail, name='site_detail'),
    path('sites/create/', views.site_create, name='site_create'),
    path('sites/<int:pk>/edit/', views.site_edit, name='site_edit'),
    # Business Plans
    path('plans/', views.plan_list, name='plan_list'),
    path('plans/<int:pk>/', views.plan_detail, name='plan_detail'),
    path('plans/create/', views.plan_create, name='plan_create'),
    path('plans/<int:pk>/edit/', views.plan_edit, name='plan_edit'),
    path('plans/<int:plan_pk>/sections/create/', views.section_create, name='section_create'),
    path('plans/<int:plan_pk>/sections/<int:pk>/edit/', views.section_edit, name='section_edit'),
    path('plans/<int:plan_pk>/sections/reorder/', views.section_reorder, name='section_reorder'),
    # KPIs
    path('kpis/', views.kpi_list, name='kpi_list'),
    path('kpis/<int:pk>/', views.kpi_detail, name='kpi_detail'),
    path('kpis/<int:pk>/update-value/', views.kpi_update_value, name='kpi_update_value'),
    # Tasks
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/board/', views.task_board, name='task_board'),
    path('tasks/<int:pk>/', views.task_detail, name='task_detail'),
    path('tasks/create/', views.task_create, name='task_create'),
    path('tasks/<int:pk>/edit/', views.task_edit, name='task_edit'),
    path('tasks/<int:pk>/delete/', views.task_delete, name='task_delete'),
    # Social Media
    path('social/', views.social_list, name='social_list'),
    path('social/calendar/', views.social_calendar, name='social_calendar'),
    path('social/<int:pk>/', views.social_detail, name='social_detail'),
    path('social/create/', views.social_create, name='social_create'),
    path('social/<int:pk>/edit/', views.social_edit, name='social_edit'),
]
