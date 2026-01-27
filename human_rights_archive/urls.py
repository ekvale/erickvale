from django.urls import path
from . import views

app_name = 'human_rights_archive'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('articles/', views.article_list, name='article_list'),
    path('articles/<int:pk>/', views.article_detail, name='article_detail'),
    path('sources/', views.source_list, name='source_list'),
    path('tags/', views.tag_list, name='tag_list'),
    path('add-by-url/', views.add_by_url, name='add_by_url'),
    path('export/csv/', views.export_csv, name='export_csv'),
    path('about/', views.about, name='about'),
]
