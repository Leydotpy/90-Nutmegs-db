from rest_framework.pagination import PageNumberPagination, CursorPagination

class PageNumberPaginationClass(PageNumberPagination):
    page_size = 10
    max_page_size = 1000


class CursorPaginationClass(CursorPagination):
    page_size = 10
    ordering = "-timestamp"