from unittest.mock import patch

import pytest
from django.contrib.auth.models import AnonymousUser, User

from tests.test_base import GraphQLTestCase

pytestmark = pytest.mark.django_db


class PermissionTests(GraphQLTestCase):
    def test_check_permission_with_valid_permission(self):
        """Test permission check with valid permission"""
        from apps.core.permissions import check_permission
        from apps.users.models import UserProfile

        # Ensure profile exists and patch has_permission
        profile, _ = UserProfile.objects.get_or_create(user=self.user1)
        with patch.object(profile, "has_permission", return_value=True):
            result = check_permission(self.user1, "user:read")
            assert result is True

    def test_check_permission_with_invalid_permission(self):
        """Test permission check with invalid permission"""
        from apps.core.permissions import check_permission
        from apps.users.models import UserProfile

        profile, _ = UserProfile.objects.get_or_create(user=self.user1)
        with patch.object(profile, "has_permission", return_value=False):
            result = check_permission(self.user1, "invalid:permission")
            assert result is False

    def test_check_permission_unauthenticated_user(self):
        """Test permission check with unauthenticated user"""
        from apps.core.permissions import check_permission

        anonymous_user = AnonymousUser()
        result = check_permission(anonymous_user, "user:read")
        assert result is False

    def test_check_permission_user_without_profile(self):
        """Test permission check with user without profile"""
        user_without_profile = User.objects.create_user(
            username="noprofile_perm", email="noprofile@test.com", password="pass"
        )

        from apps.core.permissions import check_permission

        result = check_permission(user_without_profile, "user:read")
        assert result is False
