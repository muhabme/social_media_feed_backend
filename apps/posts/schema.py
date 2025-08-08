import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth.models import User
from .models import Post


class PostType(DjangoObjectType):
    class Meta:
        model = Post
        fields = "__all__"


class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", "date_joined")


class PostQuery(graphene.ObjectType):
    all_posts = graphene.List(PostType)
    post = graphene.Field(PostType, id=graphene.Int(required=True))
    posts_by_user = graphene.List(PostType, user_id=graphene.Int(required=True))

    def resolve_all_posts(self, info):
        return Post.objects.filter(is_active=True).order_by("-created_at")

    def resolve_post(self, info, id):
        try:
            return Post.objects.get(pk=id, is_active=True)
        except Post.DoesNotExist:
            return None

    def resolve_posts_by_user(self, info, user_id):
        return Post.objects.filter(author_id=user_id, is_active=True).order_by(
            "-created_at"
        )


class CreatePost(graphene.Mutation):
    class Arguments:
        content = graphene.String(required=True)
        image_url = graphene.String(required=False)

    post = graphene.Field(PostType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, content, image_url=None):
        user = info.context.user

        if not user.is_authenticated:
            raise Exception("Authentication required")

        try:
            post = Post.objects.create(author=user, content=content)
            return CreatePost(
                post=post, success=True, message="Post created successfully!"
            )
        except Exception as e:
            return CreatePost(
                post=None, success=False, message=f"Error creating post: {str(e)}"
            )


class UpdatePost(graphene.Mutation):
    class Arguments:
        post_id = graphene.Int(required=True)
        content = graphene.String(required=True)

    post = graphene.Field(PostType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, post_id, content):
        try:
            post = Post.objects.get(pk=post_id, is_active=True)
            post.content = content
            post.save()

            return UpdatePost(
                post=post, success=True, message="Post updated successfully!"
            )
        except Post.DoesNotExist:
            return UpdatePost(post=None, success=False, message="Post not found")


class DeletePost(graphene.Mutation):
    class Arguments:
        post_id = graphene.Int(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, post_id):
        try:
            post = Post.objects.get(pk=post_id, is_active=True)
            post.is_active = False  # Soft delete
            post.save()

            return DeletePost(success=True, message="Post deleted successfully!")
        except Post.DoesNotExist:
            return DeletePost(success=False, message="Post not found")


class PostMutation(graphene.ObjectType):
    create_post = CreatePost.Field()
    update_post = UpdatePost.Field()
    delete_post = DeletePost.Field()
