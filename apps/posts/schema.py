import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth.models import User
from .models import Post
from utils.pagination import paginate_queryset


class PostType(DjangoObjectType):
    class Meta:
        model = Post
        fields = "__all__"


class PostPaginationType(graphene.ObjectType):
    items = graphene.List(PostType)
    total_items = graphene.Int()
    total_pages = graphene.Int()
    current_page = graphene.Int()


class PostQuery(graphene.ObjectType):
    all_posts = graphene.Field(
        PostPaginationType,
        page=graphene.Int(required=False),
        items_per_page=graphene.Int(required=False),
    )
    post = graphene.Field(PostType, id=graphene.Int(required=True))
    posts_by_user = graphene.Field(
        PostPaginationType,
        user_id=graphene.Int(required=True),
        page=graphene.Int(required=False),
        items_per_page=graphene.Int(required=False),
    )

    def resolve_all_posts(self, info, page=1, items_per_page=10):
        qs = Post.objects.filter(is_active=True).order_by("-created_at")
        data = paginate_queryset(qs, page, items_per_page)
        return PostPaginationType(**data)

    def resolve_post(self, info, id):
        try:
            return Post.objects.get(pk=id, is_active=True)
        except Post.DoesNotExist:
            return None

    def resolve_posts_by_user(self, info, user_id, page=1, items_per_page=10):
        qs = Post.objects.filter(author_id=user_id, is_active=True).order_by(
            "-created_at"
        )
        data = paginate_queryset(qs, page, items_per_page)
        return PostPaginationType(**data)


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
