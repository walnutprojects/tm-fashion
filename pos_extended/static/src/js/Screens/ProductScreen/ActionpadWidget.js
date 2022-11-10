odoo.define('pos_extended.ActionpadWidget', function (require) {
    'use strict';

    const ActionpadWidget = require('point_of_sale.ActionpadWidget');
    const {patch} = require('web.utils');


    patch(ActionpadWidget.prototype, 'pos_extended.ActionpadWidget', {
        mounted() {
            this._super(...arguments);
            const self = this;
            this.env.pos.get('selectedOrder').on('change:order_mode', () => {
                self.togglePayButton();
            });
            self.togglePayButton();
        },
        togglePayButton() {
            const self = this;
            const order = this.env.pos.get('selectedOrder');
            const order_mode = order.get_order_mode();
            $(self.el).find('button.pay').prop("disabled", order_mode !== 'sale');
        },
        willUnmount() {
            this._super(...arguments);
            this.env.pos.get('selectedOrder').off('change:order_mode', null, this);
        }
    });
});
