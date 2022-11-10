# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError
import json
from datetime import datetime
import hashlib


class PosOrder(models.Model):
    _inherit = "pos.order"

    ocean_invoice_type_id = fields.Many2one('ocean.invoice.type', 'Ocean Invoice Type')
    ocean_invoice_number = fields.Char('Ocean Invoice Number')
    ocean_modification_date = fields.Datetime('Ocean Modification Date')
    ocean_import_log_ids = fields.One2many('ocean.import.log', 'order_id', 'Ocean Import Log', readonly=True)


class OceanInvoiceType(models.Model):
    _name = 'ocean.invoice.type'
    _rec_name = 'invoice_type_en_name'

    ocean_id = fields.Integer('Ocean ID')
    invoice_type_ar_name = fields.Char('Arabic Name')
    invoice_type_en_name = fields.Char('English Name')


class OceanFetchLog(models.Model):
    _name = 'ocean.fetch.log'

    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company, readonly=True)
    pos_config_id = fields.Many2one('pos.config', 'POS Config', readonly=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user, readonly=True)
    date_create = fields.Datetime('Create Date', default=lambda self: fields.Datetime.now(), readonly=True)
    request_params = fields.Text('Request Params', readonly=True)
    error_messages = fields.Text('Error Messages', readonly=True)
    ocean_import_log_ids = fields.One2many('ocean.import.log', 'ocean_fetch_id', 'Fetch Log', readonly=True)


class OceanImportLog(models.Model):
    _name = "ocean.import.log"
    _order = 'id asc'

    ocean_fetch_id = fields.Many2one('ocean.fetch.log', 'Fetch Log', readonly=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company, readonly=True)
    pos_config_id = fields.Many2one('pos.config', 'POS Config', readonly=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user, readonly=True)
    date_create = fields.Datetime('Create Date', default=lambda self: fields.Datetime.now(), readonly=True)
    json_data = fields.Text('JSON Data', readonly=True)
    order_id = fields.Many2one('pos.order', 'Order', readonly=True)
    error_messages = fields.Text('Error Messages', readonly=True)
    update_done = fields.Boolean('Update done?', default=False, readonly=True)
    checksum = fields.Char('Checksum')

    @api.depends('json_data')
    def _compute_check_sum(self):
        for log in self:
            data = json.loads(log.json_data)
            data['TotalResultCount'] = 0
            json_string = json.dumps(data)
            checksum = hashlib.md5(json_string.encode('utf-8')).hexdigest()
            log.checksum = checksum

    @api.model
    def get_ocean_session(self):
        if self.pos_config_id.current_session_id and self.pos_config_id.current_session_id.state == 'opened':
            return self.pos_config_id.current_session_id
        session = self.env['pos.session'].search([('config_id', '=', self.pos_config_id.id),
                                               ('state', '=', 'opened'), ('rescue', '=', False)], limit=1)
        if not session:
            session = self.env['pos.session'].search([('config_id', '=', self.pos_config_id.id),
                                            ('state', '=', 'opening_control'), ('rescue', '=', False)], limit=1)
            if not session:
                session = self.env['pos.session'].create({
                    'user_id': self.env.uid,
                    'config_id': self.pos_config_id.id
                })
            if session.state == 'opening_control':
                session.state = 'opened'
                session.set_cashbox_pos(session.cash_register_balance_start, 'Session Opened')
        if session.state != 'opened':
            raise UserError('Failed to open session for Ocean orders')
        return session

    @api.model
    def get_invoice_type(self, order_data):
        invoice_type = self.env['ocean.invoice.type'].search([('ocean_id', '=', order_data['InvoiceTypeId'])], limit=1)
        if not invoice_type:
            invoice_type = self.env['ocean.invoice.type'].create({
                'ocean_id': order_data['InvoiceTypeId'],
                'invoice_type_ar_name': order_data['InvoiceTypeArName'],
                'invoice_type_en_name': order_data['InvoiceTypeEnName'],
            })
        return invoice_type

    @api.model
    def get_customer(self, order_data):
        customer = self.env['res.partner'].search([('ocean_id', '=', order_data['CustomerID'])], limit=1)
        if not customer:
            customer = self.env['res.partner'].create({
                'customer_rank': 1,
                'is_company': False,
                'name': order_data['CustomerName'],
            })
        return customer

    @api.model
    def get_user(self, order_data):
        user = self.env['res.users'].search([('ocean_id', '=', order_data['EmployeeID'])], limit=1)
        if not user:
            user = self.env['res.users'].create({
                'ocean_id': order_data['EmployeeID'],
                'name': order_data['EmployeeEnName'],
                'ocean_employee_ar_name': order_data['EmployeeArName'],
                'login': order_data['EmployeeID'],
            })
        return user

    @api.model
    def get_product(self, line_data):
        product = self.env['product.product'].search([('ocean_id', '=', line_data["ItemID"])], limit=1)
        if not product:
            product = self.env['product.product'].create({
                'ocean_id': line_data['ItemID'],
                'name': line_data['ProductEnName'],
                'name_secondary': line_data['ProductArName'],
                'detailed_type': 'product',
                'categ_id': self.pos_config_id.ocean_product_category_id.id,
                'taxes_id': [(6, 0, [])],
                'supplier_taxes_id': [(6, 0, [])],
                'barcode': line_data['BarCode'],
                'default_code': line_data['SKU'],
                'available_in_pos': True,
                'lst_price': line_data['Price'],#@TODO : Currently all quantity is 1, and no FC
                'standard_price': line_data['Cost'],#@TODO : Currently all quantity is 1, and no FC
            })
        return product

    @api.model
    def get_payment_method(self, payment_data):
        payment_method = self.env['pos.payment.method'].search([('ocean_id', '=', payment_data["PaymentTypeID"])], limit=1)
        if not payment_method:
            payment_method = self.env['pos.payment.method'].create({
                'ocean_id': payment_data['PaymentTypeID'],
                'name': payment_data['PayTypeEnName'] or payment_data['PaymentTypeID'],
            })
            self.env.cr.execute('''INSERT INTO pos_config_pos_payment_method_rel 
                (pos_config_id, pos_payment_method_id) VALUES (%s, %s)
             ''', (self.pos_config_id.id, payment_method.id))
        return payment_method

    def synchronize_ocean_orders(self):
        # @TODO : Put in try catch and show exceptions in error messages
        if not self:
            logs = self.search([('update_done', '=', False)])
        else:
            logs = self
        for log in logs:
            order_data = json.loads(log.json_data)
            if not log.order_id:
                session = log.get_ocean_session()
                invoice_type = log.get_invoice_type(order_data)
                date_order = datetime.strptime(order_data['InvoiceDate'][:11] + order_data['InvoiceTime'][11:],
                                               '%Y-%m-%dT%H:%M:%S')
                customer = log.get_customer(order_data)
                user = log.get_user(order_data)
                #@TODO: Tax & FC
                order_vals = {
                    'company_id': log.pos_config_id.company_id.id,
                    'session_id': session.id,
                    'ocean_invoice_type_id': invoice_type.id,
                    'date_order': date_order,
                    'partner_id': customer.id,
                    'currency_id': log.pos_config_id.pricelist_id.currency_id.id,
                    'pricelist_id': log.pos_config_id.pricelist_id.id,
                    'note': order_data['Notes'],
                    'user_id': user.id,
                    'amount_tax': order_data['Tax'],
                    'amount_total': order_data['FinalValue'],
                    'amount_paid': order_data['FinalValue'],
                    'amount_return': order_data['ReturnCash'],
                    #'state': 'paid',
                    #branch_id
                    #costcenter
                }
                lines = []
                for line_data in order_data["SalesInvoiceItems"]:
                    product = log.get_product(line_data)
                    line_vals = {
                        'product_id': product.id,
                        'full_product_name': line_data['SKU'] + ' ' + product.name,
                        'qty': line_data["Quantity"],
                        'price_unit': line_data["Price"],
                        'total_cost': line_data["Cost"],
                        'is_total_cost_computed': True,
                        'discount':  100.00 * (1.00 - float(line_data["FinalPrice"])/(line_data["Price"]*line_data["Quantity"])),
                        'discount_amount': line_data["DiscountVal"],
                        'notice': line_data["Notes"],
                        'price_subtotal': line_data["FinalPrice"],
                        'price_subtotal_incl': line_data["FinalPrice"],
                    }
                    lines.append((0, 0, line_vals))
                order_vals['lines'] = lines

                payment_lines = []
                for payment_data in order_data["SalesInvoicePayments"]:
                    payment_method = log.get_payment_method(payment_data)
                    payment_vals = {
                        'payment_method_id': payment_method.id,
                        'amount': payment_data["Value"],
                        'transaction_id': payment_data["ApprovalNo"],
                        'note': payment_data["CardNo"],
                    }
                    payment_lines.append((0, 0, payment_vals))
                order_vals['payment_ids'] = payment_lines
                order = self.env['pos.order'].create(order_vals)
                order.state = 'paid'
                log.order_id = order
                log.update_done = True


class ResPartner(models.Model):

    _inherit = 'res.partner'

    ocean_id = fields.Integer('Ocean ID')


class ResUser(models.Model):

    _inherit = 'res.users'

    ocean_id = fields.Char('Ocean Employee ID')
    ocean_employee_ar_name = fields.Char('Ocean Employee Arabic Name')


class ProductProduct(models.Model):

    _inherit = 'product.product'

    ocean_id = fields.Integer('Ocean ID')


class PosPaymentMethod(models.Model):

    _inherit = 'pos.payment.method'

    ocean_id = fields.Integer('Ocean ID')


