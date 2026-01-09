from django.urls import path
from . import views

app_name = 'personality_type_game'

urlpatterns = [
    path('', views.game_home, name='home'),
    path('play/', views.play_game, name='play'),
    path('play/<str:session_id>/', views.play_game, name='play_session'),
    path('api/start/', views.start_game, name='start_game'),
    path('api/session/<str:session_id>/scenario/', views.get_scenario, name='get_scenario'),
    path('api/session/<str:session_id>/round/<int:round_id>/answer/', views.submit_answer, name='submit_answer'),
    path('api/session/<str:session_id>/round/<int:round_id>/hint/', views.get_hint, name='get_hint'),
    path('summary/<str:session_id>/', views.game_summary, name='summary'),
]

