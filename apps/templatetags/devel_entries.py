from django import template

register = template.Library()

@register.inclusion_tag('devel_entries.html')
def devel_entries(bundles, cx_platform):
    return {
        'bundles': bundles,
        'cx_platform': cx_platform,
    }

@register.inclusion_tag('devel_entry.html')
def devel_entry(bundle, cx_platform):
    import os.path
    return {
        'bundle': bundle,
        'filename': os.path.basename(bundle.path),
        'cx_platform': cx_platform,
    }
