from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'limit'
    max_page_size = 100

    def get_page_size(self, request):
        """
        Позволяет пользователю указать `?limit=...` в URL.
        Если `limit` отсутствует — используется `page_size`.
        Если `limit` превышает `max_page_size` — обрезается.
        """
        limit = request.query_params.get(self.page_size_query_param)
        if limit and limit.isdigit():
            return min(int(limit), self.max_page_size)
        return self.page_size
