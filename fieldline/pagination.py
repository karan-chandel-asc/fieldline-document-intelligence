from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from fieldline.responses import success_response


class CustomPagination(PageNumberPagination):
    page_size = 8
    page_query_param = "page"
    page_size_query_param = "page_size"
    max_page_size = 50

    def get_paginated_response(self, data):
        return Response(
            success_response(
                message=getattr(self, "response_message", "Fetched successfully"),
                data={
                    "results": data,
                    "page": self.page.number,
                    "page_size": self.get_page_size(self.request),
                    "has_more": self.page.has_next(),
                    "total": self.page.paginator.count,
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                },
            )
        )
