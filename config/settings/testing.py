"""
Test settings for Django project.
Optimized for fast test execution.
"""

from .base import *
from datetime import timedelta
import tempfile
import os

# Testing flags
DEBUG = False
TESTING = True

# Use fast SQLite database for testing
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "OPTIONS": {
            "timeout": 20,
        },
        "TEST": {
            "NAME": ":memory:",
        },
    }
}

# Use faster password hashers for testing
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable logging during tests to reduce noise
LOGGING_CONFIG = None
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
    },
    "loggers": {
        "django": {
            "handlers": ["null"],
            "propagate": False,
        },
    },
}

# Email backend for testing
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

SESSION_ENGINE = "django.contrib.sessions.backends.db"

# Use dummy cache backend for tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        "LOCATION": "test-cache",
    },
    "sessions": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        "LOCATION": "test-cache",
    },
    "counters": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        "LOCATION": "test-cache",
    },
}

# Disable rate limiting in tests
RATELIMIT_ENABLE = False

# Fast JWT settings for tests
JWT_SECRET_KEY = "test-jwt-secret-key-for-testing-only"
GRAPHQL_JWT = {
    "JWT_SECRET_KEY": JWT_SECRET_KEY,
    "JWT_EXPIRATION_DELTA": timedelta(hours=1),
    "JWT_AUTH_HEADER_PREFIX": "Bearer",
    "JWT_VERIFY_EXPIRATION": True,
    "JWT_VERIFY": True,
}

# Test runner configuration
TEST_RUNNER = "django.test.runner.DiscoverRunner"
ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

# Media files for testing
MEDIA_ROOT = os.path.join(tempfile.gettempdir(), "test_media")
MEDIA_URL = "/test_media/"

# Static files for testing
STATIC_ROOT = os.path.join(tempfile.gettempdir(), "test_static")

# Security settings for testing
SECRET_KEY = "django-insecure-test-key-only-for-testing-do-not-use-in-production"

# Celery settings for testing (if using Celery)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# GraphQL settings for testing
GRAPHENE = {
    "SCHEMA": "graphql_api.schema.schema",
    "MIDDLEWARE": [
        "graphql_jwt.middleware.JSONWebTokenMiddleware",
    ],
}

# Override any Redis settings for testing
if "REDIS_LOCATION" in locals():
    REDIS_LOCATION = "redis://localhost:6379/15"  # Use different DB for tests

# Disable any external API calls during testing
# Add any other service URLs that should be mocked
EXTERNAL_API_BASE_URL = "http://testserver/api/"

# Performance testing settings
PERFORMANCE_TEST_THRESHOLD = 1.0  # seconds

# Test-specific middleware (remove any that cause issues in tests)
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Disable any problematic apps for testing
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "graphene_django",
    "corsheaders",
    # Remove django_redis and django_ratelimit for tests if causing issues
] + LOCAL_APPS

# Authentication backends for testing
AUTHENTICATION_BACKENDS = [
    "graphql_jwt.backends.JSONWebTokenBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# Ensure timezone settings
USE_TZ = True
TIME_ZONE = "UTC"
