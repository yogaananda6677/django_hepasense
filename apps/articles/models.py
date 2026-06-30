"""Models for articles app."""

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Category(models.Model):
    """Kategori artikel kesehatan."""
    name = models.CharField('Nama', max_length=100, unique=True)
    slug = models.SlugField('Slug', max_length=120, unique=True, blank=True)
    description = models.TextField('Deskripsi', blank=True)
    icon = models.CharField('Icon', max_length=50, blank=True,
                             help_text='Nama icon (mis. heart, brain)')
    is_active = models.BooleanField('Aktif', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'article_categories'
        verbose_name = 'Kategori'
        verbose_name_plural = 'Kategori'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Tag(models.Model):
    """Tag untuk artikel."""
    name = models.CharField('Nama', max_length=50, unique=True)
    slug = models.SlugField('Slug', max_length=60, unique=True, blank=True)

    class Meta:
        db_table = 'article_tags'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Article(models.Model):
    """Artikel kesehatan."""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    title = models.CharField('Judul', max_length=255)
    slug = models.SlugField('Slug', max_length=280, unique=True, blank=True)
    excerpt = models.TextField('Ringkasan', max_length=500, blank=True)
    content = models.TextField('Konten')
    featured_image = models.ImageField(
        'Gambar Utama',
        upload_to='articles/',
        blank=True,
        null=True,
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name='articles',
        verbose_name='Kategori',
        null=True,
        blank=True,
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='articles',
        verbose_name='Tag',
        blank=True,
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='articles',
        verbose_name='Author',
        null=True,
        blank=True,
    )

    status = models.CharField(
        'Status',
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft',
    )

    # Stats
    view_count = models.PositiveIntegerField('Jumlah View', default=0)
    read_time_minutes = models.PositiveIntegerField('Estimasi Baca (menit)', default=5)

    # SEO
    meta_title = models.CharField('Meta Title', max_length=255, blank=True)
    meta_description = models.TextField('Meta Description', blank=True)

    published_at = models.DateTimeField('Dipublikasikan', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'articles'
        verbose_name = 'Artikel'
        verbose_name_plural = 'Artikel'
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['status', '-published_at']),
            models.Index(fields=['slug']),
            models.Index(fields=['category', '-published_at']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Article.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()

        # Estimate read time
        if self.content:
            word_count = len(self.content.split())
            self.read_time_minutes = max(1, round(word_count / 200))

        super().save(*args, **kwargs)


class Bookmark(models.Model):
    """Bookmark artikel oleh user."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookmarks',
        verbose_name='User',
    )
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='bookmarks',
        verbose_name='Artikel',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'article_bookmarks'
        unique_together = ['user', 'article']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.article.title}"