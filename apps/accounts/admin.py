from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from apps.accounts.models import User, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profil'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ['-created_at']
    list_display = ['email', 'first_name', 'last_name', 'is_patient',
                    'is_doctor', 'two_factor_enabled', 'is_active', 'created_at']
    list_filter = ['is_active', 'is_staff', 'is_patient', 'is_doctor',
                   'two_factor_enabled', 'gender']
    search_fields = ['email', 'first_name', 'last_name', 'phone_number']

    # Tambahkan fieldsets custom (no username)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informasi Pribadi', {'fields': ('first_name', 'last_name',
                                          'phone_number', 'date_of_birth',
                                          'gender', 'avatar')}),
        ('Role & Status', {'fields': ('is_patient', 'is_doctor',
                                       'two_factor_enabled')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser',
                                      'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined',
                                         'created_at', 'updated_at')}),
    )
    readonly_fields = ['created_at', 'updated_at', 'last_login', 'date_joined']
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )
    inlines = [UserProfileInline]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'city', 'province', 'preferred_language']
    search_fields = ['user__email', 'city', 'province']