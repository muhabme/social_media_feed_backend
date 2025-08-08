import graphene
from apps.posts.schema import PostQuery, PostMutation
from apps.users.schema import UserQuery, UserMutation, FollowQuery, FollowMutation
from apps.interactions.schema import InteractionQuery, InteractionMutation


class Query(PostQuery, UserQuery, FollowQuery, InteractionQuery, graphene.ObjectType):
    pass


class Mutation(
    PostMutation, UserMutation, FollowMutation, InteractionMutation, graphene.ObjectType
):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
