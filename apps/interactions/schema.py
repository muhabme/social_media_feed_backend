import graphene
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import F
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required

from apps.core.decorators import require_permission
from apps.core.permissions import Permissions
from apps.posts.models import Post
from utils.monitoring import monitor_performance
from utils.pagination import paginate_queryset

from .models import Comment, Like, Share


class LikeType(DjangoObjectType):
    class Meta:
        model = Like
        fields = "__all__"


class LikePaginationType(graphene.ObjectType):
    items = graphene.List(LikeType)
    total_items = graphene.Int()
    total_pages = graphene.Int()
    current_page = graphene.Int()


class CommentType(DjangoObjectType):
    class Meta:
        model = Comment
        fields = "__all__"


class CommentPaginationType(graphene.ObjectType):
    items = graphene.List(CommentType)
    total_items = graphene.Int()
    total_pages = graphene.Int()
    current_page = graphene.Int()


class ShareType(DjangoObjectType):
    class Meta:
        model = Share
        fields = "__all__"


class SharePaginationType(graphene.ObjectType):
    items = graphene.List(ShareType)
    total_items = graphene.Int()
    total_pages = graphene.Int()
    current_page = graphene.Int()


class InteractionQuery(graphene.ObjectType):
    # Like queries
    post_likes = graphene.Field(
        LikePaginationType,
        post_id=graphene.Int(required=True),
        page=graphene.Int(required=False),
        items_per_page=graphene.Int(required=False),
    )
    user_likes = graphene.Field(
        LikePaginationType,
        user_id=graphene.Int(required=True),
        page=graphene.Int(required=False),
        items_per_page=graphene.Int(required=False),
    )

    # Comment queries
    post_comments = graphene.Field(
        CommentPaginationType,
        post_id=graphene.Int(required=True),
        page=graphene.Int(required=False),
        items_per_page=graphene.Int(required=False),
    )
    user_comments = graphene.Field(
        CommentPaginationType,
        user_id=graphene.Int(required=True),
        page=graphene.Int(required=False),
        items_per_page=graphene.Int(required=False),
    )
    comment_replies = graphene.Field(
        CommentPaginationType,
        parent_id=graphene.Int(required=True),
        page=graphene.Int(required=False),
        items_per_page=graphene.Int(required=False),
    )

    # Share queries
    post_shares = graphene.Field(
        SharePaginationType,
        post_id=graphene.Int(required=True),
        page=graphene.Int(required=False),
        items_per_page=graphene.Int(required=False),
    )
    user_shares = graphene.Field(
        SharePaginationType,
        user_id=graphene.Int(required=True),
        page=graphene.Int(required=False),
        items_per_page=graphene.Int(required=False),
    )

    # Interaction stats
    post_interaction_stats = graphene.Field(
        lambda: InteractionStatsType, post_id=graphene.Int(required=True)
    )

    # Like resolvers
    @monitor_performance("post_likes")
    @require_permission(Permissions.POST_READ, resource="like", log_activity=True)
    def resolve_post_likes(self, info, post_id, page=1, items_per_page=10):
        qs = Like.objects.filter(post_id=post_id).order_by("-created_at")
        data = paginate_queryset(qs, page, items_per_page)
        return LikePaginationType(**data)

    @monitor_performance("user_likes")
    @require_permission(Permissions.USER_READ, resource="user", log_activity=True)
    def resolve_user_likes(self, info, user_id, page=1, items_per_page=10):
        qs = Like.objects.filter(user_id=user_id).order_by("-created_at")
        data = paginate_queryset(qs, page, items_per_page)
        return LikePaginationType(**data)

    # Comment resolvers
    @monitor_performance("post_comments")
    @require_permission(Permissions.COMMENT_READ, resource="comment", log_activity=True)
    def resolve_post_comments(self, info, post_id, page=1, items_per_page=10):
        qs = Comment.objects.filter(post_id=post_id, parent__isnull=True).order_by(
            "-created_at"
        )
        data = paginate_queryset(qs, page, items_per_page)
        return CommentPaginationType(**data)

    @monitor_performance("user_comments")
    @require_permission(Permissions.COMMENT_READ, resource="comment", log_activity=True)
    def resolve_user_comments(self, info, user_id, page=1, items_per_page=10):
        qs = Comment.objects.filter(author_id=user_id).order_by("-created_at")
        data = paginate_queryset(qs, page, items_per_page)
        return CommentPaginationType(**data)

    @monitor_performance("comment_replies")
    @require_permission(Permissions.COMMENT_READ, resource="comment", log_activity=True)
    def resolve_comment_replies(self, info, parent_id, page=1, items_per_page=10):
        qs = Comment.objects.filter(parent_id=parent_id).order_by("created_at")
        data = paginate_queryset(qs, page, items_per_page)
        return CommentPaginationType(**data)

    # Share resolvers
    @monitor_performance("post_shares")
    @require_permission(Permissions.POST_READ, resource="share", log_activity=True)
    def resolve_post_shares(self, info, post_id, page=1, items_per_page=10):
        qs = Share.objects.filter(post_id=post_id).order_by("-created_at")
        data = paginate_queryset(qs, page, items_per_page)
        return SharePaginationType(**data)

    @monitor_performance("user_shares")
    @require_permission(Permissions.USER_READ, resource="user", log_activity=True)
    def resolve_user_shares(self, info, user_id, page=1, items_per_page=10):
        qs = Share.objects.filter(user_id=user_id).order_by("-created_at")
        data = paginate_queryset(qs, page, items_per_page)
        return SharePaginationType(**data)

    # Interaction stats resolver
    @monitor_performance("interaction_stats")
    @require_permission(Permissions.POST_READ, resource="post", log_activity=True)
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

    @login_required
    @monitor_performance("like_post")
    @require_permission(Permissions.LIKE_CREATE, resource="like", log_activity=True)
    def mutate(self, info, post_id):
        user = info.context.user
        try:
            with transaction.atomic():
                post = Post.objects.select_for_update().get(pk=post_id, is_active=True)

                existing = Like.objects.filter(user=user, post=post).first()
                if existing:
                    existing.delete()
                    Post.objects.filter(pk=post.pk).update(
                        likes_count=F("likes_count") - 1
                    )
                    return LikePost(
                        success=True, message="Post unliked", is_liked=False, like=None
                    )

                like = Like.objects.create(user=user, post=post)
                Post.objects.filter(pk=post.pk).update(likes_count=F("likes_count") + 1)
                return LikePost(
                    success=True, message="Post liked", is_liked=True, like=like
                )

        except Post.DoesNotExist:
            return LikePost(
                success=False, message="Post not found", is_liked=False, like=None
            )


class CreateComment(graphene.Mutation):
    class Arguments:
        post_id = graphene.Int(required=True)
        content = graphene.String(required=True)
        parent_id = graphene.Int(required=False)

    comment = graphene.Field(CommentType)
    success = graphene.Boolean()
    message = graphene.String()

    @login_required
    @monitor_performance("create_comment")
    @require_permission(
        Permissions.COMMENT_CREATE, resource="comment", log_activity=True
    )
    def mutate(self, info, post_id, content, parent_id=None):
        user = info.context.user

        try:
            with transaction.atomic():
                post = Post.objects.select_for_update().get(pk=post_id, is_active=True)
                parent = None

                if parent_id:
                    parent = Comment.objects.get(pk=parent_id)

                comment = Comment.objects.create(
                    author=user, post=post, content=content, parent=parent
                )

                Post.objects.filter(pk=post.pk).update(
                    comments_count=F("comments_count") + 1
                )

                return CreateComment(
                    comment=comment,
                    success=True,
                    message="Comment created successfully!",
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


class UpdateComment(graphene.Mutation):
    """New mutation to update comments with ownership check"""

    class Arguments:
        comment_id = graphene.Int(required=True)
        content = graphene.String(required=True)

    comment = graphene.Field(CommentType)
    success = graphene.Boolean()
    message = graphene.String()

    @login_required
    @monitor_performance("update_comment")
    @require_permission(
        Permissions.COMMENT_UPDATE, resource="comment", log_activity=True
    )
    def mutate(self, info, comment_id, content):
        user = info.context.user

        try:
            comment = Comment.objects.get(pk=comment_id)

            # Ownership check: Only comment author can update
            if comment.author != user:
                return UpdateComment(
                    comment=None,
                    success=False,
                    message="You can only update your own comments",
                )

            comment.content = content
            comment.save()

            return UpdateComment(
                comment=comment, success=True, message="Comment updated successfully!"
            )

        except Comment.DoesNotExist:
            return UpdateComment(
                comment=None, success=False, message="Comment not found"
            )
        except Exception as e:
            return UpdateComment(
                comment=None, success=False, message=f"Error updating comment: {str(e)}"
            )


class SharePost(graphene.Mutation):
    class Arguments:
        post_id = graphene.Int(required=True)

    share = graphene.Field(ShareType)
    success = graphene.Boolean()
    message = graphene.String()

    @login_required
    @monitor_performance("share_post")
    @require_permission(Permissions.SHARE_CREATE, resource="share", log_activity=True)
    def mutate(self, info, post_id):
        user = info.context.user

        try:
            with transaction.atomic():
                post = Post.objects.select_for_update().get(pk=post_id, is_active=True)

                # Check if already shared
                existing_share = Share.objects.filter(user=user, post=post).first()

                if existing_share:
                    return SharePost(
                        share=existing_share,
                        success=True,
                        message="Post already shared!",
                    )

                share = Share.objects.create(user=user, post=post)

                Post.objects.filter(pk=post.pk).update(
                    shares_count=F("shares_count") + 1
                )

                return SharePost(
                    share=share, success=True, message="Post shared successfully!"
                )

        except Post.DoesNotExist:
            return SharePost(share=None, success=False, message="Post not found")
        except Exception as e:
            return SharePost(
                share=None, success=False, message=f"Error sharing post: {str(e)}"
            )


class UnsharePost(graphene.Mutation):
    """New mutation to unshare posts with ownership check"""

    class Arguments:
        post_id = graphene.Int(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @login_required
    @monitor_performance("unshare_post")
    @require_permission(Permissions.SHARE_DELETE, resource="share", log_activity=True)
    def mutate(self, info, post_id):
        user = info.context.user

        try:
            with transaction.atomic():
                post = Post.objects.select_for_update().get(pk=post_id, is_active=True)

                share = Share.objects.filter(user=user, post=post).first()

                if not share:
                    return UnsharePost(
                        success=False, message="You haven't shared this post"
                    )

                share.delete()

                Post.objects.filter(pk=post.pk).update(
                    shares_count=F("shares_count") - 1
                )

                return UnsharePost(success=True, message="Post unshared successfully!")

        except Post.DoesNotExist:
            return UnsharePost(success=False, message="Post not found")
        except Exception as e:
            return UnsharePost(success=False, message=f"Error unsharing post: {str(e)}")


class DeleteComment(graphene.Mutation):
    class Arguments:
        comment_id = graphene.Int(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @monitor_performance("delete_comment")
    @login_required
    @require_permission(
        Permissions.COMMENT_DELETE, resource="comment", log_activity=True
    )
    def mutate(self, info, comment_id):
        user = info.context.user

        try:
            comment = Comment.objects.get(pk=comment_id)

            can_delete = (
                comment.author == user
                or comment.post.author == user
                or user.has_permission(Permissions.COMMENT_DELETE)
            )

            if not can_delete:
                return DeleteComment(
                    success=False,
                    message="You don't have permission to delete this comment",
                )

            post = comment.post

            replies_count = Comment.objects.filter(parent=comment).count()

            comment.delete()

            with transaction.atomic():
                Post.objects.filter(pk=post.pk).update(
                    comments_count=F("comments_count") - (1 + replies_count)
                )

            return DeleteComment(success=True, message="Comment deleted successfully!")

        except Comment.DoesNotExist:
            return DeleteComment(success=False, message="Comment not found")
        except Exception as e:
            return DeleteComment(
                success=False, message=f"Error deleting comment: {str(e)}"
            )


class DeleteShare(graphene.Mutation):
    """New mutation to delete shares with ownership check"""

    class Arguments:
        share_id = graphene.Int(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @monitor_performance("delete_share")
    @login_required
    @require_permission(Permissions.SHARE_DELETE, resource="share", log_activity=True)
    def mutate(self, info, share_id):
        user = info.context.user

        try:
            share = Share.objects.get(pk=share_id)

            # Ownership check: Only share owner or admin can delete
            can_delete = share.user == user or user.has_permission(
                Permissions.SHARE_DELETE
            )

            if not can_delete:
                return DeleteShare(
                    success=False, message="You can only delete your own shares"
                )

            post = share.post
            share.delete()

            # Update post's share count
            with transaction.atomic():
                Post.objects.filter(pk=post.pk).update(
                    shares_count=F("shares_count") - 1
                )

            return DeleteShare(success=True, message="Share deleted successfully!")

        except Share.DoesNotExist:
            return DeleteShare(success=False, message="Share not found")
        except Exception as e:
            return DeleteShare(success=False, message=f"Error deleting share: {str(e)}")


class InteractionMutation(graphene.ObjectType):
    like_post = LikePost.Field()
    create_comment = CreateComment.Field()
    update_comment = UpdateComment.Field()
    share_post = SharePost.Field()
    unshare_post = UnsharePost.Field()
    delete_comment = DeleteComment.Field()
    delete_share = DeleteShare.Field()
