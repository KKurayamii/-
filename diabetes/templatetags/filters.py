from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    """Adds a CSS class to a form field widget."""
    if 'class' in field.field.widget.attrs:
        field.field.widget.attrs['class'] += f' {css_class}'
    else:
        field.field.widget.attrs['class'] = css_class
    return field
