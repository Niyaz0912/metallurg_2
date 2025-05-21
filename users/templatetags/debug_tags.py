from django import template

register = template.Library()

@register.simple_tag
def debug():
    return "Debug info here"
