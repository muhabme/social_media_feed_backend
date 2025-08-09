from tests.test_base import GraphQLTestCase
from django.contrib.auth.models import User
import json
from django.test import Client as DjangoClient


class SecurityTests(GraphQLTestCase):
    """Security tests to ensure proper access controls"""

    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated users can't access protected queries"""
        query = """
        query {
            me {
                id
                username
            }
        }
        """

        django_client = DjangoClient()
        response = django_client.post(
            "/graphql/",
            data=json.dumps({"query": query}),
            content_type="application/json",
        )
        result = response.json()

        self.assertTrue(result.get("errors") is not None)

    def test_user_cannot_update_others_posts(self):
        """Test that users can only update their own posts"""
        mutation = """
        mutation($postId: Int!, $content: String!) {
            updatePost(postId: $postId, content: $content) {
                success
                message
            }
        }
        """

        django_client = self._get_authenticated_client(self.user2)

        response = django_client.post(
            "/graphql/",
            data=json.dumps(
                {
                    "query": mutation,
                    "variables": {
                        "postId": self.post1.id,
                        "content": "Hacked content",
                    },
                }
            ),
            content_type="application/json",
        )
        result = response.json()

        # Should fail (either via errors or success=False)
        self.assertTrue(
            result.get("errors") is not None
            or not result.get("data", {}).get("updatePost", {}).get("success", True)
        )

    def test_user_cannot_delete_others_posts(self):
        """Test that users can only delete their own posts"""
        mutation = """
        mutation($postId: Int!) {
            deletePost(postId: $postId) {
                success
                message
            }
        }
        """

        django_client = self._get_authenticated_client(self.user2)

        response = django_client.post(
            "/graphql/",
            data=json.dumps(
                {"query": mutation, "variables": {"postId": self.post1.id}}
            ),
            content_type="application/json",
        )
        result = response.json()

        self.assertTrue(
            result.get("errors") is not None
            or not result.get("data", {}).get("deletePost", {}).get("success", True)
        )

    def test_user_cannot_update_others_profile(self):
        """Test that users can only update their own profile"""
        mutation = """
        mutation($userId: Int!, $bio: String!) {
            updateUserProfile(userId: $userId, bio: $bio) {
                success
                message
            }
        }
        """

        django_client = self._get_authenticated_client(self.user2)

        response = django_client.post(
            "/graphql/",
            data=json.dumps(
                {
                    "query": mutation,
                    "variables": {"userId": self.user1.id, "bio": "Hacked bio"},
                }
            ),
            content_type="application/json",
        )
        result = response.json()

        # Should fail due to permission check
        self.assertTrue(
            result.get("errors") is not None
            or not result.get("data", {})
            .get("updateUserProfile", {})
            .get("success", True)
        )

    def test_sql_injection_prevention(self):
        """Test that GraphQL queries are safe from SQL injection"""
        malicious_query = """
        query {
            user(username: "'; DROP TABLE users; --") {
                id
                username
            }
        }
        """

        django_client = self._get_authenticated_client(self.user1)
        response = django_client.post(
            "/graphql/",
            data=json.dumps({"query": malicious_query}),
            content_type="application/json",
        )
        result = response.json()
        self.assertIsNone(result.get("errors"))

        # Should return None (user not found) without causing DB issues
        self.assertIsNone(result["data"]["user"])

        # Verify the specific test users still exist (scope the check)
        self.assertEqual(
            User.objects.filter(
                username__in=[self.user1.username, self.user2.username]
            ).count(),
            2,
        )
