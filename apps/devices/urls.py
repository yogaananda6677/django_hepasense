"""URL routing for devices app."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.devices.views import DeviceViewSet, DeviceDataSyncView

app_name = 'devices'

router = DefaultRouter()
router.register(r'', DeviceViewSet, basename='device')

urlpatterns = [
    # Sync endpoint HARUS di atas router (avoid conflict dengan detail)
    path('sync-data/', DeviceDataSyncView.as_view({'post': 'create'}),
         name='sync-data'),
    path('', include(router.urls)),
]