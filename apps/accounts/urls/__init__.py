"""
URL routing for accounts app.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.accounts.views import (
    RegisterView,
    LoginView,
    LogoutView,
    ProfileView,
    ChangePasswordView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    TwoFactorSetupView,
    TwoFactorVerifyView,
    TwoFactorDisableView,
    TwoFactorLoginView,
)

app_name = 'accounts'

urlpatterns = [
    # Profile
    path('profile/', ProfileView.as_view(), name='profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),

    # 2FA endpoints
    path('2fa/setup/', TwoFactorSetupView.as_view(), name='2fa-setup'),
    path('2fa/verify/', TwoFactorVerifyView.as_view(), name='2fa-verify'),
    path('2fa/disable/', TwoFactorDisableView.as_view(), name='2fa-disable'),
]