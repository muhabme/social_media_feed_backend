from unittest.mock import Mock, patch

import pytest
from django.test import TestCase

pytest.importorskip(
    "apps.posts.cache_service", reason="posts.cache_service not available"
)


@pytest.mark.django_db
class FeedCacheServiceTests(TestCase):
    def setUp(self):
        from apps.posts.cache_service import FeedCacheService

        self.cache_service = FeedCacheService()

    @patch("apps.posts.cache_service.redis_service")
    def test_cache_user_feed(self, mock_redis_service):
        """Ensure cache_user_feed calls redis set and returns True on success."""
        # Arrange
        mock_redis_service.set_cached.return_value = True
        self.cache_service.redis = mock_redis_service

        feed_data = {
            "items": [{"id": 1, "content": "Test post"}],
            "total_items": 1,
            "total_pages": 1,
            "current_page": 1,
        }

        # Act
        result = self.cache_service.cache_user_feed(1, feed_data, page=1)

        # Assert
        assert result is True
        mock_redis_service.set_cached.assert_called_once()

    @patch("apps.posts.cache_service.redis_service")
    def test_get_cached_feed(self, mock_redis_service):
        """Ensure get_cached_feed returns deserialized data when available."""
        mock_redis_service.get_cached.return_value = {
            "items": [{"id": 1}],
            "total_items": 1,
        }
        self.cache_service.redis = mock_redis_service

        result = self.cache_service.get_cached_feed(1, page=1)
        assert result is not None
        assert result["total_items"] == 1
        mock_redis_service.get_cached.assert_called_once()

    @patch("apps.posts.cache_service.redis_service")
    def test_cache_post_details(self, mock_redis_service):
        """Ensure caching post details uses redis set method."""
        mock_redis_service.set_cached.return_value = True
        self.cache_service.redis = mock_redis_service

        post_data = {
            "id": 1,
            "content": "Test post",
            "author": {"id": 1, "username": "testuser"},
        }

        result = self.cache_service.cache_post_details(1, post_data)
        assert result is True
        mock_redis_service.set_cached.assert_called_once()

    @patch("apps.posts.cache_service.redis_service")
    def test_invalidate_user_feed(self, mock_redis_service):
        """Invalidate should delete matching keys and bump feed version counter."""
        mock_client = Mock()
        mock_client.keys.return_value = ["feed:key1", "feed:key2"]
        mock_client.delete = Mock()
        mock_redis_service.redis_client = mock_client
        mock_redis_service.increment_counter = Mock()
        self.cache_service.redis = mock_redis_service

        self.cache_service.invalidate_user_feed(1)

        mock_client.delete.assert_called_once_with("feed:key1", "feed:key2")
        mock_redis_service.increment_counter.assert_called_once_with("feed_version:1")
