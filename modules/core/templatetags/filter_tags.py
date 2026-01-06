from django import template

register = template.Library()

@register.filter
def my_filter(value):
    return value.upper()
