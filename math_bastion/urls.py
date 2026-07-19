from django.urls import path

from . import views

app_name = 'math_bastion'

urlpatterns = [
    path('', views.play, name='play'),
    path('api/leaderboard/', views.leaderboard, name='leaderboard'),
    path('api/score/', views.submit_score, name='submit_score'),
]
