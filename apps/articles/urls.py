"""URL routing for articles app."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.articles.views import (
    ArticleViewSet,
    CategoryViewSet,
    TagViewSet,
    BookmarkViewSet,
)

app_name = 'articles'

router = DefaultRouter()
router.register(r'articles', ArticleViewSet, basename='article')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'bookmarks', BookmarkViewSet, basename='bookmark')

urlpatterns = [
    path('', include(router.urls)),
]