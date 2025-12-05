from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PODViewSet, ScenarioViewSet, DemographicDataView,
    RiskDataView, DriveTimeView
)
from . import views

router = DefaultRouter()
router.register(r'pods', PODViewSet, basename='pod')
router.register(r'scenarios', ScenarioViewSet, basename='scenario')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/demographic-data/', DemographicDataView.as_view(), name='demographic-data'),
    path('api/risk-data/', RiskDataView.as_view(), name='risk-data'),
    path('api/drive-time/', DriveTimeView.as_view(), name='drive-time'),
    path('', views.index, name='emergency-index'),
]

