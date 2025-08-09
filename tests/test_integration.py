import json

import pytest
from django.contrib.auth.models import User

from tests.test_base import GraphQLTestCase

pytestmark = pytest.mark.django_db


class IntegrationTests(GraphQLTestCase):
    """Integration tests that test complete workflows (marked as integration)."""

    def test_complete_post_interaction_workflow(self):
        """Test creating post, liking, commenting, and sharing end-to-end."""
        create_mutation = """
        mutation {
            createPost(content: "Integration test post") {
                success
                post {
                    id
                    content
                    likesCount
                    commentsCount
                }
            }
        }
        """

        django_client = self._get_authenticated_client(self.user1)
        response = django_client.post(
            "/graphql/",
            data=json.dumps({"query": create_mutation}),
            content_type="application/json",
        )
        assert response.status_code == 200, response.content
        result = response.json()
        assert result.get("errors") is None, result
        post_id = int(result["data"]["createPost"]["post"]["id"])

        like_mutation = """
        mutation($postId: Int!) {
            likePost(postId: $postId) {
                success
                isLiked
            }
        }
        """
        django_client = self._get_authenticated_client(self.user2)
        response = django_client.post(
            "/graphql/",
            data=json.dumps({"query": like_mutation, "variables": {"postId": post_id}}),
            content_type="application/json",
        )
        assert response.status_code == 200, response.content
        result = response.json()
        assert result.get("errors") is None, result
        assert result["data"]["likePost"]["success"] is True
        assert result["data"]["likePost"]["isLiked"] is True

        comment_mutation = """
        mutation($postId: Int!) {
            createComment(postId: $postId, content: "Great post!") {
                success
                comment {
                    content
                    author {
                        username
                    }
                }
            }
        }
        """
        response = django_client.post(
            "/graphql/",
            data=json.dumps(
                {"query": comment_mutation, "variables": {"postId": post_id}}
            ),
            content_type="application/json",
        )
        assert response.status_code == 200, response.content
        result = response.json()
        assert result["data"]["createComment"]["success"] is True
        assert result["data"]["createComment"]["comment"]["content"] == "Great post!"

        share_mutation = """
        mutation($postId: Int!) {
            sharePost(postId: $postId) {
                success
            }
        }
        """
        response = django_client.post(
            "/graphql/",
            data=json.dumps(
                {"query": share_mutation, "variables": {"postId": post_id}}
            ),
            content_type="application/json",
        )
        assert response.status_code == 200, response.content
        result = response.json()
        assert result["data"]["sharePost"]["success"] is True

        verify_query = """
        query($postId: Int!) {
            post(id: $postId) {
                content
                likesCount
                commentsCount
                author {
                    username
                }
            }
        }
        """
        django_client = self._get_authenticated_client(self.user1)
        response = django_client.post(
            "/graphql/",
            data=json.dumps({"query": verify_query, "variables": {"postId": post_id}}),
            content_type="application/json",
        )
        assert response.status_code == 200, response.content
        result = response.json()
        post_data = result["data"]["post"]
        assert post_data["content"] == "Integration test post"
        assert post_data["author"]["username"] == self.user1.username

    def test_user_registration_and_profile_workflow(self):
        """Test complete user registration with OTP verification in a controlled way."""
        # Use a unique email to avoid clashes across tests
        email = "newuser_integration@test.com"

        register_mutation = f"""
        mutation {{
            registerUser(
                username: "newuser_integration",
                email: "{email}",
                password: "securepass123",
                firstName: "New",
                lastName: "User",
                bio: "New user bio"
            ) {{
                success
                message
            }}
        }}
        """

        django_client = self._get_authenticated_client(self.user1)
        response = django_client.post(
            "/graphql/",
            data=json.dumps({"query": register_mutation}),
            content_type="application/json",
        )
        assert response.status_code == 200, response.content
        result = response.json()
        assert result.get("errors") is None, result

        from apps.users.models import OTP

        # OTP created by registration flow should exist
        otp_obj = OTP.objects.filter(email=email).first()
        assert otp_obj is not None

        # Simulate generating a known OTP code and verifying it
        otp_obj.delete()
        new_otp, known_code = OTP.create_for_email(
            email=email,
            data={
                "username": "newuser_integration",
                "email": email,
                "password": "securepass123",
                "first_name": "New",
                "last_name": "User",
                "bio": "New user bio",
            },
        )

        verify_mutation = """
        mutation($email: String!, $otpCode: String!) {
            verifyEmailOtp(email: $email, otpCode: $otpCode) {
                success
                message
                user {
                    username
                    firstName
                    lastName
                }
            }
        }
        """
        response = django_client.post(
            "/graphql/",
            data=json.dumps(
                {
                    "query": verify_mutation,
                    "variables": {"email": email, "otpCode": known_code},
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 200, response.content
        result = response.json()
        assert result["data"]["verifyEmailOtp"]["success"] is True
        user_data = result["data"]["verifyEmailOtp"]["user"]
        assert user_data["username"] == "newuser_integration"
        assert user_data["firstName"] == "New"

        new_user = User.objects.get(username="newuser_integration")
        assert new_user.email == email
        assert hasattr(new_user, "profile")
        assert new_user.profile.bio == "New user bio"

    def test_follow_unfollow_workflow(self):
        """Test following and unfollowing users with count updates."""
        follow_mutation = """
        mutation($userId: Int!) {
            followUser(userId: $userId) {
                success
                message
            }
        }
        """

        django_client = self._get_authenticated_client(self.user1)
        response = django_client.post(
            "/graphql/",
            data=json.dumps(
                {"query": follow_mutation, "variables": {"userId": self.user2.id}}
            ),
            content_type="application/json",
        )
        assert response.status_code == 200, response.content
        result = response.json()
        assert result["data"]["followUser"]["success"] is True

        follow_check_query = """
        query($userId: Int!) {
            isFollowing(userId: $userId)
            followersCount(userId: $userId)
            followingCount(userId: $userId)
        }
        """
        response = django_client.post(
            "/graphql/",
            data=json.dumps(
                {"query": follow_check_query, "variables": {"userId": self.user2.id}}
            ),
            content_type="application/json",
        )
        assert response.status_code == 200, response.content
        result = response.json()
        assert result["data"]["isFollowing"] is True
        assert result["data"]["followersCount"] == 1

        response = django_client.post(
            "/graphql/",
            data=json.dumps(
                {"query": follow_check_query, "variables": {"userId": self.user1.id}}
            ),
            content_type="application/json",
        )
        assert response.status_code == 200, response.content
        result = response.json()
        assert result.get("errors") is None
        assert result["data"]["followingCount"] == 1

        unfollow_mutation = """
        mutation($userId: Int!) {
            unfollowUser(userId: $userId) {
                success
                message
            }
        }
        """
        response = django_client.post(
            "/graphql/",
            data=json.dumps(
                {"query": unfollow_mutation, "variables": {"userId": self.user2.id}}
            ),
            content_type="application/json",
        )
        assert response.status_code == 200, response.content
        result = response.json()
        assert result.get("errors") is None
        assert result["data"]["unfollowUser"]["success"] is True

        response = django_client.post(
            "/graphql/",
            data=json.dumps(
                {"query": follow_check_query, "variables": {"userId": self.user2.id}}
            ),
            content_type="application/json",
        )
        assert response.status_code == 200, response.content
        result = response.json()
        assert result["data"]["isFollowing"] is False
        assert result["data"]["followersCount"] == 0
