# -*- coding: utf-8 -*-

from odoo.addons.point_of_sale.models.stock_picking import StockPicking

# NOTE: function is rewritten to bypass the access right issue on accessing warehouse_id

def _send_confirmation_email(self):
    # Avoid sending Mail/SMS for POS deliveries
    pickings = self.filtered(lambda p: p.picking_type_id != p.picking_type_id.sudo().warehouse_id.pos_type_id)
    return super(StockPicking, pickings)._send_confirmation_email()


StockPicking._send_confirmation_email = _send_confirmation_email
