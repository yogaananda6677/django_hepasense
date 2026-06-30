"""
Serializers for accounts app.
"""

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import UserProfile

User = get_user_model()


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer untuk UserProfile."""

    class Meta:
        model = UserProfile
        fields = [
            'id', 'address', 'city', 'province', 'postal_code',
            'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relation', 'preferred_language',
            'notification_preferences',
        ]
        read_only_fields = ['id']


class UserSerializer(serializers.ModelSerializer):
    """Serializer untuk User (read & basic update)."""
    profile = UserProfileSerializer(read_only=True)
    age = serializers.IntegerField(read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'phone_number', 'date_of_birth', 'gender', 'avatar',
            'is_patient', 'is_doctor', 'two_factor_enabled',
            'age', 'profile', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'email', 'two_factor_enabled',
                            'is_patient', 'is_doctor', 'created_at', 'updated_at']


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer untuk registrasi user baru."""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
    )

    class Meta:
        model = User
        fields = [
            'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone_number',
            'date_of_birth', 'gender',
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Password tidak cocok.'
            })
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm', None)
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer untuk login (email + password)."""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password,
            )
            if not user:
                raise serializers.ValidationError(
                    'Email atau password salah.',
                    code='authorization',
                )
            if not user.is_active:
                raise serializers.ValidationError(
                    'Akun nonaktif.',
                    code='authorization',
                )
        else:
            raise serializers.ValidationError(
                'Email dan password wajib diisi.',
                code='authorization',
            )

        attrs['user'] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer untuk ubah password."""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
    )
    new_password_confirm = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs['old_password']):
            raise serializers.ValidationError({
                'old_password': 'Password lama salah.'
            })
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Password baru tidak cocok.'
            })
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    """Request reset password - kirim email berisi token."""
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email tidak terdaftar.')
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Konfirmasi reset password dengan token."""
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
    )


class TwoFactorSetupSerializer(serializers.Serializer):
    """Serializer untuk setup 2FA - return QR code data."""
    pass


class TwoFactorVerifySerializer(serializers.Serializer):
    """Serializer untuk verify 2FA code."""
    otp_code = serializers.CharField(required=True, max_length=6, min_length=6)


def get_tokens_for_user(user):
    """Helper: generate JWT tokens untuk user."""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }