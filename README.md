# HepaSense Backend

Backend API untuk platform kesehatan **HepaSense** — monitoring kesehatan (NH3, suhu, kelembapan), artikel kesehatan, integrasi wearable, dan 2FA authentication.

Dibangun dengan **Django 5.x + Django REST Framework + JWT + PostgreSQL**.

---

## 🎯 Fitur Utama

| Fitur | Endpoint |
|-------|----------|
| 🔐 JWT Auth (Register/Login/Logout) | `/api/v1/auth/` |
| 👤 Profil & ubah password | `/api/v1/accounts/` |
| 🔒 2FA (TOTP + QR Code) | `/api/v1/accounts/2fa/` |
| 📊 Dashboard monitoring | `/api/v1/health-monitor/dashboard/` |
| 🌡️ Sensor readings (NH3, suhu, kelembapan) | `/api/v1/health-monitor/sensors/` |
| ❤️ Vital signs (heart rate, BP, SpO2, dll) | `/api/v1/health-monitor/vitals/` |
| 🚨 Health alerts | `/api/v1/health-monitor/alerts/` |
| 📰 Artikel kesehatan + bookmark | `/api/v1/articles/` |
| ⌚ Wearable device pairing | `/api/v1/devices/` |

---

## 🚀 Quick Start (Docker)

### Prasyarat
- Docker & Docker Compose
- (Opsional) `uv` untuk development lokal

### 1. Clone & Setup
```bash
cd hepasense/backend
cp .env.example .env
# Edit .env sesuai kebutuhan (opsional untuk dev)
```

### 2. Jalankan
```bash
docker-compose up --build
```

Backend akan tersedia di: **http://localhost:8080**
Admin: **http://localhost:8080/admin/**

Setelah jalan, otomatis:
- ✅ Migrasi database
- ✅ Seed 6 kategori, 12 tag, 5 artikel

### 3. Buat Superuser
```bash
docker-compose exec web python manage.py createsuperuser
```

### 4. Seed Demo Data (opsional)
```bash
docker-compose exec web python manage.py seed_demo_data
# User demo: demo@hepasense.com / demo123456
```

---

## 💻 Development Lokal (tanpa Docker)

### Prasyarat
- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (recommended) atau pip
- PostgreSQL 17+ (atau pakai SQLite untuk coba-coba)

### Setup
```bash
# Install uv (kalau belum)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Copy .env
cp .env.example .env
# Edit DATABASE_* ke SQLite atau PostgreSQL lokal

# Jalankan migrasi
uv run python manage.py migrate

# Seed data awal
uv run python manage.py seed_articles

# Jalankan server
uv run python manage.py runserver
```

Backend di: **http://localhost:8000**

---

## 📚 API Dokumentasi

### Base URL
```
http://localhost:8080/api/v1/
```

### Autentikasi
Semua endpoint (kecuali register/login/2fa-verify) butuh JWT token:
```
Authorization: Bearer <access_token>
```

Dapatkan token via:
```bash
curl -X POST http://localhost:8080/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

Response:
```json
{
  "user": {...},
  "tokens": {
    "access": "eyJ...",
    "refresh": "eyJ..."
  },
  "requires_2fa": false
}
```

### Contoh: Get Dashboard
```bash
curl http://localhost:8080/api/v1/health-monitor/dashboard/ \
  -H "Authorization: Bearer <access_token>"
```

### Contoh: Tambah Sensor Reading
```bash
curl -X POST http://localhost:8080/api/v1/health-monitor/sensors/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_type": "nh3",
    "value": 18.5,
    "unit": "ppm",
    "location": "Ruang Tidur"
  }'
```

Lihat daftar lengkap endpoint di bagian **API Reference** di bawah.

---

## 📁 Struktur Project

```
hepasense/
├── config/              # Django project config
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── accounts/        # User, Profile, 2FA, Auth
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── admin.py
│   ├── health_monitor/  # Sensor, Vital Signs, Alerts
│   ├── articles/        # Articles, Categories, Bookmarks
│   └── devices/         # Wearable Device Integration
├── media/               # User uploads
├── static/              # Static files
├── logs/                # Application logs
├── .env                 # Environment config (NOT in git)
├── manage.py
├── pyproject.toml
├── docker-compose.yml
└── README.md
```

---

## 🔐 2FA (Two-Factor Authentication)

Alur setup:
1. User login → dapat JWT token
2. `POST /api/v1/accounts/2fa/setup/` → dapat `secret` + `qr_code_base64`
3. User scan QR dengan Google Authenticator / Authy
4. `POST /api/v1/accounts/2fa/verify/` dengan `{"otp_code": "123456"}`
5. ✅ 2FA aktif

Login flow dengan 2FA:
1. `POST /api/v1/auth/login/` → response `requires_2fa: true`
2. `POST /api/v1/auth/2fa/login/` dengan `{"email": "...", "otp_code": "123456"}`
3. ✅ Dapat JWT token penuh

---

## 🔌 Device Integration (Wearable)

Setiap device punya `device_token` unik untuk push data:

```bash
curl -X POST http://localhost:8080/api/v1/devices/sync-data/ \
  -H "Content-Type: application/json" \
  -d '{
    "device_token": "abc123...",
    "records": [
      {
        "heart_rate": 72,
        "blood_pressure_systolic": 120,
        "blood_pressure_diastolic": 80,
        "oxygen_saturation": 98,
        "body_temperature": 36.6,
        "recorded_at": "2026-06-30T10:00:00Z"
      }
    ]
  }'
```

User bisa regenerate token via `POST /api/v1/devices/{id}/regenerate_token/`.

---

## 📖 API Reference (Ringkasan)

### Auth
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| POST | `/api/v1/auth/register/` | Daftar akun baru |
| POST | `/api/v1/auth/login/` | Login |
| POST | `/api/v1/auth/logout/` | Logout (blacklist token) |
| POST | `/api/v1/auth/token/` | JWT obtain (SimpleJWT) |
| POST | `/api/v1/auth/token/refresh/` | JWT refresh |
| POST | `/api/v1/auth/password/reset/` | Request reset password |
| POST | `/api/v1/auth/password/reset/confirm/` | Confirm reset password |
| POST | `/api/v1/auth/2fa/login/` | Verify OTP saat login |

### Accounts
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET/PUT/PATCH | `/api/v1/accounts/profile/` | Lihat/update profil |
| POST | `/api/v1/accounts/change-password/` | Ubah password |
| POST | `/api/v1/accounts/2fa/setup/` | Setup 2FA (return QR) |
| POST | `/api/v1/accounts/2fa/verify/` | Verify & aktifkan 2FA |
| POST | `/api/v1/accounts/2fa/disable/` | Disable 2FA |

### Health Monitor
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET | `/api/v1/health-monitor/dashboard/` | Dashboard summary |
| GET/POST | `/api/v1/health-monitor/sensors/` | List/create sensor readings |
| GET/PUT/PATCH/DELETE | `/api/v1/health-monitor/sensors/{id}/` | Sensor detail |
| GET/POST | `/api/v1/health-monitor/vitals/` | List/create vital signs |
| GET | `/api/v1/health-monitor/vitals/latest/` | Latest vital sign |
| GET | `/api/v1/health-monitor/alerts/` | List alerts |
| POST | `/api/v1/health-monitor/alerts/{id}/mark_read/` | Tandai dibaca |
| POST | `/api/v1/health-monitor/alerts/{id}/mark_resolved/` | Tandai selesai |
| GET | `/api/v1/health-monitor/alerts/unread_count/` | Hitung unread |

### Articles
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET/POST | `/api/v1/articles/articles/` | List/create artikel |
| GET | `/api/v1/articles/articles/{slug}/` | Detail artikel |
| GET | `/api/v1/articles/articles/popular/` | Top 10 populer |
| GET | `/api/v1/articles/articles/recent/` | 10 terbaru |
| GET | `/api/v1/articles/articles/my_articles/` | Artikel user |
| GET | `/api/v1/articles/categories/` | List kategori |
| GET | `/api/v1/articles/tags/` | List tag |
| GET/POST | `/api/v1/articles/bookmarks/` | List/create bookmark |

### Devices
| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET/POST | `/api/v1/devices/` | List/pair devices |
| GET/PATCH/DELETE | `/api/v1/devices/{id}/` | Device detail |
| POST | `/api/v1/devices/{id}/sync/` | Manual sync |
| POST | `/api/v1/devices/{id}/regenerate_token/` | Token baru |
| GET | `/api/v1/devices/{id}/sync_logs/` | History sync |
| POST | `/api/v1/devices/sync-data/` | Device push data |

---

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# With coverage
uv run pytest --cov=apps
```

---

## 🛠️ Tech Stack

- **Django 5.1** - Web framework
- **Django REST Framework 3.15** - REST API
- **SimpleJWT** - JWT authentication
- **django-otp** - 2FA (TOTP)
- **PostgreSQL 17** - Database
- **django-filter** - Filtering
- **django-cors-headers** - CORS
- **Pillow** - Image handling
- **uv** - Fast Python package manager

---

## 🔒 Security

- ✅ Custom user model (email as username)
- ✅ JWT dengan refresh token rotation & blacklist
- ✅ 2FA (TOTP via Google Authenticator)
- ✅ Password validation (min 8, common, numeric)
- ✅ CORS configured
- ✅ HTTPS-ready (HSTS, secure cookies di production)
- ✅ Rate limiting (100/hour anon, 1000/hour user)
- ✅ Threshold-based alert system

---

## 📜 License

MIT — HepaSense © 2026

---

## 🤝 Kontribusi

1. Fork
2. Buat branch (`git checkout -b feature/AmazingFeature`)
3. Commit (`git commit -m 'Add some AmazingFeature'`)
4. Push (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

**HepaSense** — *Your Health, Our Priority* 🏥