# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class PosReturnReason(models.Model):
    _name = 'pos.return.reason'
    _description = "Pos Return Reasons"

    name = fields.Char(string='Reason', required=True)
