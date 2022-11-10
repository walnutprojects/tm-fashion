# -*- coding: utf-8 -*-

import logging
from odoo import fields, models, api, _
from odoo.osv.expression import AND

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        res['barcode_number'] = ui_order.get('barcode')
        refund_order_employee_id = ui_order.get('refund_order_employee_id')
        if refund_order_employee_id:
            res['employee_id'] = refund_order_employee_id
        return res

    @api.model
    def _payment_fields(self, order, ui_paymentline):
        res = super(PosOrder, self)._payment_fields(order, ui_paymentline)
        res['note'] = ui_paymentline.get('note', '')
        return res

    @api.model
    def search_sudo_paid_order_ids(self, domain, limit, offset):
        """Search for 'paid' orders that satisfy the given domain, limit and offset."""
        default_domain = ['&', ('config_id', '!=', False), '!', '|', ('state', '=', 'draft'),
                          ('state', '=', 'cancelled')]
        real_domain = AND([domain, default_domain])
        ids = self.sudo().search(AND([domain, default_domain]), limit=limit, offset=offset).ids
        totalCount = self.sudo().search_count(real_domain)
        return {'ids': ids, 'totalCount': totalCount}

    def _export_for_ui(self, order):
        result = super(PosOrder, self)._export_for_ui(order)
        result.update({
            'barcode': order.barcode_number,
            'employee_id': order.employee_id.id,
            'pos_config': order.session_id.config_id.display_name,
        })
        return result

    def update_payment_lines(self, vals):
        for idx, pl in enumerate(self.payment_ids):
            pl.write(vals[idx])
        self._onchange_amount_all()
        return self.export_for_ui()

    @api.depends('lines', 'lines.qty')
    def _compute_sale_type(self):
        for order in self:
            sale_type = 'sale'
            for line in order.lines:
                if line.qty < 0:
                    sale_type = 'refund'
                if sale_type == 'refund' and line.qty > 0:
                    sale_type = 'exchange'
                    break
            order.sale_type = sale_type

    barcode_number = fields.Char(string="Barcode Number")
    sale_type = fields.Selection([('sale', 'Sale'), ('exchange', 'Exchange'), ('refund', 'Refund')], string="Sale Type",
                                 compute='_compute_sale_type', store=True)
    discount_amount = fields.Monetary(string="Discount Amount", compute='_compute_discount', store=True)
    discount = fields.Float(string="Discount %", compute='_compute_discount', store=True)
    margin = fields.Monetary(groups="pos_extended.group_pos_margin")
    margin_percent = fields.Float(groups="pos_extended.group_pos_margin")
    # removed readonly from payment_ids
    payment_ids = fields.One2many('pos.payment', 'pos_order_id', string='Payments', readonly=False)

    @api.depends('lines', 'lines.discount_amount')
    def _compute_discount(self):
        for rec in self:
            discount_amount = sum(rec.lines.mapped('discount_amount'))
            total = rec.amount_total + discount_amount
            rec.discount_amount = discount_amount
            if discount_amount > 0:
                rec.discount = discount_amount / total


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    def _order_line_fields(self, line, session_id):
        result = super()._order_line_fields(line, session_id)
        vals = result[2]
        vals['return_reason_id'] = line[2].get('return_reason', False)
        return result

    @api.depends('order_id', 'refunded_orderline_id')
    def _compute_employee(self):
        for line in self:
            if line.refunded_orderline_id:
                line.employee_id = line.refunded_orderline_id.employee_id.id
            else:
                line.employee_id = line.order_id.employee_id.id

    discount_amount = fields.Monetary(string="Discount Amount", compute='_compute_discount_amount', store=True)
    return_reason_id = fields.Many2one('pos.return.reason', string="Return Reason")
    employee_id = fields.Many2one('hr.employee', compute='_compute_employee', store=True)

    # qty_available = fields.Float(related='product_id.qty_available', string='Qty On Hand', store=True)
    margin = fields.Monetary(groups="pos_extended.group_pos_margin")
    margin_percent = fields.Float(groups="pos_extended.group_pos_margin")

    @api.depends('discount', 'qty', 'price_unit', 'order_id.currency_rate')
    def _compute_discount_amount(self):
        for rec in self:
            currency_rate = rec.order_id.currency_rate if rec.order_id.currency_rate != 0 else 1
            discount_amount = (rec.qty * rec.price_unit) * (rec.discount / 100) / currency_rate
            rec.discount_amount = discount_amount
