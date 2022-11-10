# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def get_product_info_pos(self, price, quantity, pos_config_id):
        res = super().get_product_info_pos(price, quantity, pos_config_id)
        if self.env.user.show_all_wh_info_pos:
            # Warehouses
            warehouse_list = [
                {'name': w.name,
                 'available_quantity': self.sudo().with_context({'warehouse': w.id}).qty_available,
                 'forecasted_quantity': self.sudo().with_context({'warehouse': w.id}).virtual_available,
                 'uom': self.uom_name}
                for w in self.env['stock.warehouse'].sudo().search([('company_id', '=', self.company_id.id or self.env.company.id)])]

            # Show all warehouses @todo link it with boolean in user level
            res['warehouses'] = warehouse_list

        return res
