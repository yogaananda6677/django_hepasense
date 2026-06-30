"""
Auth-specific URLs (login, register, password reset, token).
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.views import (
    RegisterView,
    LoginView,
    LogoutView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    TwoFactorLoginView,
)

app_name = 'accounts-auth'

urlpatterns = [
    # JWT token obtain
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),

    # Register / Login / Logout
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Password reset
    path('password/reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),

    # 2FA login verification
    path('2fa/login/', TwoFactorLoginView.as_view(), name='2fa-login'),
]