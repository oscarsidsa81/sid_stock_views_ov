# -*- coding: utf-8 -*-
{
    "name": "SID Stock Views OV",
    "summary": "Recrea vistas OV de Stock con referencias estables (sin IDs numéricos) y campos SID base.",
    "version": "15.0.1.0.2",
    "category": "Inventory",
    "license": "LGPL-3",
    "author": "SIDSA",
    "depends": [
        "stock",
        "mail",
        "sale_stock",
        "purchase_stock",
        "sid_product_base",
        "sid_stock_base",
        "sid_stock_actions_ov",
    ],
    "data": [
        # vistas se crean en post_init para poder localizar inherit_id por nombre
    ],
    "post_init_hook": "post_init_create_sid_stock_views_ov",
    "installable": True,
    "application": False,
}
