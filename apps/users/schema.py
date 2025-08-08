import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from .models import UserProfile, OTP, Follow
import graphql_jwt
from utils.pagination import paginate_queryset
from graphql_jwt.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "date_joined")


class UserPaginationType(graphene.ObjectType):
    items = graphene.List(UserType)
    total_items = graphene.Int()
    total_pages = graphene.Int()
    current_page = graphene.Int()


class FollowType(DjangoObjectType):
    class Meta:
        model = Follow
        fields = "__all__"


class FollowPaginationType(graphene.ObjectType):
    items = graphene.List(FollowType)
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

    def resolve_me(self, info):
        user = info.context.user
        if user.is_authenticated:
            return user
        return None

    def resolve_user(self, info, id=None, username=None):
        try:
            if id:
                return User.objects.get(pk=id)
            elif username:
                return User.objects.get(username=username)
            return None
        except User.DoesNotExist:
            return None

    def resolve_all_users(self, info, page=1, items_per_page=10):
        qs = User.objects.filter(is_active=True).order_by("-created_at")
        data = paginate_queryset(qs, page, items_per_page)
        return UserPaginationType(**data)

    def resolve_user_profile(self, info, user_id):
        try:
            return UserProfile.objects.get(user_id=user_id)
        except UserProfile.DoesNotExist:
            return None

    def resolve_user_with_profile(self, info, user_id):
        try:
            user = User.objects.get(pk=user_id)
            profile = UserProfile.objects.filter(user=user).first()

            return UserWithProfileType(
                id=user.id,
                username=user.username,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                bio=profile.bio if profile else "",
                followers_count=Follow.objects.filter(following_id=user.id).count(),
                following_count=Follow.objects.filter(follower_id=user.id).count(),
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

    def resolve_followers(self, info, user_id, page=1, items_per_page=10):
        qs = User.objects.filter(
            id__in=Follow.objects.filter(following_id=user_id).values_list(
                "follower_id", flat=True
            )
        ).order_by("-date_joined")
        data = paginate_queryset(qs, page, items_per_page)
        return FollowPaginationType(**data)

    def resolve_following(self, info, user_id, page=1, items_per_page=10):
        qs = User.objects.filter(
            id__in=Follow.objects.filter(follower_id=user_id).values_list(
                "following_id", flat=True
            )
        ).order_by("-date_joined")
        data = paginate_queryset(qs, page, items_per_page)
        return FollowPaginationType(**data)

    def resolve_is_following(self, info, user_id):
        current_user = info.context.user
        if not current_user.is_authenticated:
            return False
        return Follow.objects.filter(
            follower=current_user, following_id=user_id
        ).exists()

    def resolve_followers_count(self, info, user_id):
        return Follow.objects.filter(following_id=user_id).count()

    def resolve_following_count(self, info, user_id):
        return Follow.objects.filter(follower_id=user_id).count()


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

    @login_required
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

    @login_required
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

    def mutate(
        self, info, username, email, password, first_name="", last_name="", bio=""
    ):
        # Check existing user by username/email (your existing checks)
        if User.objects.filter(username=username).exists():
            return RegisterUser(success=False, message="Username already exists")
        if User.objects.filter(email=email).exists():
            return RegisterUser(success=False, message="Email already exists")

        now = timezone.now()

        # 1. Check OTPs sent today (from midnight to now)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        otp_count_today = OTP.objects.filter(
            email=email, created_at__gte=start_of_day
        ).count()
        if otp_count_today >= 3:
            return RegisterUser(
                success=False, message="Maximum OTP requests reached for today"
            )

        # 2. Check if last OTP was sent less than 10 minutes ago
        last_otp = OTP.objects.filter(email=email).order_by("-created_at").first()
        if last_otp and (now - last_otp.created_at) < timedelta(minutes=10):
            return RegisterUser(
                success=False,
                message="Please wait a few minutes before requesting another OTP",
            )

        # Generate and create OTP as before
        otp_code = OTP.generate_otp()
        OTP.objects.create(
            email=email,
            otp_code=otp_code,
            data={
                "username": username,
                "email": email,
                "password": password,
                "first_name": first_name,
                "last_name": last_name,
                "bio": bio,
            },
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

    def mutate(self, info, email, otp_code):
        try:
            otp_entry = OTP.objects.filter(email=email, otp_code=otp_code).first()
            if not otp_entry:
                return VerifyEmailOTP(success=False, message="Invalid OTP")

            if otp_entry.is_expired():
                otp_entry.delete()
                return VerifyEmailOTP(success=False, message="OTP expired")

            data = otp_entry.data

            # Create user
            from django.contrib.auth.models import User

            user = User.objects.create_user(
                username=data["username"],
                email=data["email"],
                password=data["password"],
                first_name=data["first_name"],
                last_name=data["last_name"],
            )

            # Create profile
            UserProfile.objects.create(user=user, bio=data["bio"])

            otp_entry.delete()
            return VerifyEmailOTP(
                success=True, message="User created successfully!", user=user
            )

        except Exception as e:
            return VerifyEmailOTP(success=False, message=f"Error: {str(e)}")


class ObtainJSONWebToken(graphql_jwt.JSONWebTokenMutation):
    user = graphene.Field(UserType)

    @classmethod
    def resolve(cls, root, info, **kwargs):
        return cls(user=info.context.user)


class LogoutUser(graphene.Mutation):
    success = graphene.Boolean()

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
