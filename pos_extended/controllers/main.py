# -*- coding: utf-8 -*-
import logging
from odoo.http import Response, request

from odoo import http
from odoo.addons.point_of_sale.controllers.main import PosController
from odoo.addons.bus.controllers.main import BusController
from odoo.osv.expression import AND

_logger = logging.getLogger(__name__)


class PosControllerExt(PosController):

    @http.route('/pos/check_connection', type='json', auth='none', website=True)
    def check_connection(self):
        return Response('success', status=200)

    @http.route(['/pos/web', '/pos/ui'], type='http', auth='user')
    def pos_web(self, config_id=False, **k):
        domain = [
            ('state', 'in', ['opening_control', 'opened']),
            ('user_id', '=', request.session.uid),
            ('rescue', '=', False)
        ]
        if config_id:
            domain = AND([domain, [('config_id', '=', int(config_id))]])
        pos_session = request.env['pos.session'].sudo().search(domain, limit=1)

        if not pos_session and config_id:
            domain = [
                ('state', 'in', ['opening_control', 'opened']),
                ('rescue', '=', False),
                ('config_id', '=', int(config_id)),
            ]
            pos_session = request.env['pos.session'].sudo().search(domain, limit=1)
        if not pos_session:
            return request.redirect('/web#action=point_of_sale.action_client_pos_menu')

        pos_config_id = pos_session.config_id
        current_user_id = request.env.user
        no_access_to_another_users_session = pos_config_id.current_user_id != current_user_id and not current_user_id.access_other_users_session_pos
        if no_access_to_another_users_session:
            return request.redirect('/web#action=point_of_sale.action_client_pos_menu')

        return super(PosControllerExt, self).pos_web(config_id, **k)