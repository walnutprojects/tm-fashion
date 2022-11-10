# -*- coding: utf-8 -*-
{
    "name": "POS Ocean API",
    "version": "15.0.0.0.1",
    "category": "Point of Sale",
    'summary': 'Ocean API Intengration',
    "description": """
Ocean API Integration
    """,
    "author": "Walnut Software Solutions",
    "website": "www.walnutit.com",
    "depends": ['pos_extended'],
    "data": [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'views/menu.xml',
        'views/pos_config_view.xml',
        'views/ocean_import_log.xml',
    ],
    'qweb': [
    ],
    'assets': {
    },
    "auto_install": False,
    "installable": True,
    'license': 'OPL-1'
}
