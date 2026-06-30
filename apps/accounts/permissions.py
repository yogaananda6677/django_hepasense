"""
Custom permissions for accounts app.
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission: hanya owner yang boleh edit.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj == request.user or obj.user == request.user


class IsDoctor(permissions.BasePermission):
    """Hanya untuk user dengan role dokter."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_doctor)


class IsVerified2FA(permissions.BasePermission):
    """User yang 2FA nya aktif harus sudah verify OTP."""

    message = '2FA verification required.'

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        # Kalau 2FA aktif, harus sudah verified via OTPMiddleware
        if user.two_factor_enabled:
            return getattr(user, 'is_verified', lambda: False)() if hasattr(user, 'is_verified') else True
        return True