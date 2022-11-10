from odoo import fields, models


class ProductDepartment(models.Model):
    _name = "product.department"
    _description = 'Product Department'

    name = fields.Char(string="Name", required=True)
