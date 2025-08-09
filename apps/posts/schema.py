import graphene
from graphene_django import DjangoObjectType
from .models import Post
from utils.pagination import paginate_queryset
from .cache_service import feed_cache_service
from apps.core.redis_service import redis_service
from apps.users.models import User
from graphql_jwt.decorators import login_required
from math import ceil
from apps.interactions.models import Comment
from django.db.models import Prefetch
from utils.monitoring import monitor_performance


class PostType(DjangoObjectType):
    likes_count = graphene.Int()
    comments_count = graphene.Int()
    is_liked = graphene.Boolean()

    class Meta:
        model = Post
        fields = "__all__"

    @monitor_performance("likes_count")
    def resolve_likes_count(self, info):
        """Get real-time like count from Redis"""
        cached_count = redis_service.get_counter(f"post:{self.id}:likes")
        return cached_count if cached_count is not None else self.likes_count

    @monitor_performance("comments_count")
    def resolve_comments_count(self, info):
        """Get real-time comment count from Redis"""
        cached_count = redis_service.get_counter(f"post:{self.id}:comments")
        return cached_count if cached_count is not None else self.comments_count

    @monitor_performance("is_liked")
    def resolve_is_liked(self, info):
        """Check if current user liked this post"""
        if not info.context.user.is_authenticated:
            return False

        like_key = f"user_likes:{info.context.user.id}"
        return redis_service.is_in_set(like_key, str(self.id))


class PostPaginationType(graphene.ObjectType):
    items = graphene.List(PostType)
    total_items = graphene.Int()
    total_pages = graphene.Int()
    current_page = graphene.Int()


class PostQuery(graphene.ObjectType):
    post = graphene.Field(PostType, id=graphene.Int(required=True))
    posts_by_user = graphene.Field(
        PostPaginationType,
        user_id=graphene.Int(required=True),
        page=graphene.Int(required=False),
        items_per_page=graphene.Int(required=False),
    )
    user_feed = graphene.Field(
        PostPaginationType,
        page=graphene.Int(required=False),
        items_per_page=graphene.Int(required=False),
    )
    trending_posts = graphene.Field(
        PostPaginationType,
        page=graphene.Int(required=False),
        items_per_page=graphene.Int(required=False),
    )

    @login_required
    @monitor_performance("post")
    def resolve_post(self, info, id):
        """Get single post with caching"""
        cached_post = feed_cache_service.get_cached_post(id)
        if cached_post:
            try:
                return Post.objects.get(id=id, is_active=True)
            except Post.DoesNotExist:
                feed_cache_service.invalidate_post_cache(id)
                return None

        try:
            post = Post.objects.select_related("author").get(id=id, is_active=True)
            post_data = {
                "id": post.id,
                "content": post.content,
                "author": {"id": post.author.id, "username": post.author.username},
                "likes_count": post.likes_count,
                "comments_count": post.comments_count,
                "created_at": post.created_at.isoformat(),
            }
            feed_cache_service.cache_post_details(id, post_data)
            return post
        except Post.DoesNotExist:
            return None

    @login_required
    @monitor_performance("posts_by_user")
    def resolve_posts_by_user(self, info, user_id, page=1, items_per_page=10):
        """Get user's posts with caching"""

        cache_key = f"user_posts_{user_id}_page_{page}_per_{items_per_page}"

        cached_result = redis_service.get_cached(cache_key)
        if cached_result:
            post_ids = [item["id"] for item in cached_result["items"]]
            if post_ids:
                posts = Post.objects.filter(
                    id__in=post_ids, author_id=user_id, is_active=True
                )
                posts_dict = {post.id: post for post in posts}
                ordered_posts = [
                    posts_dict[post_id] for post_id in post_ids if post_id in posts_dict
                ]

                return PostPaginationType(
                    items=ordered_posts,
                    total_items=cached_result["total_items"],
                    total_pages=cached_result["total_pages"],
                    current_page=cached_result["current_page"],
                )

        qs = (
            Post.objects.filter(author_id=user_id, is_active=True)
            .order_by("-created_at")
            .prefetch_related(
                Prefetch("comments", queryset=Comment.objects.select_related("author"))
            )
        )
        data = paginate_queryset(qs, page, items_per_page)

        cache_data = {
            "items": [{"id": post.id} for post in data["items"]],
            "total_items": data["total_items"],
            "total_pages": data["total_pages"],
            "current_page": data["current_page"],
        }
        redis_service.set_cached(cache_key, cache_data, timeout=600)

        return PostPaginationType(**data)

    @login_required
    @monitor_performance("user_feed")
    def resolve_user_feed(self, info, page=1, items_per_page=10):
        """Get user's personalized feed with caching"""
        user = info.context.user

        cached_feed = feed_cache_service.get_cached_feed(
            user.id, page=page, per_page=items_per_page
        )

        if cached_feed and cached_feed.get("items"):
            post_ids = [post["id"] for post in cached_feed["items"]]
            posts = Post.objects.filter(id__in=post_ids, is_active=True)
            posts_dict = {post.id: post for post in posts}
            ordered_posts = [
                posts_dict[post_id] for post_id in post_ids if post_id in posts_dict
            ]

            return PostPaginationType(
                items=ordered_posts,
                total_items=cached_feed.get("total_items", len(ordered_posts)),
                total_pages=cached_feed.get("total_pages", 1),
                current_page=page,
            )

        following_users = User.objects.filter(follower_relationships__follower=user)
        qs = (
            Post.objects.filter(author__in=following_users, is_active=True)
            .order_by("-created_at")
            .prefetch_related(
                Prefetch("comments", queryset=Comment.objects.select_related("author"))
            )
        )

        data = paginate_queryset(qs, page, items_per_page)

        posts_data = {
            "items": [
                {
                    "id": post.id,
                    "content": post.content,
                    "author_id": post.author.id,
                    "created_at": post.created_at.isoformat(),
                }
                for post in data["items"]
            ],
            "total_items": data["total_items"],
            "total_pages": data["total_pages"],
            "current_page": page,
        }

        feed_cache_service.cache_user_feed(
            user.id, posts_data, page=page, per_page=items_per_page
        )

        return PostPaginationType(**data)

    @login_required
    @monitor_performance("trending_posts")
    def resolve_trending_posts(self, info, page=1, items_per_page=10):
        start = (page - 1) * items_per_page
        limit = items_per_page

        trending_ids = redis_service.get_top_from_sorted_set(
            "trending_posts", limit=start + limit
        )
        trending_ids = [str(i) for i in trending_ids]

        if not trending_ids:
            qs = Post.objects.filter(is_active=True).order_by(
                "-likes_count", "-created_at"
            )[:limit]
            return PostPaginationType(
                items=list(qs), total_items=qs.count(), total_pages=1, current_page=page
            )

        posts = Post.objects.filter(id__in=trending_ids, is_active=True)
        posts_dict = {str(p.id): p for p in posts}
        ordered_posts = [posts_dict[i] for i in trending_ids if i in posts_dict]

        total_items = len(trending_ids)
        return PostPaginationType(
            items=ordered_posts,
            total_items=total_items,
            total_pages=ceil(total_items / items_per_page),
            current_page=page,
        )


class CreatePost(graphene.Mutation):
    class Arguments:
        content = graphene.String(required=True)
        image_url = graphene.String(required=False)

    post = graphene.Field(PostType)
    success = graphene.Boolean()
    message = graphene.String()

    @login_required
    @monitor_performance("create_post")
    def mutate(self, info, content, image_url=None):
        user = info.context.user

        try:
            post = Post.objects.create(author=user, content=content, image=image_url)

            post_data = {
                "id": post.id,
                "content": post.content,
                "author": {"id": post.author.id, "username": post.author.username},
                "likes_count": 0,
                "comments_count": 0,
                "created_at": post.created_at.isoformat(),
            }
            feed_cache_service.cache_post_details(post.id, post_data)

            redis_service.set_cached(
                f"post:{post.id}:likes", 0, cache_name="counters", timeout=None
            )
            redis_service.set_cached(
                f"post:{post.id}:comments", 0, cache_name="counters", timeout=None
            )

            self._invalidate_post_creation_caches(user.id)

            return CreatePost(
                post=post, success=True, message="Post created successfully!"
            )
        except Exception as e:
            return CreatePost(
                post=None, success=False, message=f"Error creating post: {str(e)}"
            )

    def _invalidate_post_creation_caches(self, user_id):
        """Invalidate caches affected by new post creation"""
        pattern = f"user_posts_{user_id}_*"
        for k in redis_service.redis_client.scan_iter(match=pattern):
            redis_service.redis_client.delete(k)

        feed_cache_service.invalidate_user_feed(user_id)


class UpdatePost(graphene.Mutation):
    class Arguments:
        post_id = graphene.Int(required=True)
        content = graphene.String(required=True)

    post = graphene.Field(PostType)
    success = graphene.Boolean()
    message = graphene.String()

    @login_required
    @monitor_performance("update_post")
    def mutate(self, info, post_id, content):
        user = info.context.user

        try:
            post = Post.objects.get(pk=post_id, author=user, is_active=True)
            post.content = content
            post.save()

            post_data = {
                "id": post.id,
                "content": post.content,
                "author": {"id": post.author.id, "username": post.author.username},
                "likes_count": redis_service.get_counter(f"post:{post.id}:likes")
                or post.likes_count,
                "comments_count": redis_service.get_counter(f"post:{post.id}:comments")
                or post.comments_count,
                "created_at": post.created_at.isoformat(),
            }
            feed_cache_service.cache_post_details(post.id, post_data)

            self._invalidate_post_update_caches(user.id, post_id)

            return UpdatePost(
                post=post, success=True, message="Post updated successfully!"
            )
        except Post.DoesNotExist:
            return UpdatePost(
                post=None,
                success=False,
                message="Post not found or you don't have permission",
            )

    def _invalidate_post_update_caches(self, user_id, post_id):
        """Invalidate caches affected by post update"""
        feed_cache_service.invalidate_post_cache(post_id)

        pattern = f"user_posts_{user_id}_*"
        for k in redis_service.redis_client.scan_iter(match=pattern):
            redis_service.redis_client.delete(k)

        feed_cache_service.invalidate_user_feed(user_id)


class DeletePost(graphene.Mutation):
    class Arguments:
        post_id = graphene.Int(required=True)

    success = graphene.Boolean()
    message = graphene.String()

    @login_required
    @monitor_performance("delete_post")
    def mutate(self, info, post_id):
        user = info.context.user

        try:
            post = Post.objects.get(pk=post_id, author=user, is_active=True)
            post.is_active = False  # Soft delete
            post.save()

            self._cleanup_deleted_post_caches(user.id, post_id)

            return DeletePost(success=True, message="Post deleted successfully!")
        except Post.DoesNotExist:
            return DeletePost(
                success=False, message="Post not found or you don't have permission"
            )

    def _cleanup_deleted_post_caches(self, user_id, post_id):
        """Clean up caches for deleted post"""
        feed_cache_service.invalidate_post_cache(post_id)

        redis_service.redis_client.zrem("trending_posts", str(post_id))

        redis_service.delete_cached(f"post:{post_id}:likes", cache_name="counters")
        redis_service.delete_cached(f"post:{post_id}:comments", cache_name="counters")
        redis_service.delete_cached(f"post:{post_id}:shares", cache_name="counters")

        pattern = f"user_posts_{user_id}_*"
        for k in redis_service.redis_client.scan_iter(match=pattern):
            redis_service.redis_client.delete(k)


class PostMutation(graphene.ObjectType):
    create_post = CreatePost.Field()
    update_post = UpdatePost.Field()
    delete_post = DeletePost.Field()
