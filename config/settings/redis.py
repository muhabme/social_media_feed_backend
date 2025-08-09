from decouple import config

REDIS_URL = f"redis://{config('REDIS_HOST', default='redis')}:{config('REDIS_PORT', default='6379')}"

# Django Cache Configuration
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL + "/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SERIALIZER": "django_redis.serializers.json.JSONSerializer",
            "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 20,
                "retry_on_timeout": True,
            },
        },
        "KEY_PREFIX": "social_media",
        "TIMEOUT": 300,  # 5 minutes default
    },
    # Separate cache for sessions
    "sessions": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL + "/2",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "TIMEOUT": 86400,  # 24 hours
    },
    # Cache for real-time counters
    "counters": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL + "/3",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "TIMEOUT": None,  # Never expire counters
    },
}

# Use Redis for sessions
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "sessions"
SESSION_COOKIE_AGE = 86400  # 24 hours

# Celery Configuration (for background tasks)
CELERY_BROKER_URL = REDIS_URL + "/4"
CELERY_RESULT_BACKEND = REDIS_URL + "/5"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
