import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth.models import User
from .models import Like, Comment, Share
from apps.posts.models import Post


class LikeType(DjangoObjectType):
    class Meta:
        model = Like
        fields = "__all__"


class CommentType(DjangoObjectType):
    class Meta:
        model = Comment
        fields = "__all__"


class ShareType(DjangoObjectType):
    class Meta:
        model = Share
        fields = "__all__"


class InteractionQuery(graphene.ObjectType):
    # Like queries
    post_likes = graphene.List(LikeType, post_id=graphene.Int(required=True))
    user_likes = graphene.List(LikeType, user_id=graphene.Int(required=True))

    # Comment queries
    post_comments = graphene.List(CommentType, post_id=graphene.Int(required=True))
    user_comments = graphene.List(CommentType, user_id=graphene.Int(required=True))
    comment_replies = graphene.List(CommentType, parent_id=graphene.Int(required=True))

    # Share queries
    post_shares = graphene.List(ShareType, post_id=graphene.Int(required=True))
    user_shares = graphene.List(ShareType, user_id=graphene.Int(required=True))

    # Interaction stats
    post_interaction_stats = graphene.Field(
        lambda: InteractionStatsType, post_id=graphene.Int(required=True)
    )

    def resolve_post_likes(self, info, post_id):
        return Like.objects.filter(post_id=post_id).order_by("-created_at")

    def resolve_user_likes(self, info, user_id):
        return Like.objects.filter(user_id=user_id).order_by("-created_at")

    def resolve_post_comments(self, info, post_id):
        return Comment.objects.filter(
            post_id=post_id, parent__isnull=True  # Only top-level comments
        ).order_by("-created_at")

    def resolve_user_comments(self, info, user_id):
        return Comment.objects.filter(author_id=user_id).order_by("-created_at")

    def resolve_comment_replies(self, info, parent_id):
        return Comment.objects.filter(parent_id=parent_id).order_by("created_at")

    def resolve_post_shares(self, info, post_id):
        return Share.objects.filter(post_id=post_id).order_by("-created_at")

    def resolve_user_shares(self, info, user_id):
        return Share.objects.filter(user_id=user_id).order_by("-created_at")

    def resolve_post_interaction_stats(self, info, post_id):
        try:
            post = Post.objects.get(pk=post_id)
            likes_count = Like.objects.filter(post=post).count()
            comments_count = Comment.objects.filter(post=post).count()
            shares_count = Share.objects.filter(post=post).count()

            return InteractionStatsType(
                post_id=post_id,
                likes_count=likes_count,
                comments_count=comments_count,
                shares_count=shares_count,
                total_interactions=likes_count + comments_count + shares_count,
            )
        except Post.DoesNotExist:
            return None


class InteractionStatsType(graphene.ObjectType):
    post_id = graphene.Int()
    likes_count = graphene.Int()
    comments_count = graphene.Int()
    shares_count = graphene.Int()
    total_interactions = graphene.Int()


class LikePost(graphene.Mutation):
    class Arguments:
        post_id = graphene.Int(required=True)

    like = graphene.Field(LikeType)
    success = graphene.Boolean()
    message = graphene.String()
    is_liked = graphene.Boolean()

    def mutate(self, info, post_id):
        user = info.context.user

        # For development, create a test user if not authenticated
        if not user.is_authenticated:
            user, created = User.objects.get_or_create(
                username="testuser",
                defaults={
                    "email": "test@example.com",
                    "first_name": "Test",
                    "last_name": "User",
                },
            )

        try:
            post = Post.objects.get(pk=post_id, is_active=True)

            # Check if already liked
            existing_like = Like.objects.filter(user=user, post=post).first()

            if existing_like:
                # Unlike (remove the like)
                existing_like.delete()
                # Update post's like count
                post.likes_count = Like.objects.filter(post=post).count()
                post.save()

                return LikePost(
                    like=None,
                    success=True,
                    message="Post unliked successfully!",
                    is_liked=False,
                )
            else:
                # Like the post
                like = Like.objects.create(user=user, post=post)
                # Update post's like count
                post.likes_count = Like.objects.filter(post=post).count()
                post.save()

                return LikePost(
                    like=like,
                    success=True,
                    message="Post liked successfully!",
                    is_liked=True,
                )

        except Post.DoesNotExist:
            return LikePost(
                like=None, success=False, message="Post not found", is_liked=False
            )
        except Exception as e:
            return LikePost(
                like=None, success=False, message=f"Error: {str(e)}", is_liked=False
            )


class CreateComment(graphene.Mutation):
    class Arguments:
        post_id = graphene.Int(required=True)
        content = graphene.String(required=True)
        parent_id = graphene.Int(required=False)

    comment = graphene.Field(CommentType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, post_id, content, parent_id=None):
        user = info.context.user

        # For development, create a test user if not authenticated
        if not user.is_authenticated:
            user, created = User.objects.get_or_create(
                username="testuser",
                defaults={
                    "email": "test@example.com",
                    "first_name": "Test",
                    "last_name": "User",
                },
            )

        try:
            post = Post.objects.get(pk=post_id, is_active=True)
            parent = None

            if parent_id:
                parent = Comment.objects.get(pk=parent_id)

            comment = Comment.objects.create(
                author=user, post=post, content=content, parent=parent
            )

            # Update post's comment count
            post.comments_count = Comment.objects.filter(post=post).count()
            post.save()

            return CreateComment(
                comment=comment, success=True, message="Comment created successfully!"
            )

        except Post.DoesNotExist:
            return CreateComment(comment=None, success=False, message="Post not found")
        except Comment.DoesNotExist:
            return CreateComment(
                comment=None, success=False, message="Parent comment not found"
            )
        except Exception as e:
            return CreateComment(
                comment=None, success=False, message=f"Error creating comment: {str(e)}"
            )


class SharePost(graphene.Mutation):
    class Arguments:
        post_id = graphene.Int(required=True)

    share = graphene.Field(ShareType)
    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, post_id):
        user = info.context.user

        # For development, create a test user if not authenticated
        if not user.is_authenticated:
            user, created = User.objects.get_or_create(
                username="testuser",
                defaults={
                    "email": "test@example.com",
                    "first_name": "Test",
                    "last_name": "User",
                },
            )

        try:
            post = Post.objects.get(pk=post_id, is_active=True)

            # Check if already shared
            existing_share = Share.objects.filter(user=user, post=post).first()

            if existing_share:
                return SharePost(
                    share=existing_share, success=True, message="Post already shared!"
                )

            share = Share.objects.create(user=user, post=post)

            # Update post's share count
            post.shares_count = Share.objects.filter(post=post).count()
            post.save()

            return SharePost(
                share=share, success=True, message="Post shared successfully!"
            )

        except Post.DoesNotExist:
            return SharePost(share=None, success=False, message="Post not found")
        except Exception as e:
            return SharePost(
                share=None, success=False, message=f"Error sharing post: {str(e)}"
            )


class DeleteComment(graphene.Mutation):
    class Arguments:
        comment_id = graphene.Int(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    def mutate(self, info, comment_id):
        try:
            comment = Comment.objects.get(pk=comment_id)
            post = comment.post

            comment.delete()

            # Update post's comment count
            post.comments_count = Comment.objects.filter(post=post).count()
            post.save()

            return DeleteComment(success=True, message="Comment deleted successfully!")

        except Comment.DoesNotExist:
            return DeleteComment(success=False, message="Comment not found")


class InteractionMutation(graphene.ObjectType):
    like_post = LikePost.Field()
    create_comment = CreateComment.Field()
    share_post = SharePost.Field()
    delete_comment = DeleteComment.Field()
