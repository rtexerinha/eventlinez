from django import template

register = template.Library()

@register.filter
def getitem(form, field_name):
    """Return a bound form field by name: {{ form|getitem:'field_name' }}"""
    try:
        return form[field_name]
    except KeyError:
        return None
