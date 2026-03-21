from django.urls import path
from . import views

app_name = 'nomoar'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('Timeline/', views.TimelineView.as_view(), name='timeline'),
    path('Map/', views.MapView.as_view(), name='map'),
    path('EventDetail/<slug:slug>/', views.EventDetailView.as_view(), name='event_detail'),
    path('Submit/', views.submit_event, name='submit'),
    path('Educators/', views.EducatorsView.as_view(), name='educators'),
    path('Pricing/', views.PricingView.as_view(), name='pricing'),
]
