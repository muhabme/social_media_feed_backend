import logging
import os
import time
from functools import wraps

from django.core.cache import cache
from django.utils import timezone

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/graphql.log"), logging.StreamHandler()],
)

logger = logging.getLogger("graphql_api")


class GraphQLMonitor:
    @staticmethod
    def log_query_performance(operation_name, execution_time, user_id=None):
        """Log query performance metrics"""
        logger.info(
            f"GraphQL Operation: {operation_name} | "
            f"Execution Time: {execution_time:.3f}s | "
            f"User: {user_id or 'Anonymous'}"
        )

        # Store metrics in cache for dashboard
        metrics_key = (
            f"metrics:{operation_name}:{timezone.now().strftime('%Y-%m-%d-%H')}"
        )
        current_metrics = cache.get(metrics_key, {"count": 0, "total_time": 0})
        current_metrics["count"] += 1
        current_metrics["total_time"] += execution_time
        cache.set(metrics_key, current_metrics, timeout=3600)

    @staticmethod
    def log_error(operation_name, error, user_id=None):
        """Log GraphQL errors"""
        logger.error(
            f"GraphQL Error in {operation_name}: {str(error)} | "
            f"User: {user_id or 'Anonymous'}"
        )


def monitor_performance(operation_name, min_log_time=0.001):
    """Decorator to monitor GraphQL operation performance and optionally skip fast logs"""

    def decorator(func):
        @wraps(func)
        def wrapper(self, info, *args, **kwargs):
            start_time = time.time()
            user_id = (
                getattr(info.context.user, "id", None)
                if hasattr(info.context, "user")
                else None
            )

            try:
                result = func(self, info, *args, **kwargs)
                execution_time = time.time() - start_time

                if execution_time >= min_log_time:
                    GraphQLMonitor.log_query_performance(
                        operation_name, execution_time, user_id
                    )
                return result

            except Exception as e:
                execution_time = time.time() - start_time
                GraphQLMonitor.log_error(operation_name, e, user_id)
                raise

        return wrapper

    return decorator
