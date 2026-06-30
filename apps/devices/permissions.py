"""Custom permissions for devices app."""

from rest_framework import permissions


class IsDeviceOwner(permissions.BasePermission):
    """Hanya owner device yang boleh akses."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user