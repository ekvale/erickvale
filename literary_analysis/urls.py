"""
URL configuration for literary_analysis app.
"""
from django.urls import path
from . import views

app_name = 'literary_analysis'

urlpatterns = [
    path('', views.index, name='index'),
    path('works/', views.LiteraryWorkListView.as_view(), name='work_list'),
    path('works/upload/', views.upload_work, name='upload_work'),
    path('works/<int:pk>/', views.LiteraryWorkDetailView.as_view(), name='work_detail'),
    path('codebooks/', views.CodebookListView.as_view(), name='codebook_list'),
    path('codebooks/<int:pk>/', views.CodebookDetailView.as_view(), name='codebook_detail'),
    path('analyses/', views.AnalysisListView.as_view(), name='analysis_list'),
    path('analyses/create/', views.create_analysis, name='create_analysis'),
    path('analyses/<int:pk>/', views.AnalysisDetailView.as_view(), name='analysis_detail'),
    path('analyses/<int:pk>/code/', views.coding_interface, name='coding_interface'),
    path('analyses/<int:pk>/dashboard/', views.analysis_dashboard, name='analysis_dashboard'),
    path('analyses/<int:pk>/generate-report/', views.generate_report, name='generate_report'),
    path('analyses/<int:pk>/report/', views.view_report, name='view_report'),
    path('api/segments/', views.create_segment, name='api_create_segment'),
    path('api/segments/<int:pk>/', views.update_segment, name='api_update_segment'),
    path('api/segments/<int:pk>/delete/', views.delete_segment, name='api_delete_segment'),
]

