# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PoSPayment(models.Model):
    _inherit = 'pos.payment'

    @api.model
    def default_get(self, fields):
        res = super(PoSPayment, self).default_get(fields)
        if self.env.context.get('default_pos_order_id'):
            res['pos_order_id'] = self.env.context.get('default_pos_order_id')
        return res

    note = fields.Char(string="Note")
    order_state = fields.Selection(related='pos_order_id.state', readonly=1)
