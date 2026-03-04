from django.urls import path
from . import views

app_name = 'chess_trainer'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('opening/<int:pk>/', views.OpeningDetailView.as_view(), name='opening_detail'),
    path('lesson/<int:pk>/', views.LessonView.as_view(), name='lesson'),
    path('lesson/<int:pk>/submit/', views.LessonSubmitView.as_view(), name='lesson_submit'),
    path('lesson/<int:pk>/quiz/', views.QuizView.as_view(), name='quiz'),
    path('lesson/<int:pk>/drill/', views.DrillView.as_view(), name='drill'),
]
