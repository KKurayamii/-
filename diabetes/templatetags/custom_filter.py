from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    return dictionary.get(key, None)

@register.filter
def range_filter(value):
    return range(1, value + 1)
