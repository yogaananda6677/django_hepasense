"""
Management command: seed data awal untuk development.

Usage:
    python manage.py seed_articles
    python manage.py seed_articles --flush  (hapus data dulu)
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.articles.models import Article, Category, Tag


CATEGORIES = [
    {'name': 'Nutrisi', 'description': 'Tips nutrisi & diet sehat', 'icon': 'apple'},
    {'name': 'Olahraga', 'description': 'Aktivitas fisik & fitness', 'icon': 'dumbbell'},
    {'name': 'Kesehatan Mental', 'description': 'Kesehatan jiwa & psikologi', 'icon': 'brain'},
    {'name': 'Penyakit Kronis', 'description': 'Diabetes, hipertensi, jantung', 'icon': 'heart-pulse'},
    {'name': 'Pencegahan', 'description': 'Vaksinasi & deteksi dini', 'icon': 'shield'},
    {'name': 'Ibu & Anak', 'description': 'Kehamilan, persalinan, parenting', 'icon': 'baby'},
]

TAGS = ['Diet', 'Vitamin', 'Cardio', 'Strength', 'Mindfulness', 'Diabetes',
        'Hipertensi', 'Jantung', 'Imunisasi', 'Bayi', 'ASI', 'Sleep']

ARTICLES = [
    {
        'title': '10 Manfaat Minum Air Putih di Pagi Hari',
        'excerpt': 'Minum air putih di pagi hari memberikan banyak manfaat untuk tubuh, mulai dari melancarkan metabolisme hingga meningkatkan konsentrasi.',
        'content': '''Air putih adalah komponen vital bagi tubuh manusia. Minum air putih di pagi hari, terutama setelah bangun tidur, memberikan berbagai manfaat:

1. **Melancarkan metabolisme** - Setelah berpuasa semalaman, tubuh membutuhkan hidrasi untuk memulai proses metabolisme.
2. **Membersihkan racun** - Air membantu ginjal membuang limbah metabolisme.
3. **Meningkatkan konsentrasi** - Otak yang terhidrasi dengan baik bekerja lebih optimal.
4. **Menjaga kesehatan kulit** - Hidrasi cukup membuat kulit lebih kenyal dan bercahaya.
5. **Memperlancar pencernaan** - Air membantu kerja sistem pencernaan.

Disarankan minum 1-2 gelas air putih (200-400ml) segera setelah bangun tidur, sebelum sarapan.
''',
        'category': 'Nutrisi',
        'tags': ['Diet', 'Vitamin'],
    },
    {
        'title': 'Cara Menjaga Kesehatan Jantung di Usia Muda',
        'excerpt': 'Penyakit jantung tidak hanya menyerang orang tua. Berikut langkah pencegahan yang bisa dilakukan sejak usia muda.',
        'content': '''Penyakit kardiovaskular adalah penyebab kematian nomor satu di dunia. Banyak yang mengira ini hanya menyerang usia tua, padahal gaya hidup muda bisa jadi penentu.

**Langkah pencegahan:**
- Rutin olahraga minimal 30 menit/hari
- Konsumsi makanan rendah lemak jenuh
- Hindari rokok dan alkohol
- Kelola stres dengan baik
- Cek kesehatan rutin

**Tanda bahaya yang perlu diwaspadai:**
- Nyeri dada
- Sesak napas saat aktivitas ringan
- Jantung berdebar tanpa sebab jelas
- Kelelahan berlebihan

Segera periksakan diri ke dokter jika mengalami gejala di atas.
''',
        'category': 'Penyakit Kronis',
        'tags': ['Jantung', 'Cardio'],
    },
    {
        'title': 'Pentingnya 2FA untuk Keamanan Data Kesehatan',
        'excerpt': 'Data kesehatan adalah data sensitif. Two-Factor Authentication (2FA) adalah lapisan keamanan penting.',
        'content': '''Data kesehatan termasuk informasi paling sensitif. Jika jatuh ke tangan yang salah, bisa digunakan untuk penipuan, diskriminasi, atau bahkan pemerasan.

**Apa itu 2FA?**
Two-Factor Authentication adalah metode keamanan yang memerlukan dua bukti identitas:
1. Sesuatu yang Anda tahu (password)
2. Sesuatu yang Anda punya (HP/authenticator app)

**Cara mengaktifkan 2FA di HepaSense:**
1. Login ke akun Anda
2. Buka menu Profile > Keamanan
3. Klik "Aktifkan 2FA"
4. Scan QR code dengan Google Authenticator atau Authy
5. Masukkan kode verifikasi
6. Simpan backup code di tempat aman

Dengan 2FA, meskipun password Anda bocor, orang lain tidak bisa masuk tanpa kode dari HP Anda.
''',
        'category': 'Pencegahan',
        'tags': ['Mindfulness'],
    },
    {
        'title': 'Panduan HIIT untuk Pemula',
        'excerpt': 'High-Intensity Interval Training (HIIT) adalah metode olahraga efektif membakar lemak dalam waktu singkat.',
        'content': '''HIIT adalah metode latihan yang交替 antara periode intensitas tinggi dan istirahat/pemulihan.

**Contoh HIIT 20 menit untuk pemula:**
- 30 detik: jumping jacks (intensitas tinggi)
- 30 detik: istirahat
- 30 detik: squat
- 30 detik: istirahat
- 30 detik: push-up
- 30 detik: istirahat
- Ulangi 4-5 ronde

**Manfaat HIIT:**
- Pembakaran kalori tinggi (afterburn effect)
- Meningkatkan VO2 max
- Efisien waktu (15-30 menit cukup)
- Tidak butuh alat

**Peringatan:**
Konsultasikan dengan dokter jika memiliki riwayat penyakit jantung sebelum memulai HIIT.
''',
        'category': 'Olahraga',
        'tags': ['Cardio', 'Strength'],
    },
    {
        'title': 'Mengelola Stres dengan Mindfulness',
        'excerpt': 'Mindfulness adalah teknik sederhana namun powerful untuk mengelola stres dan meningkatkan kualitas hidup.',
        'content': '''Mindfulness adalah praktik memperhatikan momen saat ini dengan penuh kesadaran, tanpa menghakimi.

**Latihan mindfulness 5 menit:**
1. Duduk dengan nyaman, pejamkan mata
2. Fokus pada napas masuk dan keluar
3. Saat pikiran mengembara, kembalikan fokus ke napas
4. Lakukan 5 menit setiap hari

**Manfaat jangka panjang:**
- Menurunkan kortisol (hormon stres)
- Meningkatkan fokus dan konsentrasi
- Memperbaiki kualitas tidur
- Mengurangi gejala anxiety & depresi

Mulailah dari 5 menit/hari, lalu tingkatkan secara bertahap.
''',
        'category': 'Kesehatan Mental',
        'tags': ['Mindfulness', 'Sleep'],
    },
]


class Command(BaseCommand):
    help = 'Seed data awal artikel, kategori, dan tag untuk HepaSense'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Hapus semua data artikel/kategori/tag sebelum seed',
        )

    def handle(self, *args, **options):
        if options['flush']:
            self.stdout.write(self.style.WARNING('Menghapus data lama...'))
            Article.objects.all().delete()
            Category.objects.all().delete()
            Tag.objects.all().delete()

        # Categories
        self.stdout.write('Membuat kategori...')
        categories = {}
        for cat_data in CATEGORIES:
            cat, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'description': cat_data['description'],
                    'icon': cat_data['icon'],
                },
            )
            categories[cat.name] = cat
            status_msg = '✓' if created else '→'
            self.stdout.write(f'  {status_msg} {cat.name}')

        # Tags
        self.stdout.write('Membuat tag...')
        tags = {}
        for tag_name in TAGS:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            tags[tag_name] = tag

        # Articles
        self.stdout.write('Membuat artikel...')
        for art_data in ARTICLES:
            cat = categories.get(art_data.pop('category'))
            article_tags = art_data.pop('tags', [])

            article, created = Article.objects.get_or_create(
                title=art_data['title'],
                defaults={
                    **art_data,
                    'category': cat,
                    'status': 'published',
                    'published_at': timezone.now(),
                },
            )
            if article_tags:
                article.tags.set([tags[t] for t in article_tags if t in tags])

            status_msg = '✓' if created else '→'
            self.stdout.write(f'  {status_msg} {article.title}')

        self.stdout.write(self.style.SUCCESS(
            f'\nSelesai! Total: {Category.objects.count()} kategori, '
            f'{Tag.objects.count()} tag, {Article.objects.count()} artikel.'
        ))