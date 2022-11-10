odoo.define('pos_extended.ControlButtonsInherit', function (require) {
    'use strict';

    const RefundButton = require('point_of_sale.RefundButton');
    const SetPricelistButton = require('point_of_sale.SetPricelistButton');
    const ProductInfoButton = require('point_of_sale.ProductInfoButton');
    const {patch} = require('web.utils');

    const patchObjects = [{
        obj: RefundButton.prototype,
        order_mode: 'sale'
    }, {
        obj: SetPricelistButton.prototype,
        order_mode: 'sale'
    }, {
        obj: ProductInfoButton.prototype,
        order_mode: 'sale'
    }];

    for (const patchObject of patchObjects) {
        patch(patchObject.obj, 'pos_extended.ControlButtonsInherit', {
            mounted() {
                const self = this;
                this.env.pos.get('selectedOrder').on('change:order_mode', () => {
                    self.renderElement();
                });
                self.renderElement();
            },
            renderElement() {
                var self = this;
                var order = this.env.pos.get('selectedOrder');
                const order_mode = order.get_order_mode();
                if (patchObject.obj === RefundButton.prototype) {
                    const show_refund_btn_pos = this.env.pos.get_pos_function_visibility_for_current_user('show_refund_btn_pos')
                    $(self.el).toggle(order_mode === patchObject.order_mode && show_refund_btn_pos);
                } else {
                    $(self.el).toggle(order_mode === patchObject.order_mode);
                }
            }
        });
    }
});
