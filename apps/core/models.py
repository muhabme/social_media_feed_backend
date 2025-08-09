from django.db import models
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ActivityLog(TimeStampedModel):
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="activity_logs",
        db_index=True,
    )

    action = models.CharField(max_length=100, db_index=True)
    resource = models.CharField(max_length=50, db_index=True)

    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")

    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    user_agent = models.TextField(blank=True)

    execution_time_ms = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = "activity_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["action", "created_at"]),
            models.Index(fields=["resource", "created_at"]),
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["ip_address", "created_at"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        username = self.user.username if self.user else "Anonymous"
        return f"{username} {self.action} {self.resource} at {self.created_at}"

    @classmethod
    def log_activity(
        cls,
        user,
        action,
        resource,
        content_object=None,
        description="",
        metadata=None,
        request=None,
    ):
        """
        Convenience method to create activity log entries
        """
        log_data = {
            "user": user,
            "action": action,
            "resource": resource,
            "description": description,
            "metadata": metadata or {},
        }

        if content_object:
            log_data["content_object"] = content_object

        if request:
            log_data["ip_address"] = cls._get_client_ip(request)
            log_data["user_agent"] = request.META.get("HTTP_USER_AGENT", "")[:500]

        return cls.objects.create(**log_data)

    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
