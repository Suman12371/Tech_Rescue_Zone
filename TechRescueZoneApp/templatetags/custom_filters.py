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


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def get_attr(obj, attr_name):
    return getattr(obj, attr_name, '')


@register.filter
def get_previous_message(message_list, index):
    """Get the previous message from a list based on the current index"""
    if index > 0 and index < len(message_list):
        return message_list[index - 1]
    return None

@register.filter
def get_message_date(message):
    """Get the formatted date from a message"""
    if message and hasattr(message, 'created_at'):
        return message.created_at.strftime("%B %d, %Y")
    return ""