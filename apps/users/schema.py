import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from .models import UserProfile
import graphql_jwt
from utils.pagination import paginate_queryset


class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "date_joined")


class UserPaginationType(graphene.ObjectType):
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
                followers_count=profile.followers_count if profile else 0,
                following_count=profile.following_count if profile else 0,
                date_joined=user.date_joined,
            )
        except User.DoesNotExist:
            return None


class CreateUser(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)
        first_name = graphene.String(required=False)
        last_name = graphene.String(required=False)
        bio = graphene.String(required=False)

    user = graphene.Field(UserType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(
        self, info, username, email, password, first_name="", last_name="", bio=""
    ):
        try:
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                return CreateUser(
                    user=None, success=False, message="Username already exists"
                )

            if User.objects.filter(email=email).exists():
                return CreateUser(
                    user=None, success=False, message="Email already exists"
                )

            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )

            # Create user profile
            UserProfile.objects.create(user=user, bio=bio)

            return CreateUser(
                user=user, success=True, message="User created successfully!"
            )

        except Exception as e:
            return CreateUser(
                user=None, success=False, message=f"Error creating user: {str(e)}"
            )


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


class UserMutation(graphene.ObjectType):
    create_user = CreateUser.Field()  # Register
    token_auth = ObtainJSONWebToken.Field()  # Login
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()
    logout_user = LogoutUser.Field()
    update_user_profile = UpdateUserProfile.Field()
