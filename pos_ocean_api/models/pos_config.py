# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from .oceanapi import OceanAPI
from datetime import datetime
import calendar
import pytz
import hashlib
import json


class PosConfig(models.Model):
    _inherit = "pos.config"
    is_ocean_api = fields.Boolean('POS Used for Ocean API')
    ocean_server_url = fields.Char('Server URL')
    ocean_private_key = fields.Char('Private Key')
    ocean_public_key = fields.Char('Public Key')
    date_last_imported = fields.Datetime('Last imported on')
    ocean_product_category_id = fields.Many2one('product.category', 'Category for Products in Ocean')

    def create_ocean_import_logs(self, order_details, fetch_log):
        log_obj = self.env['ocean.import.log']
        for data in order_details:
            data.pop('TotalResultCount')
            json_string = json.dumps(data)
            checksum = hashlib.md5(json_string.encode('utf-8')).hexdigest()
            log = log_obj.search([('checksum', '=', checksum)])
            if not log:
                log_obj.create({
                    'ocean_fetch_id': fetch_log.id,
                    'pos_config_id': self.id,
                    'json_data': json_string,
                    'checksum': checksum,
                })

    def get_ocean_orders(self, api, fromdate, todate, page_no=1, page_size=100):
        endpoint = 'SalesInvoice/Modify?PageSize=%s&PageNumber=%s&FromDate=%s&ToDate=%s' % (page_size, page_no,
                                                                                            fromdate, todate)
        #@TODO :write error details in fetch log
        try:
            orders = api.make_api_request(endpoint)
            if orders:# and type(orders) is list:
                if orders[0].get('TotalResultCount', 0) > (page_no * page_size):
                    page_no += 1
                    orders += self.get_ocean_orders(api, fromdate, todate, page_no, page_size)
            return orders
        except Exception as e:
            raise e

    def fetch_ocean_orders(self, page_size=100):
        for pos_config in self.search([]).filtered(lambda r: r.is_ocean_api and r.date_last_imported):
            api = OceanAPI(pos_config.ocean_server_url, pos_config.ocean_private_key, pos_config.ocean_public_key,
                           pos_config.name)
            current_time = datetime.now()

            todate = calendar.timegm(current_time.timetuple())
            fromdate = calendar.timegm(pos_config.date_last_imported.timetuple())
            fetch_log = self.env['ocean.fetch.log'].create({
                'request_params': str(fromdate) + ',' + str(todate),
                'pos_config_id': pos_config.id,
            })
            self._cr.commit()
            order_details = pos_config.get_ocean_orders(api, fromdate, todate, page_size=page_size)
            self._cr.commit()
            if not fetch_log.error_messages:
                pos_config.create_ocean_import_logs(order_details, fetch_log)
                pos_config.date_last_imported = current_time.strftime('%Y-%m-%d %H:%M:%S')

    def ocean_session_close(self):
        for pos_config in self.search([]).filtered(lambda r: r.is_ocean_api):
            if pos_config.current_session_id and not pos_config.current_session_id.rescue:
                session = pos_config.current_session_id
                if session.state == 'opened':
                    session.post_closing_cash_details(session.cash_register_balance_end)
                    session.update_closing_control_state_session('Closing ocean session.')
                    difference_pairs = [[2, 0]]#TODO Make it with bank payments
                    session.close_session_from_ui(difference_pairs)

