# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductLabelLayout(models.TransientModel):
    _inherit = 'product.label.layout'

    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', help='Pricelist')
    barcode_type = fields.Selection([('barcode', 'Barcode')], string="Barcode Type",
                                    default='barcode', required=True)


class ReportProductTemplateLabelDymo(models.AbstractModel):
    _inherit = 'report.product.report_producttemplatelabel_dymo'

    def _get_report_values(self, docids, data):
        layout_wizard = self.env['product.label.layout'].browse(data.get('layout_wizard'))
        if not layout_wizard:
            return {}
        data = super(ReportProductTemplateLabelDymo, self)._get_report_values(docids, data)
        data['pricelist'] = layout_wizard.pricelist_id
        return data