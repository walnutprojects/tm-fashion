# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
import requests
from werkzeug.urls import url_join

from odoo import _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round, float_is_zero, float_repr

import hmac
import hashlib
import base64
from Crypto.Cipher import AES
import json


class OceanAPI():
    "Implementation of Ocean API"

    def __init__(self, base_url, private_key, public_key, debug_logger):
        self.private_key = private_key
        self.public_key = public_key
        self.base_url = base_url
        #self.debug_logger = debug_logger
        self.authorization_token = self._get_authorization_token()

    def _get_authorization_token(self):
        hmc = hmac.new(bytes(self.private_key, 'utf-8'), digestmod=hashlib.sha256)
        hmc.update(self.public_key.encode('utf-8'))
        authorization_token = base64.b64encode(bytes(self.public_key + ':' + str(base64.b64encode(hmc.digest()), 'utf-8'), 'utf-8'))
        return str(authorization_token, 'utf-8')

    def make_api_request(self, endpoint,  data=None):
        """make an api call, return response"""
        access_url = url_join(self.base_url, endpoint)
        try:
            #self.debug_logger("%s\n%s\n%s" % (access_url, request_type, data if data else None), 'ocean_api%s' % endpoint)
            response = requests.get(access_url, headers={'Authorization': 'Basic %s' % self.authorization_token,
                                                         'Accept-Encoding': 'gzip, deflate, br',
                                                         'Accept': '*/*'}, timeout=180, data=data)
            #self.debug_logger("%s\n%s" % (response.status_code, response.text), '%s' % endpoint)
            if response.status_code != 200:
                response = response.json()
                # check for any error in response
                if 'error' in response:
                    error_message = response['error'].get('message')
                    error_detail = response['error'].get('errors')
                    if error_detail:
                        error_message += ''.join(['\n - %s: %s' % (err.get('field', _('Unspecified field')),
                                                                   err.get('message', _('Unknown error'))) for err in
                                                  error_detail])
                    raise UserError(_('Returned an error: %s', error_message))
            else:
                cipher_bytes = base64.b64decode(response.text)
                cipher = AES.new(self.private_key, AES.MODE_CBC, self.public_key)

                decrypted_bytes = cipher.decrypt(cipher_bytes)
                if decrypted_bytes[-1:] not in (b']', b'}'):
                    decrypted_bytes = decrypted_bytes.rstrip(decrypted_bytes[-1:])
                if decrypted_bytes[-1:] != b']':
                    decrypted_bytes += bytes(']', 'utf-8')
                try:
                    return json.loads(str(bytes('[{"TotalResultCount"', 'utf-8') + decrypted_bytes[20:], 'utf-8'))
                except Exception as e:
                    raise UserError(_('Invalid response'))
            return response
        except Exception as e:
            raise e

