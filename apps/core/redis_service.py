import json
import time
import hashlib
from typing import Any, Optional, List, Dict
from django.core.cache import cache, caches
from django.conf import settings
import redis


class RedisService:
    def __init__(self):
        self.default_cache = cache
        self.counter_cache = caches["counters"]
        self.session_cache = caches["sessions"]

        # Direct Redis connection for advanced operations
        self.redis_client = redis.from_url(
            settings.REDIS_URL, decode_responses=True, health_check_interval=30
        )

    # Cache Management
    def get_cached(self, key: str, cache_name: str = "default") -> Optional[Any]:
        """Get value from cache with proper error handling"""
        try:
            return caches[cache_name].get(key)
        except Exception as e:
            print(f"Cache get error for key {key}: {e}")
            return None

    def set_cached(
        self, key: str, value: Any, timeout: int = 300, cache_name: str = "default"
    ) -> bool:
        """Set value in cache with proper error handling"""
        try:
            return caches[cache_name].set(key, value, timeout)
        except Exception as e:
            print(f"Cache set error for key {key}: {e}")
            return False

    def delete_cached(self, key: str, cache_name: str = "default") -> bool:
        """Delete value from cache"""
        try:
            return caches[cache_name].delete(key)
        except Exception as e:
            print(f"Cache delete error for key {key}: {e}")
            return False

    def get_or_set_cached(
        self, key: str, default_func, timeout: int = 300, cache_name: str = "default"
    ) -> Any:
        """Get from cache or set if doesn't exist"""
        cached_value = self.get_cached(key, cache_name)
        if cached_value is not None:
            return cached_value

        value = default_func()
        self.set_cached(key, value, timeout, cache_name)
        return value

    # Counter Operations
    def increment_counter(self, key: str, amount: int = 1) -> int:
        """Increment counter in Redis"""
        try:
            return self.counter_cache.get_or_set(key, 0) + amount
        except Exception:
            # Fallback to direct Redis
            return self.redis_client.incr(key, amount)

    def get_counter(self, key: str) -> int:
        """Get counter value"""
        try:
            return self.counter_cache.get(key, 0)
        except Exception:
            return int(self.redis_client.get(key) or 0)

    def reset_counter(self, key: str) -> bool:
        """Reset counter to 0"""
        return self.set_cached(key, 0, cache_name="counters", timeout=None)

    # List Operations
    def push_to_list(self, key: str, value: Any, max_length: int = 100) -> bool:
        """Push value to Redis list with max length"""
        try:
            serialized_value = (
                json.dumps(value) if not isinstance(value, str) else value
            )
            self.redis_client.lpush(key, serialized_value)
            self.redis_client.ltrim(key, 0, max_length - 1)
            return True
        except Exception as e:
            print(f"List push error for key {key}: {e}")
            return False

    def get_list(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """Get list from Redis"""
        try:
            items = self.redis_client.lrange(key, start, end)
            return [
                json.loads(item) if item.startswith("{") else item for item in items
            ]
        except Exception as e:
            print(f"List get error for key {key}: {e}")
            return []

    # Set Operations
    def add_to_set(self, key: str, value: str) -> bool:
        """Add value to Redis set"""
        try:
            return bool(self.redis_client.sadd(key, value))
        except Exception as e:
            print(f"Set add error for key {key}: {e}")
            return False

    def is_in_set(self, key: str, value: str) -> bool:
        """Check if value is in Redis set"""
        try:
            return self.redis_client.sismember(key, value)
        except Exception as e:
            print(f"Set check error for key {key}: {e}")
            return False

    # Sorted Set Operations (for trending, rankings)
    def add_to_sorted_set(
        self, key: str, mapping: Dict[str, float], expire: int = None
    ) -> bool:
        """Add items to sorted set with scores"""
        try:
            result = self.redis_client.zadd(key, mapping)
            if expire:
                self.redis_client.expire(key, expire)
            return bool(result)
        except Exception as e:
            print(f"Sorted set add error for key {key}: {e}")
            return False

    def get_top_from_sorted_set(self, key: str, limit: int = 10) -> List[str]:
        """Get top items from sorted set"""
        try:
            return self.redis_client.zrevrange(key, 0, limit - 1)
        except Exception as e:
            print(f"Sorted set get error for key {key}: {e}")
            return []

    # Pub/Sub Operations
    def publish(self, channel: str, message: Any) -> bool:
        """Publish message to Redis channel"""
        try:
            serialized_message = (
                json.dumps(message) if not isinstance(message, str) else message
            )
            self.redis_client.publish(channel, serialized_message)
            return True
        except Exception as e:
            print(f"Publish error for channel {channel}: {e}")
            return False

    # Key Management
    def expire_key(self, key: str, seconds: int) -> bool:
        """Set expiration for key"""
        try:
            return self.redis_client.expire(key, seconds)
        except Exception as e:
            print(f"Expire error for key {key}: {e}")
            return False

    def key_exists(self, key: str) -> bool:
        """Check if key exists"""
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            print(f"Key exists error for key {key}: {e}")
            return False


# Global Redis service instance
redis_service = RedisService()
