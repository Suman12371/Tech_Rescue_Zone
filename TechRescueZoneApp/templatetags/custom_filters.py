from django import template

register = template.Library()

@register.filter(name='get_primary_image')
def get_primary_image(images):
    """Returns the first primary image or None if not found"""
    primary_image = images.filter(is_primary=True).first()
    return primary_image





@register.filter
def subtract(value, arg):
    try:
        return value - arg
    except (TypeError, ValueError):
        return value
    
@register.filter
def div(value, arg):
    try:
        return value / arg
    except (TypeError, ValueError, ZeroDivisionError):
        return value
    
@register.filter
def mul(value, arg):
    try:
        return value * arg
    except (TypeError, ValueError):
        return value
    
@register.filter
def multiply(value, arg):
    return value * arg