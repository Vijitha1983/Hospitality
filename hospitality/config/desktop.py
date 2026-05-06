from frappe import _


def get_data():
    return [
        {
            "module_name": "Hotel",
            "color": "#1a3c5e",
            "icon": "octicon octicon-home",
            "type": "module",
            "label": _("Hotel"),
        },
        {
            "module_name": "Restaurant",
            "color": "#c8962e",
            "icon": "octicon octicon-fork",
            "type": "module",
            "label": _("Restaurant"),
        },
        {
            "module_name": "Bar",
            "color": "#8b1a1a",
            "icon": "octicon octicon-kebab-vertical",
            "type": "module",
            "label": _("Bar"),
        },
        {
            "module_name": "Shared",
            "color": "#3d5a80",
            "icon": "octicon octicon-gear",
            "type": "module",
            "label": _("Hospitality Settings"),
        },
    ]
