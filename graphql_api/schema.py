import graphene

from apps.interactions.schema import InteractionMutation, InteractionQuery
from apps.posts.schema import PostMutation, PostQuery
from apps.users.schema import (
    AdminQuery,
    AuthMutation,
    FollowMutation,
    FollowQuery,
    UserMutation,
    UserQuery,
)


class Query(
    PostQuery, UserQuery, AdminQuery, FollowQuery, InteractionQuery, graphene.ObjectType
):
    pass


class Mutation(
    AuthMutation,
    UserMutation,
    FollowMutation,
    PostMutation,
    InteractionMutation,
    graphene.ObjectType,
):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
