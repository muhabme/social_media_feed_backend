import pytest
from django.test import TestCase
from django.contrib.auth.models import User

pytestmark = pytest.mark.django_db


class RolePermissionModelTests(TestCase):
    def setUp(self):
        # Use unique test names to avoid cross-test collisions
        from apps.users.models import Role, Permission

        self.role, _ = Role.objects.get_or_create(
            name="test_role_models",
            defaults={"description": "Test Role", "is_active": True},
        )
        self.permission, _ = Permission.objects.get_or_create(
            codename="test:read_models",
            defaults={
                "name": "Test Permission Models",
                "description": "Test permission",
                "resource": "test",
                "action": "read",
            },
        )

    def test_role_creation(self):
        from apps.users.models import Role

        role, _ = Role.objects.get_or_create(
            name="admin_test_models",
            defaults={"description": "Admin role", "is_active": True},
        )
        assert role.name == "admin_test_models"
        assert role.is_active is True
        assert str(role) == role.name

    def test_permission_creation(self):
        from apps.users.models import Permission

        permission, _ = Permission.objects.get_or_create(
            codename="user:create",
            defaults={"name": "User Create", "resource": "user", "action": "create"},
        )
        assert str(permission) == "user:create"

    def test_role_permission_relationship(self):
        from apps.users.models import RolePermission

        role_perm, _ = RolePermission.objects.get_or_create(
            role=self.role, permission=self.permission
        )
        assert role_perm.role == self.role
        assert role_perm.permission == self.permission

    def test_unique_role_permission_constraint(self):
        from apps.users.models import RolePermission

        RolePermission.objects.get_or_create(role=self.role, permission=self.permission)
        role_perm, created = RolePermission.objects.get_or_create(
            role=self.role, permission=self.permission
        )
        assert created is False


class UserProfileModelTests(TestCase):
    def setUp(self):
        from apps.users.models import Role, Permission, RolePermission

        self.user = User.objects.create_user(
            username="testuser_models", email="test@example.com", password="testpass123"
        )
        self.role, _ = Role.objects.get_or_create(
            name="user_models", defaults={"is_active": True}
        )
        self.permission, _ = Permission.objects.get_or_create(
            codename="post:read_models",
            defaults={"name": "Read Posts", "resource": "post", "action": "read"},
        )
        RolePermission.objects.get_or_create(role=self.role, permission=self.permission)

    def test_user_profile_creation(self):
        from apps.users.models import UserProfile

        profile = UserProfile.objects.create(
            user=self.user, bio="Test bio", role=self.role
        )
        assert profile.user == self.user
        assert profile.bio == "Test bio"
        assert str(profile) == f"profile:{self.user.username}"

    def test_has_permission_with_active_role(self):
        from apps.users.models import UserProfile

        profile = UserProfile.objects.create(user=self.user, role=self.role)
        assert profile.has_permission("post:read_models") is True
        assert profile.has_permission("post:write_models") is False

    def test_has_permission_with_inactive_role(self):
        from apps.users.models import UserProfile

        self.role.is_active = False
        self.role.save()
        profile = UserProfile.objects.create(user=self.user, role=self.role)
        assert profile.has_permission("post:read_models") is False

    def test_has_permission_without_role(self):
        from apps.users.models import UserProfile

        profile = UserProfile.objects.create(user=self.user)
        assert profile.has_permission("post:read_models") is False

    def test_get_permissions(self):
        from apps.users.models import UserProfile

        profile = UserProfile.objects.create(user=self.user, role=self.role)
        permissions = profile.get_permissions()
        assert self.permission in permissions
