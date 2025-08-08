import graphene
from apps.posts.schema import PostQuery, PostMutation
from apps.users.schema import UserQuery
from apps.interactions.schema import InteractionQuery, InteractionMutation


class Query(PostQuery, UserQuery, InteractionQuery, graphene.ObjectType):
    pass


class Mutation(PostMutation, InteractionMutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
