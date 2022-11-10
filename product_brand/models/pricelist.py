# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from itertools import chain


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    def price_rule_where_str(self, products):
        where_str = super(ProductPricelist, self).price_rule_where_str(products)
        brand_ids = []
        for p in self.env['product.product'].browse(products):
            if p.product_brand_id:
                brand_ids.append(p.product_brand_id.id)
        if brand_ids:
            brand_ids = list(brand_ids)
            brand_ids_str = ",".join([str(i) for i in brand_ids])
            where_str += """ AND (item.brand_id IS NULL OR item.brand_id in (%s)) """ % brand_ids_str
        return where_str

    # def _compute_price_rule_get_items(self, products_qty_partner, date, uom_id, prod_tmpl_ids,
    #                                   prod_ids, categ_ids, brand_ids):
    #     self.ensure_one()
    #     # Load all rules
    #     self.env['product.pricelist.item'].flush(['price', 'currency_id', 'company_id', 'active'])
    #     self.env.cr.execute(
    #         """
    #         SELECT
    #             item.id
    #         FROM
    #             product_pricelist_item AS item
    #         LEFT JOIN product_category AS categ ON item.categ_id = categ.id
    #         WHERE
    #             (item.product_tmpl_id IS NULL OR item.product_tmpl_id = any(%s))
    #             AND (item.product_id IS NULL OR item.product_id = any(%s))
    #             AND (item.categ_id IS NULL OR item.categ_id = any(%s))
    #             AND (item.brand_id IS NULL OR item.brand_id = any(%s))
    #             AND (item.pricelist_id = %s)
    #             AND (item.date_start IS NULL OR item.date_start<=%s)
    #             AND (item.date_end IS NULL OR item.date_end>=%s)
    #             AND (item.active = TRUE)
    #         ORDER BY
    #             item.applied_on, item.min_quantity desc, categ.complete_name desc, item.id desc
    #         """,
    #         (prod_tmpl_ids, prod_ids, categ_ids, brand_ids, self.id, date, date))
    #     # NOTE: if you change `order by` on that query, make sure it matches
    #     # _order from model to avoid inconstencies and undeterministic issues.
    #
    #     item_ids = [x[0] for x in self.env.cr.fetchall()]
    #     return self.env['product.pricelist.item'].browse(item_ids)
    #
    # def _compute_price_rule(self, products_qty_partner, date=False, uom_id=False):
    #     """ Low-level method - Mono pricelist, multi products
    #     Returns: dict{product_id: (price, suitable_rule) for the given pricelist}
    #
    #     Date in context can be a date, datetime, ...
    #
    #         :param products_qty_partner: list of typles products, quantity, partner
    #         :param datetime date: validity date
    #         :param ID uom_id: intermediate unit of measure
    #     """
    #     self.ensure_one()
    #     if not date:
    #         date = self._context.get('date') or fields.Datetime.now()
    #     if not uom_id and self._context.get('uom'):
    #         uom_id = self._context['uom']
    #     if uom_id:
    #         # rebrowse with uom if given
    #         products = [item[0].with_context(uom=uom_id) for item in products_qty_partner]
    #         products_qty_partner = [(products[index], data_struct[1], data_struct[2]) for index, data_struct in enumerate(products_qty_partner)]
    #     else:
    #         products = [item[0] for item in products_qty_partner]
    #
    #     if not products:
    #         return {}
    #
    #     categ_ids = {}
    #     brand_ids = []
    #     for p in products:
    #         categ = p.categ_id
    #         if p.product_brand_id:
    #             brand_ids.append(p.product_brand_id.id)
    #         while categ:
    #             categ_ids[categ.id] = True
    #             categ = categ.parent_id
    #     categ_ids = list(categ_ids)
    #
    #     is_product_template = products[0]._name == "product.template"
    #     if is_product_template:
    #         prod_tmpl_ids = [tmpl.id for tmpl in products]
    #         # all variants of all products
    #         prod_ids = [p.id for p in
    #                     list(chain.from_iterable([t.product_variant_ids for t in products]))]
    #     else:
    #         prod_ids = [product.id for product in products]
    #         prod_tmpl_ids = [product.product_tmpl_id.id for product in products]
    #
    #     items = self._compute_price_rule_get_items(products_qty_partner, date, uom_id, prod_tmpl_ids, prod_ids, categ_ids, brand_ids)
    #
    #     results = {}
    #     for product, qty, partner in products_qty_partner:
    #         results[product.id] = 0.0
    #         suitable_rule = False
    #
    #         # Final unit price is computed according to `qty` in the `qty_uom_id` UoM.
    #         # An intermediary unit price may be computed according to a different UoM, in
    #         # which case the price_uom_id contains that UoM.
    #         # The final price will be converted to match `qty_uom_id`.
    #         qty_uom_id = self._context.get('uom') or product.uom_id.id
    #         qty_in_product_uom = qty
    #         if qty_uom_id != product.uom_id.id:
    #             try:
    #                 qty_in_product_uom = self.env['uom.uom'].browse([self._context['uom']])._compute_quantity(qty, product.uom_id)
    #             except UserError:
    #                 # Ignored - incompatible UoM in context, use default product UoM
    #                 pass
    #
    #         # if Public user try to access standard price from website sale, need to call price_compute.
    #         # TDE SURPRISE: product can actually be a template
    #         price = product.price_compute('list_price')[product.id]
    #
    #         price_uom = self.env['uom.uom'].browse([qty_uom_id])
    #         for rule in items:
    #             if not rule._is_applicable_for(product, qty_in_product_uom):
    #                 continue
    #             if rule.base == 'pricelist' and rule.base_pricelist_id:
    #                 price_tmp = rule.base_pricelist_id._compute_price_rule([(product, qty, partner)], date, uom_id)[product.id][0]  # TDE: 0 = price, 1 = rule
    #                 price = rule.base_pricelist_id.currency_id._convert(price_tmp, self.currency_id, self.env.company, date, round=False)
    #             else:
    #                 # if base option is public price take sale price else cost price of product
    #                 # price_compute returns the price in the context UoM, i.e. qty_uom_id
    #                 price = product.price_compute(rule.base)[product.id]
    #
    #             if price is not False:
    #                 # pass the date through the context for further currency conversions
    #                 rule_with_date_context = rule.with_context(date=date)
    #                 price = rule_with_date_context._compute_price(price, price_uom, product, quantity=qty, partner=partner)
    #                 suitable_rule = rule
    #             break
    #         # Final price conversion into pricelist currency
    #         if suitable_rule and suitable_rule.compute_price != 'fixed' and suitable_rule.base != 'pricelist':
    #             if suitable_rule.base == 'standard_price':
    #                 cur = product.cost_currency_id
    #             else:
    #                 cur = product.currency_id
    #             price = cur._convert(price, self.currency_id, self.env.company, date, round=False)
    #
    #         if not suitable_rule:
    #             cur = product.currency_id
    #             price = cur._convert(price, self.currency_id, self.env.company, date, round=False)
    #
    #         results[product.id] = (price, suitable_rule and suitable_rule.id or False)
    #
    #     return results


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    applied_on = fields.Selection(selection_add=[('4_product_brand', 'Product Brand')],
                                  ondelete={'4_product_brand': 'cascade'})
    brand_id = fields.Many2one("product.brand", string="Brand")

    @api.depends('applied_on', 'categ_id', 'product_tmpl_id', 'product_id', 'compute_price', 'fixed_price',
                 'pricelist_id', 'percent_price', 'price_discount', 'price_surcharge')
    def _get_pricelist_item_name_price(self):
        super(ProductPricelistItem, self)._get_pricelist_item_name_price()
        for item in self:
            if item.brand_id and item.applied_on == '4_product_brand':
                item.name = _("Brand: %s") % (item.brand_id.name)

    @api.constrains('product_id', 'product_tmpl_id', 'categ_id')
    def _check_product_consistency(self):
        super(ProductPricelistItem, self)._check_product_consistency()
        for item in self:
            if item.applied_on == "4_product_brand" and not item.brand_id:
                raise ValidationError(_("Please specify the brand for which this rule should be applied"))

