# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ResUsers(models.Model):
    _inherit = "res.users"

    show_cost_info_pos = fields.Boolean(string="Show Cost Information?", default=True)
    show_discount_btn_pos = fields.Boolean(string="Show Discount Button?", default=True)
    show_price_btn_pos = fields.Boolean(string="Show Price Button?", default=True)
    show_delete_btn_pos = fields.Boolean(string="Show Delete Button?", default=True)
    show_refund_btn_pos = fields.Boolean(string="Show Refund Button?", default=True)
    show_sign_change_btn_pos = fields.Boolean(string="Show Sign Change Button?", default=True)
    show_cash_move_btn_pos = fields.Boolean(string="Show Cash Move Button?", default=True)
    show_all_wh_info_pos = fields.Boolean(string="Show Qty in All WH?", default=True)
    show_money_adjustment_pos = fields.Boolean(string="Show Money Adjustment?")
    access_other_users_session_pos = fields.Boolean(string="Access Other User's Session?", default=False)
