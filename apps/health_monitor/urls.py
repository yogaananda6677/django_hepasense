"""URL routing for health monitor app."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.health_monitor.views import (
    SensorReadingViewSet,
    VitalSignViewSet,
    HealthAlertViewSet,
    DashboardSummaryView,
)

app_name = 'health_monitor'

router = DefaultRouter()
router.register(r'sensors', SensorReadingViewSet, basename='sensor')
router.register(r'vitals', VitalSignViewSet, basename='vital')
router.register(r'alerts', HealthAlertViewSet, basename='alert')

urlpatterns = [
    path('', include(router.urls)),
    path('dashboard/', DashboardSummaryView.as_view(), name='dashboard'),
]