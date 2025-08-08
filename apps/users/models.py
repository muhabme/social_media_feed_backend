from django.contrib.auth.models import User
from django.db import models
from apps.core.models import TimeStampedModel


class UserProfile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True)

    class Meta:
        db_table = "user_profiles"


class Follow(TimeStampedModel):
    follower = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="following_relationships"
    )
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="follower_relationships"
    )

    class Meta:
        db_table = "follows"
        unique_together = ("follower", "following")

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"
