"""
Custom pagination for TerraSketch project.
"""
from rest_framework.pagination import CursorPagination as BaseCursorPagination
from rest_framework.response import Response
from collections import OrderedDict


class CursorPagination(BaseCursorPagination):
    """
    Custom cursor-based pagination for better performance with large datasets.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    cursor_query_param = 'cursor'
    cursor_query_description = 'The pagination cursor value.'
    ordering = '-created_at'  # Default ordering
    
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('count', len(data)),
            ('results', data)
        ]))


class StandardResultsSetPagination(BaseCursorPagination):
    """
    Standard pagination for endpoints that need it.
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200
    
    def get_paginated_response(self, data):
        return Response(OrderedDict([
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('count', len(data)),
            ('page_size', self.page_size),
            ('results', data)
        ]))