class Permissions:
    """
    Central place to define all permission codenames
    """

    # User permissions
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # Post permissions
    POST_CREATE = "post:create"
    POST_READ = "post:read"
    POST_UPDATE = "post:update"
    POST_DELETE = "post:delete"

    # Comment permissions
    COMMENT_CREATE = "comment:create"
    COMMENT_READ = "comment:read"
    COMMENT_UPDATE = "comment:update"
    COMMENT_DELETE = "comment:delete"

    # Like permissions
    LIKE_CREATE = "like:create"
    LIKE_DELETE = "like:delete"

    # Share permissions
    SHARE_CREATE = "share:create"
    SHARE_DELETE = "share:delete"

    # Admin permissions
    ADMIN_ACCESS = "admin:access"
    ADMIN_USER_MANAGE = "admin:user_manage"
    ADMIN_CONTENT_MODERATE = "admin:content_moderate"
    ADMIN_ACTIVITY_VIEW = "admin:activity_view"
    ADMIN_SYSTEM_CONFIG = "admin:system_config"

    # Follow permissions
    FOLLOW_CREATE = "follow:create"
    FOLLOW_DELETE = "follow:delete"


# Helper function to check permissions in views/resolvers without decorator
def check_permission(user, permission_codename):
    """
    Check if a user has a specific permission

    Args:
        user: Django User instance
        permission_codename: Permission codename string

    Returns:
        bool: True if user has permission, False otherwise
    """
    if not user or not user.is_authenticated:
        return False

    if not hasattr(user, "profile") or not user.profile:
        return False

    return user.profile.has_permission(permission_codename)
