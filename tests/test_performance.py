import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from apps.users.models import Role, Permission, UserProfile
from django.test.utils import CaptureQueriesContext
from django.db import connection


@pytest.mark.django_db
class PerformanceTests(TestCase):
    def setUp(self):
        # Create (or get) role
        self.role, _created = Role.objects.get_or_create(
            name="user", defaults={"is_active": True}
        )

    def test_bulk_user_query_efficiency(self):
        """
        Ensure typical user/profile retrieval uses optimized queries.
        We assert the number of DB queries is reasonable (keeps tests stable
        across CI variations) rather than asserting elapsed time.
        """
        # Create permission and users
        permission, _ = Permission.objects.get_or_create(
            codename="user:read",
            defaults={"name": "User Read", "description": "Permission to read users"},
        )

        users = []
        for i in range(50):  # moderate amount to validate select_related usage
            user = User.objects.create_user(
                username=f"user{i}", email=f"user{i}@test.com", password="testpass"
            )
            UserProfile.objects.create(user=user, role=self.role)
            users.append(user)

        # When using select_related, total queries should be small (e.g., < 5)
        with CaptureQueriesContext(connection) as ctx:
            profiles = UserProfile.objects.select_related("user", "role").all()
            list(profiles)  # force evaluation

        # assert that queries count is modest (this threshold is conservative)
        self.assertLess(len(ctx.captured_queries), 6)

    def test_bulk_post_query_efficiency(self):
        """Ensure post retrieval with select_related is efficient."""
        permission, _ = Permission.objects.get_or_create(
            codename="post:read",
            defaults={"name": "Post Read", "description": "Permission to read posts"},
        )

        user = User.objects.create_user(
            username="perfuser", email="perfuser@test.com", password="testpass"
        )
        UserProfile.objects.create(user=user, role=self.role)

        from apps.posts.models import Post

        for i in range(50):
            Post.objects.create(author=user, content=f"Test post content {i}")

        with CaptureQueriesContext(connection) as ctx:
            posts_query = Post.objects.select_related("author").all()
            list(posts_query)

        self.assertLess(len(ctx.captured_queries), 6)
