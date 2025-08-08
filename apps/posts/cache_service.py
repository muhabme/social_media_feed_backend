from typing import List, Dict, Any, Optional
from django.contrib.auth.models import User
from django.db.models import QuerySet
from apps.core.redis_service import redis_service
from .models import Post
import hashlib
import json


class FeedCacheService:
    def __init__(self):
        self.redis = redis_service
        self.feed_timeout = 300  # 5 minutes
        self.post_timeout = 1800  # 30 minutes
        self.pagination_timeout = 300  # 5 minutes for pagination data

    def _generate_feed_key(self, user_id: int, page: int = 1, **filters) -> str:
        """Generate unique cache key for user feed"""
        filter_str = "".join(f"{k}:{v}" for k, v in sorted(filters.items()))
        key_string = f"user_feed:{user_id}:page:{page}:{filter_str}"
        return hashlib.md5(key_string.encode()).hexdigest()[:16]

    def get_cached_feed(self, user_id: int, page: int = 1, **filters) -> Optional[Dict]:
        """Get user's cached feed with pagination data"""
        cache_key = self._generate_feed_key(user_id, page, **filters)
        cached_data = self.redis.get_cached(f"feed:{cache_key}")

        if cached_data and isinstance(cached_data, dict):
            return cached_data
        elif cached_data and isinstance(cached_data, list):
            return {
                "items": cached_data,
                "total_items": len(cached_data),
                "total_pages": 1,
                "current_page": page,
            }
        return None

    def cache_user_feed(
        self, user_id: int, feed_data: Dict, page: int = 1, **filters
    ) -> bool:
        """Cache user's personalized feed with pagination metadata"""
        cache_key = self._generate_feed_key(user_id, page, **filters)
        return self.redis.set_cached(
            f"feed:{cache_key}", feed_data, timeout=self.feed_timeout
        )

    def cache_post_details(self, post_id: int, post_data: Dict) -> bool:
        """Cache individual post details"""
        return self.redis.set_cached(
            f"post:{post_id}", post_data, timeout=self.post_timeout
        )

    def get_cached_post(self, post_id: int) -> Optional[Dict]:
        """Get cached post details"""
        return self.redis.get_cached(f"post:{post_id}")

    def invalidate_user_feed(self, user_id: int):
        """Invalidate all cached versions of user's feed"""
        pattern = f"feed:*user_feed:{user_id}:*"
        keys = self.redis.redis_client.keys(pattern)
        if keys:
            self.redis.redis_client.delete(*keys)

        version_key = f"feed_version:{user_id}"
        self.redis.increment_counter(version_key)

    def invalidate_post_cache(self, post_id: int):
        """Invalidate cached post data"""
        self.redis.delete_cached(f"post:{post_id}")


feed_cache_service = FeedCacheService()
