import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from .models import UserProfile, OTP, Follow, Role
import graphql_jwt
from utils.pagination import paginate_queryset
from graphql_jwt.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from utils.monitoring import monitor_performance
from apps.core.decorators import (
    require_permission,
    require_admin,
    require_self_or_admin,
)
from apps.core.permissions import Permissions
from apps.core.models import ActivityLog


class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "date_joined")


class UserPaginationType(graphene.ObjectType):
    items = graphene.List(UserType)
    total_items = graphene.Int()
    total_pages = graphene.Int()
    current_page = graphene.Int()


class FollowPaginationType(graphene.ObjectType):
    items = graphene.List(UserType)
    total_items = graphene.Int()
    total_pages = graphene.Int()
    current_page = graphene.Int()


class UserProfileType(DjangoObjectType):
    class Meta:
        model = UserProfile
        fields = "__all__"


class UserWithProfileType(graphene.ObjectType):
    """Combined user and profile information"""

    id = graphene.Int()
    username = graphene.String()
    email = graphene.String()
    first_name = graphene.String()
    last_name = graphene.String()
    bio = graphene.String()
    followers_count = graphene.Int()
    following_count = graphene.Int()
    date_joined = graphene.DateTime()


class UserQuery(graphene.ObjectType):
    me = graphene.Field(UserType)
    user = graphene.Field(UserType, id=graphene.Int(), username=graphene.String())
    all_users = graphene.Field(
        UserPaginationType,
        page=graphene.Int(required=False),
        items_per_page=graphene.Int(required=False),
    )
    user_profile = graphene.Field(UserProfileType, user_id=graphene.Int(required=True))
    user_with_profile = graphene.Field(
        UserWithProfileType, user_id=graphene.Int(required=True)
    )

    @login_required
    @monitor_performance("me")
    @require_permission(Permissions.USER_READ, resource="user", log_activity=True)
    def resolve_me(self, info):
        user = info.context.user
        if user.is_authenticated:
            return user
        return None

    @monitor_performance("user")
    @login_required
    @require_permission(Permissions.USER_READ, resource="user", log_activity=True)
    def resolve_user(self, info, id=None, username=None):
        try:
            if id:
                return User.objects.get(pk=id)
            elif username:
                return User.objects.get(username=username)
            return None
        except User.DoesNotExist:
            return None

    @monitor_performance("all_users")
    @login_required
    @require_permission(Permissions.USER_READ, resource="user", log_activity=True)
    def resolve_all_users(self, info, page=1, items_per_page=10):
        qs = User.objects.filter(is_active=True).order_by("-created_at")
        data = paginate_queryset(qs, page, items_per_page)
        return UserPaginationType(**data)

    @monitor_performance("user_profile")
    @login_required
    @require_permission(Permissions.USER_READ, resource="user", log_activity=True)
    def resolve_user_profile(self, info, user_id):
        try:
            return UserProfile.objects.get(user_id=user_id)
        except UserProfile.DoesNotExist:
            return None

    @monitor_performance("user_with_profile")
    @login_required
    @require_permission(Permissions.USER_READ, resource="user", log_activity=True)
    def resolve_user_with_profile(self, info, user_id):
        try:
            user = (
                User.objects.filter(pk=user_id)
                .select_related("profile")
                .annotate(
                    followers_count=Count("follower_relationships", distinct=True),
                    following_count=Count("following_relationships", distinct=True),
                )
                .first()
            )
            if not user:
                return None

            return UserWithProfileType(
                id=user.id,
                username=user.username,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                bio=(user.profile.bio if hasattr(user, "profile") else ""),
                followers_count=user.followers_count,
                following_count=user.following_count,
                date_joined=user.date_joined,
            )
        except User.DoesNotExist:
            return None


class FollowQuery(graphene.ObjectType):
    followers = graphene.Field(
        FollowPaginationType,
        user_id=graphene.Int(required=True),
        page=graphene.Int(required=False),
        items_per_page=graphene.Int(required=False),
    )
    following = graphene.Field(
        FollowPaginationType,
        user_id=graphene.Int(required=True),
        page=graphene.Int(required=False),
        items_per_page=graphene.Int(required=False),
    )
    is_following = graphene.Boolean(user_id=graphene.Int(required=True))
    followers_count = graphene.Int(user_id=graphene.Int(required=True))
    following_count = graphene.Int(user_id=graphene.Int(required=True))

    @monitor_performance("followers")
    @login_required
    @require_permission(Permissions.USER_READ, resource="user", log_activity=True)
    def resolve_followers(self, info, user_id, page=1, items_per_page=10):
        qs = User.objects.filter(
            id__in=Follow.objects.filter(following_id=user_id).values_list(
                "follower_id", flat=True
            )
        ).order_by("-date_joined")
        data = paginate_queryset(qs, page, items_per_page)
        return FollowPaginationType(**data)

    @monitor_performance("following")
    @login_required
    @require_permission(Permissions.USER_READ, resource="user", log_activity=True)
    def resolve_following(self, info, user_id, page=1, items_per_page=10):
        qs = User.objects.filter(
            id__in=Follow.objects.filter(follower_id=user_id).values_list(
                "following_id", flat=True
            )
        ).order_by("-date_joined")
        data = paginate_queryset(qs, page, items_per_page)
        return FollowPaginationType(**data)

    @monitor_performance("is_following")
    @login_required
    @require_permission(Permissions.USER_READ, resource="user", log_activity=True)
    def resolve_is_following(self, info, user_id):
        current_user = info.context.user
        if not current_user.is_authenticated:
            return False
        return Follow.objects.filter(
            follower=current_user, following_id=user_id
        ).exists()

    @monitor_performance("followers_count")
    @login_required
    @require_permission(Permissions.USER_READ, resource="user", log_activity=True)
    def resolve_followers_count(self, info, user_id):
        return Follow.objects.filter(following_id=user_id).count()

    @monitor_performance("following_count")
    @login_required
    @require_permission(Permissions.USER_READ, resource="user", log_activity=True)
    def resolve_following_count(self, info, user_id):
        return Follow.objects.filter(follower_id=user_id).count()


class ActivityLogType(DjangoObjectType):
    class Meta:
        model = ActivityLog
        fields = "__all__"


class ActivityLogPaginationType(graphene.ObjectType):
    items = graphene.List(ActivityLogType)
    total_items = graphene.Int()
    total_pages = graphene.Int()
    current_page = graphene.Int()


class AdminQuery(graphene.ObjectType):
    activity_logs = graphene.Field(
        ActivityLogPaginationType,
        user_id=graphene.Int(required=False),
        page=graphene.Int(required=False),
        items_per_page=graphene.Int(required=False),
    )

    @monitor_performance("activity_logs")
    @login_required
    @require_admin(log_activity=True)
    def resolve_activity_logs(self, info, user_id=None, page=1, items_per_page=10):
        qs = ActivityLog.objects.all()
        if user_id is not None:
            qs = qs.filter(user_id=user_id)
        qs = qs.order_by("-created_at")
        data = paginate_queryset(qs, page, items_per_page)
        return ActivityLogPaginationType(**data)


class UpdateUserProfile(graphene.Mutation):
    class Arguments:
        user_id = graphene.Int(required=True)
        bio = graphene.String(required=False)
        first_name = graphene.String(required=False)
        last_name = graphene.String(required=False)

    user = graphene.Field(UserType)
    profile = graphene.Field(UserProfileType)
    success = graphene.Boolean()
    message = graphene.String()

    @monitor_performance("update_user_profile")
    @login_required
    @require_self_or_admin(user_field="user_id", log_activity=True)
    def mutate(self, info, user_id, bio=None, first_name=None, last_name=None):
        try:
            user = User.objects.get(pk=user_id)

            # Update user fields if provided
            if first_name is not None:
                user.first_name = first_name
            if last_name is not None:
                user.last_name = last_name
            user.save()

            # Update or create profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            if bio is not None:
                profile.bio = bio
                profile.save()

            return UpdateUserProfile(
                user=user,
                profile=profile,
                success=True,
                message="Profile updated successfully!",
            )

        except User.DoesNotExist:
            return UpdateUserProfile(
                user=None, profile=None, success=False, message="User not found"
            )
        except Exception as e:
            return UpdateUserProfile(
                user=None,
                profile=None,
                success=False,
                message=f"Error updating profile: {str(e)}",
            )


class UserMutation(graphene.ObjectType):
    update_user_profile = UpdateUserProfile.Field()


class FollowUser(graphene.Mutation):
    class Arguments:
        user_id = graphene.Int(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @monitor_performance("follow_user")
    @login_required
    @require_permission(Permissions.FOLLOW_CREATE, resource="follow", log_activity=True)
    def mutate(self, info, user_id):
        current_user = info.context.user

        if current_user.id == user_id:
            return FollowUser(success=False, message="You cannot follow yourself")

        target_user = User.objects.filter(id=user_id).first()
        if not target_user:
            return FollowUser(success=False, message="User not found")

        obj, created = Follow.objects.get_or_create(
            follower=current_user, following=target_user
        )
        if not created:
            return FollowUser(success=False, message="Already following this user")

        return FollowUser(success=True, message="Followed successfully")


class UnfollowUser(graphene.Mutation):
    class Arguments:
        user_id = graphene.Int(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @monitor_performance("unfollow_user")
    @login_required
    @require_permission(Permissions.FOLLOW_DELETE, resource="follow", log_activity=True)
    def mutate(self, info, user_id):
        current_user = info.context.user

        deleted, _ = Follow.objects.filter(
            follower=current_user, following_id=user_id
        ).delete()

        if deleted:
            return UnfollowUser(success=True, message="Unfollowed successfully")
        return UnfollowUser(success=False, message="You are not following this user")


class FollowMutation(graphene.ObjectType):
    follow_user = FollowUser.Field()
    unfollow_user = UnfollowUser.Field()


class RegisterUser(graphene.Mutation):
    user = graphene.Field(UserType)
    success = graphene.Boolean()
    message = graphene.String()

    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        first_name = graphene.String()
        last_name = graphene.String()
        bio = graphene.String()

    @monitor_performance("register_user")
    def mutate(
        self, info, username, email, password, first_name="", last_name="", bio=""
    ):
        if User.objects.filter(username=username).exists():
            return RegisterUser(success=False, message="Username already exists")
        if User.objects.filter(email=email).exists():
            return RegisterUser(success=False, message="Email already exists")

        now = timezone.now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        otp_count_today = OTP.objects.filter(
            email=email, created_at__gte=start_of_day
        ).count()
        if otp_count_today >= 3:
            return RegisterUser(
                success=False, message="Maximum OTP requests reached for today"
            )

        last_otp = OTP.objects.filter(email=email).order_by("-created_at").first()
        if last_otp and (now - last_otp.created_at) < timedelta(minutes=10):
            return RegisterUser(
                success=False, message="Please wait before requesting another OTP"
            )

        # Use new method to create OTP and get the plaintext code to send via email
        otp_obj, otp_code = OTP.create_for_email(
            email=email,
            data={
                "username": username,
                "email": email,
                "password": password,
                "first_name": first_name,
                "last_name": last_name,
                "bio": bio,
            },
            max_attempts=5,
        )

        send_mail(
            subject="Your OTP Code",
            message=f"Your verification code is {otp_code}. It will expire in 10 minutes.",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )

        return RegisterUser(success=True, message="OTP sent to your email.")


class VerifyEmailOTP(graphene.Mutation):
    success = graphene.Boolean()
    message = graphene.String()
    user = graphene.Field(UserType)

    class Arguments:
        email = graphene.String(required=True)
        otp_code = graphene.String(required=True)

    @monitor_performance("verify_email_otp")
    def mutate(self, info, email, otp_code):
        otp_entry = (
            OTP.objects.filter(email=email, used=False).order_by("-created_at").first()
        )
        if not otp_entry:
            return VerifyEmailOTP(success=False, message="Invalid or expired OTP")

        if otp_entry.is_expired():
            otp_entry.delete()
            return VerifyEmailOTP(success=False, message="OTP expired")

        is_valid, status = otp_entry.verify(otp_code)
        if not is_valid:
            if status == "already_used":
                return VerifyEmailOTP(success=False, message="OTP already used")
            if status == "max_attempts":
                return VerifyEmailOTP(
                    success=False, message="Maximum verification attempts reached"
                )
            if status == "expired":
                return VerifyEmailOTP(success=False, message="OTP expired")
            return VerifyEmailOTP(success=False, message="Invalid OTP")

        # OTP valid: create user and profile
        data = otp_entry.data
        try:
            user = User.objects.create_user(
                username=data["username"],
                email=data["email"],
                password=data["password"],
                first_name=data.get("first_name", ""),
                last_name=data.get("last_name", ""),
            )
            UserProfile.objects.create(
                user=user,
                bio=data.get("bio", ""),
                role=Role.objects.filter(name="user").first(),
            )
            otp_entry.delete()
            return VerifyEmailOTP(
                success=True, message="User created successfully!", user=user
            )
        except Exception as e:
            return VerifyEmailOTP(
                success=False, message=f"Error creating user: {str(e)}"
            )


class ObtainJSONWebToken(graphql_jwt.JSONWebTokenMutation):
    user = graphene.Field(UserType)

    @classmethod
    def resolve(cls, root, info, **kwargs):
        return cls(user=info.context.user)


class LogoutUser(graphene.Mutation):
    success = graphene.Boolean()

    @monitor_performance("logout_user")
    def mutate(self, info):
        request = info.context
        request.session.flush()
        return LogoutUser(success=True)


class AuthMutation(graphene.ObjectType):
    register_user = RegisterUser.Field()  # Register
    verify_email_otp = VerifyEmailOTP.Field()  # Verify email to complete registration

    token_auth = ObtainJSONWebToken.Field()  # Login
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()

    logout_user = LogoutUser.Field()
