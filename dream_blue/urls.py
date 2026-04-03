from django.urls import path

from . import views

app_name = 'dream_blue'

urlpatterns = [
    path(
        'grantscout/',
        views.grantscout_dashboard,
        name='grantscout_dashboard',
    ),
    path(
        'api/grantscout/latest.json',
        views.grantscout_latest_api,
        name='grantscout_latest_api',
    ),
]
