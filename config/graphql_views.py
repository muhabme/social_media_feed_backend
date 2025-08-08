from django_ratelimit.exceptions import Ratelimited
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from graphene_django.views import GraphQLView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


def user_or_ip(*args):
    """
    Accept both possible signatures used by django-ratelimit:
      - user_or_ip(request)
      - user_or_ip(group, request)

    Take the last arg as the request object.
    """
    request = args[-1]
    try:
        if getattr(request, "user", None) and request.user.is_authenticated:
            return f"user:{request.user.id}"
    except Exception:
        pass
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


class RateLimitedGraphQLView(GraphQLView):

    @method_decorator(
        ratelimit(key=user_or_ip, rate="10/m", method="POST", block=False)
    )
    @csrf_exempt  # if needed
    def dispatch(self, request, *args, **kwargs):
        if getattr(request, "limited", False):
            return JsonResponse(
                {"errors": [{"message": "Rate limit exceeded"}]},
                status=429,
            )
        return super().dispatch(request, *args, **kwargs)
