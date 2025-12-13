from django import template

register = template.Library()


@register.filter
def get_item(value, arg):
    try:
        return value.get(arg, "")
    except Exception:
        return ""
