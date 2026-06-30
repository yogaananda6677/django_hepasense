"""
Views for accounts app.

Includes:
- RegisterView          : POST /api/v1/auth/register/
- LoginView             : POST /api/v1/auth/login/
- LogoutView            : POST /api/v1/auth/logout/
- ProfileView           : GET/PUT/PATCH /api/v1/accounts/profile/
- ChangePasswordView    : POST /api/v1/accounts/change-password/
- PasswordResetRequest  : POST /api/v1/auth/password/reset/
- PasswordResetConfirm  : POST /api/v1/auth/password/reset/confirm/
- TwoFactorSetupView    : POST /api/v1/accounts/2fa/setup/
- TwoFactorVerifyView   : POST /api/v1/accounts/2fa/verify/
- TwoFactorDisableView  : POST /api/v1/accounts/2fa/disable/
"""

import io
import base64

import qrcode
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from django_otp import DEVICE_ID_SESSION_KEY
from django_otp.oath import TOTP
from django_otp.plugins.otp_totp.models import TOTPDevice
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsOwnerOrReadOnly
from apps.accounts.serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    TwoFactorVerifySerializer,
    get_tokens_for_user,
)

User = get_user_model()


# =============================================================================
# Register & Login
# =============================================================================

class RegisterView(generics.CreateAPIView):
    """POST /api/v1/auth/register/ — daftar akun baru."""
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = get_tokens_for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': tokens,
            'message': 'Registrasi berhasil. Selamat datang di HepaSense!',
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """POST /api/v1/auth/login/ — login pakai email & password."""
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        tokens = get_tokens_for_user(user)

        requires_2fa = user.two_factor_enabled

        return Response({
            'user': UserSerializer(user).data,
            'tokens': tokens,
            'requires_2fa': requires_2fa,
            'message': 'Login berhasil.' if not requires_2fa else
                       'Login berhasil. Verifikasi 2FA diperlukan.',
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """POST /api/v1/auth/logout/ — blacklist refresh token."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({
                    'error': 'Refresh token wajib diisi.'
                }, status=status.HTTP_400_BAD_REQUEST)

            from rest_framework_simplejwt.tokens import RefreshToken
            from rest_framework_simplejwt.exceptions import TokenError

            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logout berhasil.'},
                            status=status.HTTP_205_RESET_CONTENT)
        except TokenError as e:
            return Response({'error': str(e)},
                            status=status.HTTP_400_BAD_REQUEST)


# =============================================================================
# Profile
# =============================================================================

class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/v1/accounts/profile/   — lihat profil sendiri
    PUT   /api/v1/accounts/profile/   — update profil
    PATCH /api/v1/accounts/profile/   — partial update
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    """POST /api/v1/accounts/change-password/ — ubah password saat login."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({
            'message': 'Password berhasil diubah. Silakan login ulang.'
        }, status=status.HTTP_200_OK)


# =============================================================================
# Password Reset
# =============================================================================

class PasswordResetRequestView(APIView):
    """POST /api/v1/auth/password/reset/ — request token via email."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        # Generate token sederhana (UUID stored in cache)
        import secrets
        token = secrets.token_urlsafe(32)
        cache.set(f'pwd_reset_{token}', email, timeout=3600)  # 1 jam

        # Di production, kirim token via email
        # Untuk development, tampilkan di response (console)
        from django.conf import settings
        if settings.DEBUG:
            return Response({
                'message': 'Token reset password telah di-generate.',
                'token': token,  # Hanya di DEBUG
                'note': 'Di production, token dikirim via email.',
            }, status=status.HTTP_200_OK)

        return Response({
            'message': 'Instruksi reset password telah dikirim ke email Anda.'
        }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """POST /api/v1/auth/password/reset/confirm/ — set password baru."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        email = cache.get(f'pwd_reset_{token}')
        if not email:
            return Response({
                'error': 'Token tidak valid atau sudah kadaluarsa.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()
            cache.delete(f'pwd_reset_{token}')
            return Response({
                'message': 'Password berhasil direset. Silakan login.'
            }, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({
                'error': 'User tidak ditemukan.'
            }, status=status.HTTP_404_NOT_FOUND)


# =============================================================================
# 2FA (TOTP) - Endpoints
# =============================================================================

class TwoFactorSetupView(APIView):
    """
    POST /api/v1/accounts/2fa/setup/

    Generate TOTP secret + QR code untuk user.
    Belum aktif sampai user verify kode pertama.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Hapus device lama kalau ada (untuk re-setup)
        TOTPDevice.objects.filter(user=user).delete()

        device = TOTPDevice.objects.create(
            user=user,
            name='default',
            confirmed=False,
        )

        # Build otpauth URL untuk QR code
        otpauth_url = device.config_url

        # Generate QR code (PNG -> base64)
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(otpauth_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')

        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        return Response({
            'secret': device.key,
            'otpauth_url': otpauth_url,
            'qr_code_base64': qr_base64,
            'message': 'Scan QR code dengan Google Authenticator / Authy, '
                       'lalu verify kode untuk mengaktifkan 2FA.',
        }, status=status.HTTP_200_OK)


class TwoFactorVerifyView(APIView):
    """
    POST /api/v1/accounts/2fa/verify/

    Verify kode TOTP dan aktifkan 2FA (saat setup).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = TwoFactorVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        otp_code = serializer.validated_data['otp_code']

        user = request.user
        device = TOTPDevice.objects.filter(user=user, confirmed=False).first()

        if not device:
            return Response({
                'error': 'Tidak ada setup 2FA yang pending. Mulai setup terlebih dahulu.'
            }, status=status.HTTP_400_BAD_REQUEST)

        if device.verify_token(otp_code):
            device.confirmed = True
            device.save()
            user.two_factor_enabled = True
            user.save()

            return Response({
                'message': '2FA berhasil diaktifkan.',
                'two_factor_enabled': True,
            }, status=status.HTTP_200_OK)

        return Response({
            'error': 'Kode OTP salah atau kadaluarsa.'
        }, status=status.HTTP_400_BAD_REQUEST)


class TwoFactorDisableView(APIView):
    """
    POST /api/v1/accounts/2fa/disable/
    {
        "password": "current_password"
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        password = request.data.get('password')
        if not password:
            return Response({'error': 'Password wajib diisi untuk menonaktifkan 2FA.'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if not user.check_password(password):
            return Response({'error': 'Password salah.'},
                            status=status.HTTP_400_BAD_REQUEST)

        TOTPDevice.objects.filter(user=user).delete()
        user.two_factor_enabled = False
        user.save()

        return Response({
            'message': '2FA berhasil dinonaktifkan.',
            'two_factor_enabled': False,
        }, status=status.HTTP_200_OK)


class TwoFactorLoginView(APIView):
    """
    POST /api/v1/auth/2fa/login/
    {
        "email": "user@example.com",
        "otp_code": "123456"
    }

    Step ke-2 dari login flow: setelah dapat temporary token, user verify OTP
    untuk dapat token JWT penuh.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        otp_code = request.data.get('otp_code')

        if not email or not otp_code:
            return Response({'error': 'Email dan OTP wajib diisi.'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User tidak ditemukan.'},
                            status=status.HTTP_404_NOT_FOUND)

        device = TOTPDevice.objects.filter(user=user, confirmed=True).first()
        if not device:
            return Response({'error': '2FA tidak aktif untuk akun ini.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if device.verify_token(otp_code):
            tokens = get_tokens_for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'tokens': tokens,
                'message': 'Login berhasil.',
            }, status=status.HTTP_200_OK)

        return Response({'error': 'Kode OTP salah.'},
                        status=status.HTTP_400_BAD_REQUEST)