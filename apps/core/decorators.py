import functools
import time

from django.contrib.auth.models import AnonymousUser
from graphql import GraphQLError


def require_permission(permission_codename, resource=None, log_activity=True):
    """
    Decorator for GraphQL resolvers that requires a specific permission.

    Args:
        permission_codename (str): The permission codename required (e.g., 'post:create', 'user:delete')
        resource (str): Optional resource name for activity logging
        log_activity (bool): Whether to log this action

    Usage:
        @require_permission('post:create')
        def resolve_create_post(self, info, **kwargs):
            # resolver logic here
            pass

        @require_permission('user:delete', resource='user')
        def resolve_delete_user(self, info, **kwargs):
            # resolver logic here
            pass
    """

    def decorator(resolver_func):
        @functools.wraps(resolver_func)
        def wrapper(*args, **kwargs):
            info = None
            for arg in args:
                if hasattr(arg, "context") and hasattr(arg.context, "user"):
                    info = arg
                    break

            if not info:
                raise GraphQLError("Unable to find GraphQL info context")

            user = info.context.user
            request = info.context

            if isinstance(user, AnonymousUser) or not user.is_authenticated:
                raise GraphQLError("Authentication required")

            if not hasattr(user, "profile") or not user.profile:
                raise GraphQLError("User profile not found")

            if not user.profile.has_permission(permission_codename):
                # Log unauthorized access attempt
                if log_activity:
                    from apps.core.models import ActivityLog

                    ActivityLog.log_activity(
                        user=user,
                        action="unauthorized_access",
                        resource=resource or permission_codename.split(":")[0],
                        description=f"Unauthorized access attempt for permission: {permission_codename}",
                        request=request,
                    )
                raise GraphQLError(
                    f"Permission denied. Required permission: {permission_codename}"
                )

            start_time = time.time()
            try:
                result = resolver_func(*args, **kwargs)

                # Log successful action
                if log_activity and resource:
                    from apps.core.models import ActivityLog

                    execution_time = int((time.time() - start_time) * 1000)

                    action = (
                        permission_codename.split(":")[1]
                        if ":" in permission_codename
                        else "action"
                    )
                    ActivityLog.log_activity(
                        user=user,
                        action=action,
                        resource=resource,
                        description=f"Successfully executed {resolver_func.__name__}",
                        metadata={
                            "resolver": resolver_func.__name__,
                            "permission": permission_codename,
                            "args_count": len(args),
                            "kwargs_count": len(kwargs),
                        },
                        request=request,
                    )

                    log_entry = ActivityLog.objects.filter(user=user).first()
                    if log_entry:
                        log_entry.execution_time_ms = execution_time
                        log_entry.save(update_fields=["execution_time_ms"])

                return result

            except Exception as e:
                # Log failed action
                if log_activity:
                    from apps.core.models import ActivityLog

                    execution_time = int((time.time() - start_time) * 1000)

                    ActivityLog.log_activity(
                        user=user,
                        action="error",
                        resource=resource or permission_codename.split(":")[0],
                        description=f"Error in {resolver_func.__name__}: {str(e)}",
                        metadata={
                            "resolver": resolver_func.__name__,
                            "permission": permission_codename,
                            "error": str(e),
                            "error_type": type(e).__name__,
                        },
                        request=request,
                    )
                raise  # Re-raise the original exception

        return wrapper

    return decorator


def require_admin(log_activity=True):
    """
    Decorator that requires admin role

    Usage:
        @require_admin()
        def resolve_admin_only_query(self, info):
            pass
    """
    return require_permission(
        "admin:access", resource="admin", log_activity=log_activity
    )


def require_self_or_admin(user_field="user_id", log_activity=True):
    """
    Decorator that allows access if user is accessing their own data or is admin

    Args:
        user_field (str): The field name in kwargs that contains the user ID
        log_activity (bool): Whether to log this action

    Usage:
        @require_self_or_admin('user_id')
        def resolve_get_user_profile(self, info, user_id):
            pass
    """

    def decorator(resolver_func):
        @functools.wraps(resolver_func)
        def wrapper(*args, **kwargs):
            info = None
            for arg in args:
                if hasattr(arg, "context") and hasattr(arg.context, "user"):
                    info = arg
                    break

            if not info:
                raise GraphQLError("Unable to find GraphQL info context")

            user = info.context.user

            # Check authentication
            if isinstance(user, AnonymousUser) or not user.is_authenticated:
                raise GraphQLError("Authentication required")

            if not hasattr(user, "profile") or not user.profile:
                raise GraphQLError("User profile not found")

            # Check if user is admin
            if user.profile.has_permission("admin:access"):
                return resolver_func(*args, **kwargs)

            # Check if user is accessing their own data
            target_user_id = kwargs.get(user_field)
            if target_user_id and str(target_user_id) == str(user.id):
                return resolver_func(*args, **kwargs)

            # Log unauthorized access
            if log_activity:
                from apps.core.models import ActivityLog

                ActivityLog.log_activity(
                    user=user,
                    action="unauthorized_access",
                    resource="user_data",
                    description=f"Attempted to access data for user {target_user_id}",
                    request=info.context,
                )

            raise GraphQLError(
                "Access denied. You can only access your own data or need admin privileges."
            )

        return wrapper

    return decorator
