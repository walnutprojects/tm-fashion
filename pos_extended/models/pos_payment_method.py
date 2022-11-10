# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PoSPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    note_required = fields.Boolean(string="Note Required?")
    commission_type = fields.Selection([
        ('fixed', 'Fixed'),
        ('percent', 'Percentage')], string="Commission Type")
    commission_account_id = fields.Many2one('account.account', string="Commission Account")
    commission = fields.Float(string="Commission")
    restrict_close_with_balance = fields.Boolean("Restrict To Close With Balance")
