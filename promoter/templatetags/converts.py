from datetime import datetime

from django import template

register = template.Library()


@register.filter(name='divise')
def divise(value, divis):
    return round((value / divis), 3)


@register.filter(name='current_time')
def current_time(format_string):
    return datetime.fromtimestamp(format_string).strftime("%Y-%m-%d")
