from django.urls import path

from . import views

app_name = 'braindump'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('capture/', views.capture_create, name='capture_create'),
    path('item/<int:pk>/status/', views.item_status, name='item_status'),
    path('item/<int:pk>/calendar/', views.item_calendar_date, name='item_calendar_date'),
    path('item/<int:pk>/meta/', views.item_update_meta, name='item_update_meta'),
    path('item/<int:pk>/archive/', views.item_archive, name='item_archive'),
    path('item/<int:pk>/recategorize/', views.recategorize, name='recategorize'),
]
