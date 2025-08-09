from unittest.mock import Mock

from django.contrib.auth import get_user_model
from django.db import connection

from tests.test_base import GraphQLTestCase


class UtilsTests(GraphQLTestCase):
    def setUp(self):
        super().setUp()
        # keep local test data predictable
        User = get_user_model()
        User.objects.filter(username__startswith="paginateuser").delete()

    def tearDown(self):
        User = get_user_model()
        User.objects.filter(username__startswith="paginateuser").delete()
        super().tearDown()

    def test_monitor_performance_decorator(self):
        from utils.monitoring import monitor_performance

        mock_self = object()
        mock_info = Mock()
        mock_info.context = Mock()
        mock_info.context.user = Mock()
        mock_info.context.user.id = 1

        @monitor_performance(operation_name="test_function")
        def test_function(self, info):
            return "success"

        result = test_function(mock_self, mock_info)
        self.assertEqual(result, "success")

    def test_paginate_queryset(self):
        """Test pagination helper; keep it DB-agnostic and deterministic."""
        from utils.pagination import paginate_queryset

        User = get_user_model()

        # create a small, stable set of users
        for i in range(10):
            username = f"paginateuser{i}"
            email = f"paginate{i}@test.com"
            User.objects.get_or_create(username=username, defaults={"email": email})

        queryset = User.objects.filter(username__startswith="paginateuser").order_by(
            "username"
        )
        paginated = paginate_queryset(queryset, page=1, items_per_page=5)

        self.assertEqual(len(paginated["items"]), 5)
        # total_items and total_pages should be deterministic with the data above
        self.assertEqual(paginated["total_items"], 10)
        self.assertEqual(paginated["total_pages"], 2)
