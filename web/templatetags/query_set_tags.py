from django import template

register = template.Library()


@register.filter(name='order_by')
def order_by(queryset, order):
    return queryset.order_by(order)
