"""
URL Configuration for HepaSense Backend.

API endpoints follow RESTful conventions under /api/v1/
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from django.http import JsonResponse


def health_check(request):
    """Simple health check endpoint for Docker/Kubernetes probes."""
    return JsonResponse({
        'status': 'healthy',
        'service': 'hepasense-backend',
        'version': '0.1.0',
    })


urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Health check
    path('health/', health_check, name='health-check'),

    # API v1
    path('api/v1/', include([
        # Authentication
        path('auth/', include('apps.accounts.urls.auth_urls')),

        # Accounts / Profile / 2FA
        path('accounts/', include('apps.accounts.urls')),

        # Health monitoring (NH3, suhu, kelembapan, dll)
        path('health-monitor/', include('apps.health_monitor.urls')),

        # Articles
        path('articles/', include('apps.articles.urls')),

        # Wearable Devices
        path('devices/', include('apps.devices.urls')),
    ])),

    # JWT token refresh
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customize admin header
admin.site.site_header = 'HepaSense Administration'
admin.site.site_title = 'HepaSense Admin'
admin.site.index_title = 'Welcome to HepaSense'