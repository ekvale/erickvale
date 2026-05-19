from django.urls import path

from . import views

app_name = 'mdh_briefings'

urlpatterns = [
    path('', views.dashboard, name='mdh_dashboard'),
    path('generate/<str:leader_id>/', views.generate_briefing, name='mdh_generate_briefing'),
    path('generate-all/', views.generate_all, name='mdh_generate_all'),
]
