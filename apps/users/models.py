import hashlib
import hmac
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel

SECRET = settings.SECRET_KEY.encode()


class Role(TimeStampedModel):
    name = models.CharField(max_length=50, unique=True, db_index=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "roles"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Permission(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True, db_index=True)
    codename = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField(blank=True)
    resource = models.CharField(max_length=50, db_index=True)
    action = models.CharField(max_length=50, db_index=True)

    class Meta:
        db_table = "permissions"
        indexes = [
            models.Index(fields=["resource", "action"]),
        ]
        ordering = ["resource", "action"]

    def __str__(self):
        return f"{self.resource}:{self.action}"


class RolePermission(TimeStampedModel):
    role = models.ForeignKey(
        Role, on_delete=models.CASCADE, related_name="role_permissions"
    )
    permission = models.ForeignKey(
        Permission, on_delete=models.CASCADE, related_name="role_permissions"
    )

    class Meta:
        db_table = "role_permissions"
        constraints = [
            models.UniqueConstraint(
                fields=["role", "permission"], name="unique_role_permission"
            )
        ]
        indexes = [
            models.Index(fields=["role", "permission"]),
        ]

    def __str__(self):
        return f"{self.role.name} - {self.permission.codename}"


class UserProfile(TimeStampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    bio = models.TextField(max_length=500, blank=True)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)
    role = models.ForeignKey(
        Role, on_delete=models.PROTECT, related_name="users", null=True, blank=True
    )

    class Meta:
        db_table = "user_profiles"

    def __str__(self):
        return f"profile:{self.user.username}"

    def has_permission(self, permission_codename):
        if not self.role or not self.role.is_active:
            return False

        return (
            self.role.role_permissions.select_related("permission")
            .filter(permission__codename=permission_codename)
            .exists()
        )

    def get_permissions(self):
        if not self.role or not self.role.is_active:
            return Permission.objects.none()
        return Permission.objects.filter(role_permissions__role=self.role)


class Follow(TimeStampedModel):
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following_relationships",
        db_index=True,
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower_relationships",
        db_index=True,
    )

    class Meta:
        db_table = "follows"
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "following"], name="unique_follow"
            ),
            models.CheckConstraint(
                check=~models.Q(follower=models.F("following")), name="no_self_follow"
            ),
        ]
        indexes = [
            models.Index(fields=["follower", "following"]),
        ]

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


class OTP(TimeStampedModel):
    email = models.EmailField(db_index=True)
    otp_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=5)
    used = models.BooleanField(default=False)
    data = models.JSONField(blank=True, null=True)

    class Meta:
        db_table = "otps"
        indexes = [models.Index(fields=["email", "created_at"])]

    OTP_TTL_MINUTES = 10

    @classmethod
    def _hash_otp(cls, otp: str):
        return hmac.new(SECRET, otp.encode(), hashlib.sha256).hexdigest()

    @classmethod
    def generate_code(cls):
        return f"{secrets.randbelow(900000) + 100000:06d}"

    @classmethod
    def create_for_email(cls, email: str, data=None, max_attempts: int = 5):
        code = cls.generate_code()
        obj = cls.objects.create(
            email=email,
            otp_hash=cls._hash_otp(code),
            attempts=0,
            max_attempts=max_attempts,
            data=data or {},
        )
        return obj, code

    def is_expired(self):
        return timezone.now() > (
            self.created_at + timedelta(minutes=self.OTP_TTL_MINUTES)
        )

    def verify(self, otp_input: str):
        if self.used:
            return False, "already_used"
        if self.attempts >= self.max_attempts:
            return False, "max_attempts"
        if self.is_expired():
            return False, "expired"
        ok = hmac.compare_digest(self.otp_hash, self._hash_otp(otp_input))
        self.attempts = models.F("attempts") + 1
        if ok:
            self.used = True
        self.save(update_fields=["attempts", "used"])
        self.refresh_from_db(fields=["attempts", "used"])
        return ok, "ok" if ok else "invalid"
