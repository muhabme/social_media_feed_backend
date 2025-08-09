import pytest
from django.contrib.auth.models import User
from django.test import Client as DjangoClient

pytest_plugins = ["pytest_django"]


@pytest.fixture
def django_client():
    """A Django test client instance."""
    return DjangoClient()


@pytest.fixture
def user1(db):
    """Create and return a test user."""
    return User.objects.create_user(
        username="testuser1", email="test1@example.com", password="testpass123"
    )


@pytest.fixture
def user2(db):
    """Create and return a second test user."""
    return User.objects.create_user(
        username="testuser2", email="test2@example.com", password="testpass123"
    )
