from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary by key"""
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def filter_status(queryset, status):
    """Filter queryset by status field"""
    if hasattr(queryset, 'filter'):
        return queryset.filter(status=status)
    return [item for item in queryset if getattr(item, 'status', None) == status]


@register.filter
def filter_by_status(queryset, status):
    """Filter attendance queryset by status"""
    return [item for item in queryset if item.status == status]
