from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict
import math


class CustomPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return self._build_response(data)

    def get_custom_paginated_response(self, data, extra_fields=None):
        return self._build_response(data, extra_fields)

    def _build_response(self, data, extra_fields=None):
        response = OrderedDict()

        if extra_fields:
            response.update(extra_fields)

        response.update(
            {
                "status": "success",
                "status_code": 200,
                "count": self.page.paginator.count,
                "total_pages": math.ceil(
                    self.page.paginator.count / self.get_page_size(self.request)
                ),
                "page_size": self.get_page_size(self.request),
                "current_page": self.page.number,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "results": data,
            }
        )

        return Response(response, status=200)
