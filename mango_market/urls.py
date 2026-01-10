from django.urls import path
from . import views

app_name = 'mango_market'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/simulation/', views.api_simulation_data, name='api_simulation'),
]
