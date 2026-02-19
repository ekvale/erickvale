from django.urls import path
from . import views

app_name = 'arm_chair_detective'

urlpatterns = [
    path('', views.case_list, name='case_list'),
    path('case/<int:pk>/', views.case_play, name='case_play'),
    path('case/<int:pk>/filter/', views.apply_filter, name='apply_filter'),
    path('case/<int:pk>/guess/', views.submit_guess, name='submit_guess'),
    path('case/<int:pk>/reset/', views.reset_case, name='reset_case'),
    path('api/case/<int:pk>/suspect-count/', views.suspect_count_api, name='suspect_count_api'),
]
