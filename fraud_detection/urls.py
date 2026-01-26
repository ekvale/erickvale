from django.urls import path
from . import views

app_name = 'fraud_detection'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('import/', views.import_data, name='import'),
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/<int:pk>/', views.transaction_detail, name='transaction_detail'),
    path('flags/', views.fraud_flag_list, name='fraud_flag_list'),
    path('flags/<int:pk>/', views.fraud_flag_detail, name='flag_detail'),
    path('vendors/', views.vendor_list, name='vendor_list'),
    path('vendors/<int:pk>/', views.vendor_detail, name='vendor_detail'),
    path('run-analysis/', views.run_analysis, name='run_analysis'),
    path('api/dashboard/', views.dashboard_api, name='dashboard_api'),
]
