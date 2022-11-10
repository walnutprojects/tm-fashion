odoo.define('pos_extended.Orderline', function (require) {
    'use strict';

    const Orderline = require('point_of_sale.Orderline');
    const {patch} = require('web.utils');


    patch(Orderline.prototype, 'pos_extended.Orderline', {
        get returnReason() {
            return this.env.pos.db.get_return_reason_by_id(this.props.line.get_return_reason());
        }
    });
});
