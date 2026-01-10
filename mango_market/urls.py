from django.urls import path
from . import views

app_name = 'mango_market'

urlpatterns = [
    path('', views.index, name='index'),
    path('results/', views.results, name='results'),
    path('results/<int:simulation_id>/', views.simulation_detail, name='simulation_detail'),
    path('api/simulation/', views.api_simulation_data, name='api_simulation'),
]
