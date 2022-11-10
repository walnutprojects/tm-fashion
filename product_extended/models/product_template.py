from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    name_secondary = fields.Char(string="Secondary Name")
    department_id = fields.Many2one('product.department', string='Department')
    internal_desc = fields.Text(string="Product Description")
    internal_desc_secondary = fields.Text(string="Product Description(AR)")
    default_vendor_id = fields.Many2one(comodel_name='res.partner', string="Default Vendor")
    tag_ids = fields.Many2many('product.tags', 'product_template_tag_ids',
                               'product_tmpl_id', 'tag_id', string="Tags")
    standard_price = fields.Float(groups="product_extended.group_show_cost_price")

    # price fields
    # price: total template price, context dependent (partner, pricelist, quantity)
    price = fields.Float(digits='Product Sale Price')
    # list_price: catalog price, user defined
    list_price = fields.Float(digits='Product Sale Price')

    @api.constrains('seller_ids')
    def validate_default_vendor(self):
        default_vendor_ids = self.seller_ids.filtered(lambda x: x.default_vendor)
        if len(default_vendor_ids) > 1:
            raise ValidationError(_("Only one Default Vendor allowed !"))

    _sql_constraints = [
        ('default_code_uniq', 'unique (company_id,default_code)', "Internal Reference must be unique per company!"),
    ]


class ProductProduct(models.Model):
    _inherit = "product.product"

    # price: total price, context dependent (partner, pricelist, quantity)
    price = fields.Float(digits='Product Sale Price')
    # price_extra: catalog extra value only, sum of variant extra attributes
    price_extra = fields.Float(digits='Product Sale Price')
    # lst_price: catalog value + extra, context dependent (uom)
    lst_price = fields.Float(digits='Product Sale Price')
    standard_price = fields.Float(groups="product_extended.group_show_cost_price")

    @api.model_create_multi
    def create(self, vals_list):
        products = super(ProductProduct, self).create(vals_list)
        auto_assign_internal_reference = self.env['ir.config_parameter'].sudo().get_param(
            'auto_assign_internal_reference')
        for product in products:
            if not product.default_code and auto_assign_internal_reference:
                product.default_code = self.env['ir.sequence'].next_by_code('product.internal.reference')
        return products

    _sql_constraints = [
        ('default_code_uniq', 'unique (company_id,default_code)', "Internal Reference must be unique per company!"),
    ]
