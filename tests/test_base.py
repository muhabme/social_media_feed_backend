from django.test import TestCase, Client as DjangoClient
from django.contrib.auth import get_user_model


class GraphQLTestCase(TestCase):
    """
    Base TestCase for GraphQL tests.

    - Uses setUpTestData to create common roles/permissions once per test class.
    - Keeps per-test users and other entities in setUp so each test gets a clean slate.
    """

    @classmethod
    def setUpTestData(cls):
        # Run expensive DB setup once per TestCase class.
        cls._setup_permissions_and_roles()

    @classmethod
    def _setup_permissions_and_roles(cls):
        # import here to avoid app import-time side-effects in some test runners
        from apps.users.models import Role, Permission, RolePermission

        permissions_data = [
            ("user:read", "user", "read", "User Read"),
            ("user:create", "user", "create", "User Create"),
            ("user:update", "user", "update", "User Update"),
            ("user:delete", "user", "delete", "User Delete"),
            ("post:read", "post", "read", "Post Read"),
            ("post:create", "post", "create", "Post Create"),
            ("post:update", "post", "update", "Post Update"),
            ("post:delete", "post", "delete", "Post Delete"),
            ("like:create", "like", "create", "Like Create"),
            ("comment:create", "comment", "create", "Comment Create"),
            ("comment:update", "comment", "update", "Comment Update"),
            ("comment:delete", "comment", "delete", "Comment Delete"),
            ("share:create", "share", "create", "Share Create"),
            ("follow:create", "follow", "create", "Follow Create"),
            ("follow:delete", "follow", "delete", "Follow Delete"),
            ("admin:access", "admin", "access", "Admin Access"),
        ]

        cls.permissions = {}
        for codename, resource, action, name in permissions_data:
            perm, _created = Permission.objects.get_or_create(
                codename=codename,
                defaults={
                    "name": name,
                    "resource": resource,
                    "action": action,
                    "description": f"{name} permission",
                },
            )
            cls.permissions[codename] = perm

        cls.user_role, _ = Role.objects.get_or_create(
            name="user",
            defaults={"description": "Regular user role", "is_active": True},
        )

        cls.admin_role, _ = Role.objects.get_or_create(
            name="admin", defaults={"description": "Admin role", "is_active": True}
        )

        user_permissions = [
            "user:read",
            "user:update",
            "post:read",
            "post:create",
            "post:update",
            "post:delete",
            "like:create",
            "comment:create",
            "comment:update",
            "share:create",
            "follow:create",
            "follow:delete",
        ]

        for perm_codename in user_permissions:
            perm = cls.permissions.get(perm_codename)
            if perm:
                RolePermission.objects.get_or_create(
                    role=cls.user_role, permission=perm
                )

        # give admin all permissions
        for perm in cls.permissions.values():
            RolePermission.objects.get_or_create(role=cls.admin_role, permission=perm)

    def setUp(self):
        """
        Create per-test users and test content. TestCase takes care of DB cleanup,
        so we keep per-test state simple and isolated.
        """
        User = get_user_model()
        self.user1 = User.objects.create_user(
            username="testuser1", email="test1@example.com", password="testpass123"
        )
        self.user2 = User.objects.create_user(
            username="testuser2", email="test2@example.com", password="testpass123"
        )

        self.setup_user_profiles()
        self.setup_test_posts()

    def setup_user_profiles(self):
        from apps.users.models import UserProfile

        # Create profiles tied to the user_role if available; otherwise default
        role = getattr(self.__class__, "user_role", None)
        if role and getattr(role, "id", None):
            self.profile1 = UserProfile.objects.create(
                user=self.user1, bio="Test bio 1", role=role
            )
            self.profile2 = UserProfile.objects.create(
                user=self.user2, bio="Test bio 2", role=role
            )
        else:
            self.profile1 = UserProfile.objects.create(
                user=self.user1, bio="Test bio 1"
            )
            self.profile2 = UserProfile.objects.create(
                user=self.user2, bio="Test bio 2"
            )

    def setup_test_posts(self):
        from apps.posts.models import Post

        self.post1 = Post.objects.create(
            author=self.user1, content="Test post content 1"
        )
        self.post2 = Post.objects.create(
            author=self.user2, content="Test post content 2"
        )

    def _authenticate_user(self, user):
        """
        Small helper that returns a minimal mock context object used by resolvers.
        Useful for unit testing resolvers without the full HTTP client.
        """

        class MockContext:
            def __init__(self, user):
                self.user = user
                self.META = {
                    "REMOTE_ADDR": "127.0.0.1",
                    "HTTP_USER_AGENT": "Test Agent",
                }

        return MockContext(user)

    def _get_authenticated_client(self, user):
        """
        Return a Django test client where `user` is already force-logged-in.
        This avoids dealing with sessions in tests that just need authenticated requests.
        """
        client = DjangoClient()
        client.force_login(user)
        return client
