from django import template

register = template.Library()

@register.filter(name='subtract')
def subtract(value, arg):
    """Subtracts the arg from the value"""
    return value - arg

@register.filter(name='multiply')
def multiply(value, arg):
    """Multiplies the value by arg"""
    return value * arg