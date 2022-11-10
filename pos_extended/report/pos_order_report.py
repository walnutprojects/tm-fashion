# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools
from odoo.addons.pos_hr.report.pos_order_report import PosOrderReport as PosOrderReportHr


def _select(self):
    return super(PosOrderReportHr, self)._select() + ',l.employee_id AS employee_id'


def _group_by(self):
    return super(PosOrderReportHr, self)._group_by() + ',l.employee_id'


PosOrderReportHr._select = _select
PosOrderReportHr._group_by = _group_by


class PosOrderReport(models.Model):
    _inherit = "report.pos.order"

    product_department_id = fields.Many2one('product.department', string='Product Department', readonly=True)
    product_brand_id = fields.Many2one('product.brand', string='Brand', readonly=True)
    default_vendor_id = fields.Many2one('res.partner', string='Vendor', readonly=True)
    return_reason_id = fields.Many2one('pos.return.reason', string="Return Reason", readonly=True)
    phone = fields.Char(string='Customer Phone', readonly=True)
    mobile = fields.Char(string='Customer Mobile', readonly=True)

    # qty_available = fields.Float(string='Qty On Hand')

    @api.model
    def _select(self):
        select_str = super()._select()
        select_str += """
                        , l.return_reason_id as return_reason_id
                        , pt.department_id as product_department_id
                        , pt.product_brand_id as product_brand_id
                        , pt.default_vendor_id as default_vendor_id
                        , rp.phone as phone
                        , rp.mobile as mobile
                        """
        # select_str += """
        # , l.qty_available as qty_available
        # """
        return select_str

    def _from(self):
        return super()._from() + " LEFT JOIN res_partner rp ON rp.id = s.partner_id"

    @api.model
    def _group_by(self):
        group_by_str = super()._group_by()
        group_by_str += ", l.return_reason_id, pt.department_id,pt.product_brand_id, pt.default_vendor_id, rp.phone, rp.mobile"
        return group_by_str
