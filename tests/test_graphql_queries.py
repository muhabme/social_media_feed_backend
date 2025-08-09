import json
import pytest
from tests.test_base import GraphQLTestCase


@pytest.mark.django_db
class UserQueryTests(GraphQLTestCase):
    def test_me_query_authenticated(self):
        query = """
        query {
            me {
                id
                username
                email
            }
        }
        """

        django_client = self._get_authenticated_client(self.user1)

        response = django_client.post(
            "/graphql/",
            data=json.dumps({"query": query}),
            content_type="application/json",
        )
        assert response.status_code == 200, response.content
        result = response.json()
        assert result.get("errors") is None, result
        data = result["data"]["me"]
        assert data["username"] == self.user1.username
        assert data["email"] == self.user1.email

    def test_user_query_by_id(self):
        query = """
        query($userId: Int!) {
            user(id: $userId) {
                id
                username
                email
            }
        }
        """

        django_client = self._get_authenticated_client(self.user1)

        response = django_client.post(
            "/graphql/",
            data=json.dumps({"query": query, "variables": {"userId": self.user2.id}}),
            content_type="application/json",
        )
        assert response.status_code == 200, response.content
        result = response.json()
        assert result.get("errors") is None, result
        data = result["data"]["user"]
        assert data["username"] == self.user2.username

    def test_user_profile_query(self):
        query = """
        query($userId: Int!) {
            userProfile(userId: $userId) {
                bio
                user {
                    username
                }
            }
        }
        """

        django_client = self._get_authenticated_client(self.user1)

        response = django_client.post(
            "/graphql/",
            data=json.dumps({"query": query, "variables": {"userId": self.user1.id}}),
            content_type="application/json",
        )
        assert response.status_code == 200, response.content
        result = response.json()
        assert result.get("errors") is None, result
        data = result["data"]["userProfile"]
        assert data["bio"] == "Test bio 1"
        assert data["user"]["username"] == self.user1.username


@pytest.mark.django_db
class PostQueryTests(GraphQLTestCase):
    def test_post_query_by_id(self):
        query = """
        query($postId: Int!) {
            post(id: $postId) {
                id
                content
                author {
                    username
                }
                likesCount
                commentsCount
            }
        }
        """

        django_client = self._get_authenticated_client(self.user1)

        response = django_client.post(
            "/graphql/",
            data=json.dumps({"query": query, "variables": {"postId": self.post1.id}}),
            content_type="application/json",
        )
        assert response.status_code == 200, response.content
        result = response.json()
        assert result.get("errors") is None, result
        data = result["data"]["post"]
        assert data["content"] == "Test post content 1"
        assert data["author"]["username"] == self.user1.username
        assert data["likesCount"] == 0

    def test_posts_by_user_query(self):
        query = """
        query($userId: Int!) {
            postsByUser(userId: $userId) {
                items {
                    id
                    content
                    author {
                        username
                    }
                }
                totalItems
            }
        }
        """

        django_client = self._get_authenticated_client(self.user1)

        response = django_client.post(
            "/graphql/",
            data=json.dumps({"query": query, "variables": {"userId": self.user1.id}}),
            content_type="application/json",
        )
        assert response.status_code == 200, response.content
        result = response.json()
        assert result.get("errors") is None, result
        data = result["data"]["postsByUser"]
        assert len(data["items"]) == 1
        assert data["items"][0]["content"] == "Test post content 1"


@pytest.mark.django_db
class FollowQueryTests(GraphQLTestCase):
    def setUp(self):
        super().setUp()
        from apps.users.models import Follow

        Follow.objects.create(follower=self.user1, following=self.user2)

    def test_followers_query(self):
        query = """
        query($userId: Int!) {
            followers(userId: $userId) {
                items {
                    id
                    username
                }
                totalItems
            }
        }
        """

        django_client = self._get_authenticated_client(self.user1)

        response = django_client.post(
            "/graphql/",
            data=json.dumps({"query": query, "variables": {"userId": self.user2.id}}),
            content_type="application/json",
        )
        assert response.status_code == 200, response.content
        result = response.json()
        assert result.get("errors") is None, result
        data = result["data"]["followers"]
        assert len(data["items"]) == 1
        assert data["items"][0]["username"] == self.user1.username

    def test_is_following_query(self):
        query = """
        query($userId: Int!) {
            isFollowing(userId: $userId)
        }
        """

        django_client = self._get_authenticated_client(self.user1)

        response = django_client.post(
            "/graphql/",
            data=json.dumps({"query": query, "variables": {"userId": self.user2.id}}),
            content_type="application/json",
        )
        assert response.status_code == 200, response.content
        result = response.json()
        assert result.get("errors") is None, result
        assert result["data"]["isFollowing"] is True
