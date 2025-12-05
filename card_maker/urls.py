from django.urls import path
from . import views

app_name = 'card_maker'

urlpatterns = [
    path('', views.index, name='index'),
    path('sets/', views.CardSetListView.as_view(), name='set_list'),
    path('sets/<slug:slug>/', views.CardSetDetailView.as_view(), name='set_detail'),
    path('sets/<slug:set_slug>/cards/<slug:card_slug>/', views.CardDetailView.as_view(), name='card_detail'),
]



