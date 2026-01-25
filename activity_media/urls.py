from django.urls import path
from . import views

app_name = 'activity_media'

urlpatterns = [
    path('', views.media_list, name='list'),
    path('upload/', views.upload_media, name='upload'),
    path('map/', views.media_map, name='map'),
    path('api/', views.media_api, name='api'),
    path('<int:pk>/', views.media_detail, name='detail'),
]
