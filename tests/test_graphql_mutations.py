import json

import pytest

from tests.test_base import GraphQLTestCase


@pytest.mark.django_db
class UserMutationTests(GraphQLTestCase):
    def test_update_user_profile_mutation(self):
        mutation = """
        mutation($userId: Int!, $bio: String, $firstName: String) {
            updateUserProfile(userId: $userId, bio: $bio, firstName: $firstName) {
                success
                message
                user {
                    firstName
                }
                profile {
                    bio
                }
            }
        }
        """

        django_client = self._get_authenticated_client(self.user1)

        response = django_client.post(
            "/graphql/",
            data=json.dumps(
                {
                    "query": mutation,
                    "variables": {
                        "userId": self.user1.id,
                        "bio": "Updated bio",
                        "firstName": "John",
                    },
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 200, response.content
        result = response.json()
        assert result.get("errors") is None, result
        data = result["data"]["updateUserProfile"]
        assert data["success"] is True
        assert data["user"]["firstName"] == "John"
        assert data["profile"]["bio"] == "Updated bio"


@pytest.mark.django_db
class PostMutationTests(GraphQLTestCase):
    def test_create_post_mutation(self):
        mutation = """
        mutation($content: String!) {
            createPost(content: $content) {
                success
                message
                post {
                    content
                    author {
                        username
                    }
                }
            }
        }
        """

        django_client = self._get_authenticated_client(self.user1)

        response = django_client.post(
            "/graphql/",
            data=json.dumps(
                {"query": mutation, "variables": {"content": "New test post"}}
            ),
            content_type="application/json",
        )
        assert response.status_code == 200, response.content
        result = response.json()
        assert result.get("errors") is None, result
        data = result["data"]["createPost"]
        assert data["success"] is True
        assert data["post"]["content"] == "New test post"
        assert data["post"]["author"]["username"] == self.user1.username

    def test_update_post_mutation(self):
        mutation = """
        mutation($postId: Int!, $content: String!) {
            updatePost(postId: $postId, content: $content) {
                success
                message
                post {
                    content
                }
            }
        }
        """

        django_client = self._get_authenticated_client(self.user1)

        response = django_client.post(
            "/graphql/",
            data=json.dumps(
                {
                    "query": mutation,
                    "variables": {
                        "postId": self.post1.id,
                        "content": "Updated post content",
                    },
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 200, response.content
        result = response.json()
        assert result.get("errors") is None, result
        data = result["data"]["updatePost"]
        assert data["success"] is True
        assert data["post"]["content"] == "Updated post content"

    def test_delete_post_mutation(self):
        mutation = """
        mutation($postId: Int!) {
            deletePost(postId: $postId) {
                success
                message
            }
        }
        """

        django_client = self._get_authenticated_client(self.user1)

        response = django_client.post(
            "/graphql/",
            data=json.dumps(
                {"query": mutation, "variables": {"postId": self.post1.id}}
            ),
            content_type="application/json",
        )
        assert response.status_code == 200, response.content
        result = response.json()
        assert result.get("errors") is None, result
        data = result["data"]["deletePost"]
        assert data["success"] is True

        # If soft-delete semantics exist, refresh and check is_active
        if hasattr(self.post1, "refresh_from_db"):
            self.post1.refresh_from_db()
            assert getattr(self.post1, "is_active", False) is False
