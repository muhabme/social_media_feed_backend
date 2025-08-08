from django.db import models
from django.contrib.auth.models import User
from apps.core.models import TimeStampedModel


class Post(TimeStampedModel):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="posts", db_index=True
    )
    content = models.TextField()
    image = models.ImageField(upload_to="posts/", blank=True, null=True)
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)
    shares_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "posts"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["author", "created_at"]),
            models.Index(fields=["is_active", "created_at"]),
        ]

    def __str__(self):
        return f"Post {self.pk} by {self.author.username}"
