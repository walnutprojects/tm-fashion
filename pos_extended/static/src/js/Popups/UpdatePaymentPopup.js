odoo.define('pos_extended.UpdatePaymentPopup', function (require) {
    'use strict';

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const models = require('point_of_sale.models');

    class UpdatePaymentPopup extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            this.payment_methods_from_config = this.env.pos.payment_methods.filter(method => this.env.pos.config.payment_method_ids.includes(method.id));
        }

        // setup() {
        // }

        get paymentLines() {
            return this.props.order.get_paymentlines()
        }

        get paymentMethods() {
            return this.payment_methods_from_config.filter(method => !method.is_refund)
        }

        async confirm() {
            const {order} = this.props;
            const paymentVals = [];
            $(this.el).find('tr.payment-line').each(function () {
                const $tr = $(this);
                paymentVals.push({
                    'payment_method_id': parseInt($tr.find('select[name="payment_method_id"] option:selected').val()),
                });
            });

            var [updated_order] = await this.rpc({
                model: 'pos.order',
                method: 'update_payment_lines',
                args: [order.backendId, paymentVals],
            });
            this.props.widget._state.syncedOrders.cache[updated_order.id] = new models.Order({}, {
                pos: this.env.pos,
                json: updated_order
            });
            this.trigger('close-popup');
        }
    }


    Registries.Component.add(UpdatePaymentPopup);

    return UpdatePaymentPopup;

});