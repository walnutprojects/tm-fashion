# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class PosConfig(models.Model):
    _inherit = "pos.config"

    def open_ui(self):
        if self.current_user_id != self.env.user and not self.env.user.access_other_users_session_pos:
            raise UserError(_("You don't have permission to access another user's session!"))
        return super(PosConfig, self).open_ui()

    commission_journal_id = fields.Many2one(
        'account.journal', string='Commission Journal',
        domain=[('type', 'in', ('general', 'sale'))],
        help="Accounting journal used to post POS session payment method commission journal entries.",
        ondelete='restrict')
    order_mode = fields.Boolean(string="Order Mode", default=True)
    pos_logo = fields.Binary(string='POS Logo')
    show_barcode = fields.Boolean(string="Show Barcode")
    extended_order_container = fields.Boolean(string="Extended Order Container")
    merge_orderline = fields.Boolean(string='Merge OrderLine', default=True)
    set_og_cashier_for_refund = fields.Boolean(string="Set Original Cashier For Refund")
    allow_cashier_change_refund_orders = fields.Boolean(string="Allow Cashier Change For Refund")
    refund_other_pos_orders = fields.Boolean(string="Allow Other POS Orders Refund")
