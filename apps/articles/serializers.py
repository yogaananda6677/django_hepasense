"""Serializers for articles app."""

from rest_framework import serializers

from apps.accounts.serializers import UserSerializer
from apps.articles.models import Article, Category, Tag, Bookmark


class CategorySerializer(serializers.ModelSerializer):
    article_count = serializers.IntegerField(source='articles.count', read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'icon', 'is_active', 'article_count']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']


class ArticleListSerializer(serializers.ModelSerializer):
    """Serializer ringan untuk list view (no full content)."""
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    author_name = serializers.CharField(source='author.get_full_name', read_only=True)
    is_bookmarked = serializers.SerializerMethodField()

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'slug', 'excerpt', 'featured_image',
            'category', 'tags', 'author_name',
            'status', 'view_count', 'read_time_minutes',
            'published_at', 'created_at', 'is_bookmarked',
        ]

    def get_is_bookmarked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Bookmark.objects.filter(user=request.user, article=obj).exists()
        return False


class ArticleDetailSerializer(ArticleListSerializer):
    """Serializer lengkap termasuk content."""
    author = UserSerializer(read_only=True)

    class Meta(ArticleListSerializer.Meta):
        fields = ArticleListSerializer.Meta.fields + ['content', 'updated_at']


class ArticleWriteSerializer(serializers.ModelSerializer):
    """Serializer untuk create/update artikel (admin/doctor only)."""

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'excerpt', 'content', 'featured_image',
            'category', 'tags', 'status',
            'meta_title', 'meta_description',
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        validated_data['author'] = self.context['request'].user
        article = Article.objects.create(**validated_data)
        if tags:
            article.tags.set(tags)
        return article


class BookmarkSerializer(serializers.ModelSerializer):
    article = ArticleListSerializer(read_only=True)
    article_id = serializers.PrimaryKeyRelatedField(
        queryset=Article.objects.all(),
        source='article',
        write_only=True,
    )

    class Meta:
        model = Bookmark
        fields = ['id', 'article', 'article_id', 'created_at']
        read_only_fields = ['id', 'created_at']