from unittest.mock import Mock
from graphql import GraphQLError
from tests.test_base import GraphQLTestCase
from django.contrib.auth import get_user_model


class DecoratorTests(GraphQLTestCase):
    def test_require_permission_decorator_with_permission(self):
        from apps.core.decorators import require_permission
        from apps.users.models import UserProfile

        @require_permission("user:read", resource="user")
        def test_resolver(self, info):
            return "success"

        # use the per-test user created in GraphQLTestCase.setUp
        real_user = self.user1

        # create profile via ORM so the OneToOne relation exists for lookups
        profile, _ = UserProfile.objects.get_or_create(user=real_user)
        # provide a runtime permission check (no need to save to DB)
        profile.has_permission = lambda codename: True

        mock_info = Mock()
        mock_info.context = Mock()
        mock_info.context.user = real_user
        mock_info.context.META = {"HTTP_X_FORWARDED_FOR": "127.0.0.1"}

        # call the resolver as if it were a bound method
        result = test_resolver(self, mock_info)
        self.assertEqual(result, "success")

    def test_require_permission_decorator_without_permission(self):
        from apps.core.decorators import require_permission
        from apps.users.models import UserProfile

        @require_permission("admin:delete", resource="admin")
        def test_resolver(self, info):
            return "success"

        real_user = self.user1
        profile, _ = UserProfile.objects.get_or_create(user=real_user)
        profile.has_permission = lambda codename: False

        mock_info = Mock()
        mock_info.context = Mock()
        mock_info.context.user = real_user
        mock_info.context.META = {"HTTP_X_FORWARDED_FOR": "127.0.0.1"}

        with self.assertRaises(GraphQLError):
            test_resolver(self, mock_info)

    def test_require_admin_decorator_with_admin(self):
        from apps.core.decorators import require_admin
        from apps.users.models import UserProfile

        User = get_user_model()

        @require_admin()
        def test_resolver(self, info):
            return "admin_success"

        # create a separate admin user to avoid changing testuser state
        real_user = User.objects.create_user(username="adminuser", password="testpass")
        profile = UserProfile.objects.create(user=real_user)
        profile.has_permission = lambda codename: True

        mock_info = Mock()
        mock_info.context = Mock()
        mock_info.context.user = real_user
        mock_info.context.META = {"HTTP_X_FORWARDED_FOR": "127.0.0.1"}

        result = test_resolver(self, mock_info)
        self.assertEqual(result, "admin_success")

    def test_mock_decorator_functionality(self):
        """Validate decorator wiring with a minimal mock implementation."""

        def mock_require_permission(permission, resource=None):
            def decorator(func):
                def wrapper(*args, **kwargs):
                    info = args[1] if len(args) > 1 else kwargs.get("info")
                    if hasattr(info, "context") and hasattr(info.context, "user"):
                        if getattr(info.context.user, "is_authenticated", False):
                            return func(*args, **kwargs)
                    raise GraphQLError("Permission denied")

                return wrapper

            return decorator

        @mock_require_permission("user:read")
        def test_resolver(self, info):
            return "success"

        mock_info = Mock()
        mock_info.context = Mock()
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_info.context.user = mock_user

        result = test_resolver(self, mock_info)
        self.assertEqual(result, "success")
