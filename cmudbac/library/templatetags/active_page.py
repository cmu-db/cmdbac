# django imports
from django import template
from django.urls import resolve
from django.urls import Resolver404


register = template.Library()


@register.simple_tag
def active_page(request, view_name):
    if not request:
        return ''
    try:
        return 'active' if resolve(request.path_info).url_name == view_name else ""
    except Resolver404:
        return ''
    return
