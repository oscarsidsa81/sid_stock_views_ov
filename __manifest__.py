# -*- coding: utf-8 -*-
{
    'name': 'SID Stock Views OV',
    'summary': 'Vistas OV para Inventario (sin hooks, xml_id estables)',
    'version': '15.0.1.1.0',
    'category': 'Inventory/Inventory',
    'license': 'LGPL-3',
    'author': 'SIDSA',
    'depends': [
        'stock',
        'sid_stock_legacy',
        'sid_stock_actions_ov',
    ],
    'data': [
        'views/stock_picking_views_ov.xml',
    ],
    'installable': True,
    'application': False,
}
