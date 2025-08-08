from django.db import models
from django.contrib.auth.models import User
from apps.core.models import TimeStampedModel
from apps.posts.models import Post


class Like(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="likes")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")

    class Meta:
        db_table = "likes"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "post"], name="unique_like_per_user_post"
            ),
        ]
        indexes = [models.Index(fields=["post", "user"])]

    def __str__(self):
        return f"{self.user.username} liked post {self.post_id}"


class Comment(TimeStampedModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="replies"
    )

    class Meta:
        db_table = "comments"
        indexes = [models.Index(fields=["post", "created_at"])]

    def __str__(self):
        return f"Comment {self.pk} on post {self.post_id}"


class Share(TimeStampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shares")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="shares")

    class Meta:
        db_table = "shares"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "post"], name="unique_share_per_user_post"
            ),
        ]
        indexes = [models.Index(fields=["post", "user"])]

    def __str__(self):
        return f"{self.user.username} shared post {self.post_id}"
