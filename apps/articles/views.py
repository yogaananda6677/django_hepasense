"""Views for articles app."""

from django.db.models import Q
from rest_framework import viewsets, status, filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.articles.models import Article, Category, Tag, Bookmark
from apps.articles.serializers import (
    ArticleListSerializer,
    ArticleDetailSerializer,
    ArticleWriteSerializer,
    CategorySerializer,
    TagSerializer,
    BookmarkSerializer,
)


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Hanya author yang bisa edit artikel miliknya."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user or request.user.is_staff


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet untuk kategori artikel.

    list    : GET    /api/v1/articles/categories/
    create  : POST   /api/v1/articles/categories/   (admin only)
    """
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']
    pagination_class = None


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet untuk tag (read-only)."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class ArticleViewSet(viewsets.ModelViewSet):
    """
    ViewSet untuk artikel.

    list    : GET    /api/v1/articles/
    create  : POST   /api/v1/articles/         (auth required)
    retrieve: GET    /api/v1/articles/{slug}/  (auto-increment view_count)
    update  : PUT    /api/v1/articles/{slug}/
    destroy : DELETE /api/v1/articles/{slug}/

    Filters: ?category=slug&tag=slug&status=published&q=keyword
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'content', 'excerpt', 'tags__name']
    ordering_fields = ['published_at', 'view_count', 'created_at']
    ordering = ['-published_at']
    lookup_field = 'slug'

    def get_queryset(self):
        qs = Article.objects.select_related('category', 'author').prefetch_related('tags')
        # Public hanya bisa lihat published, author bisa lihat semua miliknya
        if self.action in ['list', 'retrieve']:
            if self.request.user.is_authenticated:
                return qs.filter(
                    Q(status='published') | Q(author=self.request.user)
                )
            return qs.filter(status='published')
        return qs.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return ArticleListSerializer
        if self.action in ['create', 'update', 'partial_update']:
            return ArticleWriteSerializer
        return ArticleDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Auto increment view_count (kecuali author sendiri)
        if instance.author != request.user:
            instance.view_count += 1
            instance.save(update_fields=['view_count'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def popular(self, request):
        """GET /api/v1/articles/popular/ — top 10 most viewed articles."""
        popular = self.get_queryset().filter(status='published').order_by('-view_count')[:10]
        serializer = ArticleListSerializer(popular, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """GET /api/v1/articles/recent/ — latest 10 published articles."""
        recent = self.get_queryset().filter(status='published').order_by('-published_at')[:10]
        serializer = ArticleListSerializer(recent, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_articles(self, request):
        """GET /api/v1/articles/my_articles/ — artikel yang user buat."""
        my_qs = Article.objects.filter(author=request.user)
        serializer = ArticleListSerializer(my_qs, many=True, context={'request': request})
        return Response(serializer.data)


class BookmarkViewSet(viewsets.ModelViewSet):
    """
    ViewSet untuk bookmark artikel user.

    list    : GET    /api/v1/articles/bookmarks/
    create  : POST   /api/v1/articles/bookmarks/   {"article_id": 1}
    destroy : DELETE /api/v1/articles/bookmarks/{id}/
    """
    serializer_class = BookmarkSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Bookmark.objects.filter(user=self.request.user).select_related('article', 'article__category').prefetch_related('article__tags')

    def perform_create(self, serializer):
        # Prevent duplicate bookmark
        article = serializer.validated_data['article']
        bookmark, created = Bookmark.objects.get_or_create(
            user=self.request.user,
            article=article,
        )
        if not created:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'detail': 'Artikel sudah di-bookmark.'})