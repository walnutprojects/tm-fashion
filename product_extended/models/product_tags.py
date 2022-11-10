from odoo import fields, models


class ProductTags(models.Model):
    _name = "product.tags"
    _description = 'Product Tags'

    name = fields.Char(string="Name", required=True)
