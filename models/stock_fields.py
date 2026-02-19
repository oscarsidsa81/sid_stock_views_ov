# -*- coding: utf-8 -*-
from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # Campos relacionados para sustituir algunos x_* usados en vistas OV.
    # Nota: NO declaramos relacionados de pasillo/alto/lado/largo aquí para evitar
    # conflictos de tipo si sid_product_base cambia el tipo del campo (selection/char/etc).
    sid_cliente = fields.Many2one(
        related="sale_id.partner_id",
        string="Cliente (SID)",
        store=True,
        readonly=True,
    )
    sid_pedido_cliente = fields.Char(
        related="sale_id.client_order_ref",
        string="Pedido cliente (SID)",
        store=True,
        readonly=True,
    )
