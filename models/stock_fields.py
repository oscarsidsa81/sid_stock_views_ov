# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # Campos base adicionales para sustituir algunos x_* usados en vistas OV
    sid_cliente = fields.Many2one(related="sale_id.partner_id", string="Cliente (SID)", store=True, readonly=True)
    sid_pedido_cliente = fields.Char(related="sale_id.client_order_ref", string="Pedido cliente (SID)", store=True, readonly=True)


class StockMove(models.Model):
    _inherit = "stock.move"

    # Relacionados con producto (para searchpanel / listas)
    sid_pasillo = fields.Selection(related="product_tmpl_id.sid_pasillo", string="Pasillo (SID)", store=True, readonly=True)
    sid_alto = fields.Selection(related="product_tmpl_id.sid_alto", string="Alto (SID)", store=True, readonly=True)
    sid_lado = fields.Selection(related="product_tmpl_id.sid_lado", string="Lado (SID)", store=True, readonly=True)
    sid_largo = fields.Selection(related="product_tmpl_id.sid_largo", string="Largo (SID)", store=True, readonly=True)


class StockQuant(models.Model):
    _inherit = "stock.quant"

    sid_pasillo = fields.Selection(related="product_id.sid_pasillo", string="Pasillo (SID)", store=True, readonly=True)
