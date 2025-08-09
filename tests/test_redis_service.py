import pytest
from unittest.mock import Mock, patch
from django.test import TestCase

pytest.importorskip(
    "apps.core.redis_service", reason="core.redis_service not available"
)


@pytest.mark.django_db
class RedisServiceTests(TestCase):
    def setUp(self):
        from apps.core.redis_service import RedisService

        self.redis_service = RedisService()

    @patch("apps.core.redis_service.caches")
    def test_get_cached_success(self, mock_caches):
        mock_cache = Mock()
        mock_cache.get.return_value = "cached_value"
        mock_caches.__getitem__.return_value = mock_cache

        result = self.redis_service.get_cached("test_key")
        assert result == "cached_value"
        mock_cache.get.assert_called_once_with("test_key")

    @patch("apps.core.redis_service.caches")
    def test_get_cached_error_handling(self, mock_caches):
        mock_cache = Mock()
        mock_cache.get.side_effect = Exception("Cache error")
        mock_caches.__getitem__.return_value = mock_cache

        result = self.redis_service.get_cached("test_key")
        assert result is None

    @patch("apps.core.redis_service.caches")
    def test_set_cached_success(self, mock_caches):
        mock_cache = Mock()
        mock_cache.set.return_value = True
        mock_caches.__getitem__.return_value = mock_cache

        result = self.redis_service.set_cached("test_key", "test_value", 300)
        assert result is True
        mock_cache.set.assert_called_once_with("test_key", "test_value", 300)

    def test_increment_counter(self):
        with patch.object(
            self.redis_service.counter_cache, "get_or_set"
        ) as mock_get_or_set:
            mock_get_or_set.return_value = 5
            result = self.redis_service.increment_counter("test_counter", 2)
            assert result == 7

    @patch("apps.core.redis_service.redis")
    def test_push_to_list(self, mock_redis):
        mock_client = Mock()
        self.redis_service.redis_client = mock_client

        result = self.redis_service.push_to_list("test_list", {"key": "value"}, 10)
        assert result is True
        mock_client.lpush.assert_called_once()
        mock_client.ltrim.assert_called_once_with("test_list", 0, 9)

    @patch("apps.core.redis_service.redis")
    def test_add_to_set(self, mock_redis):
        mock_client = Mock()
        mock_client.sadd.return_value = 1
        self.redis_service.redis_client = mock_client

        result = self.redis_service.add_to_set("test_set", "test_value")
        assert result is True
        mock_client.sadd.assert_called_once_with("test_set", "test_value")

    @patch("apps.core.redis_service.redis")
    def test_is_in_set(self, mock_redis):
        mock_client = Mock()
        mock_client.sismember.return_value = True
        self.redis_service.redis_client = mock_client

        result = self.redis_service.is_in_set("test_set", "test_value")
        assert result is True
        mock_client.sismember.assert_called_once_with("test_set", "test_value")
