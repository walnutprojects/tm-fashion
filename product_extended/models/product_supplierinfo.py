# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    default_vendor = fields.Boolean(string='Default Vendor')
