from django import template

register = template.Library()


@register.filter
def som(value):
    """1200000 -> "1 200 000 so'm\""""
    try:
        return f"{int(value):,}".replace(',', ' ') + " so'm"
    except (TypeError, ValueError):
        return value
