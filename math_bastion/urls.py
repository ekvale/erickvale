from django.urls import path

from . import views

app_name = 'math_bastion'

urlpatterns = [
    path('', views.play, name='play'),
    path('api/leaderboard/', views.leaderboard, name='leaderboard'),
    path('api/score/', views.submit_score, name='submit_score'),
    path('api/store/', views.store_catalog, name='store_catalog'),
    path('api/wallet/', views.wallet_sync, name='wallet_sync'),
    path('api/purchase/', views.purchase_intent, name='purchase_intent'),
]
