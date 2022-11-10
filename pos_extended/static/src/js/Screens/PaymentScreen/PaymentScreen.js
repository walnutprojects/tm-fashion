odoo.define('pos_extended.PaymentScreen', function (require) {
    'use strict';

    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const {patch} = require('web.utils');

    patch(PaymentScreen.prototype, 'pos_extended.PaymentScreen', {
        addNewPaymentLine({detail: paymentMethod}) {
            // show payment note popup if note required
            if (paymentMethod.note_required) {
                this.showPopup('PaymentNotePopup', {
                    title: 'Payment Note',
                    callback: this._super.bind(this, {detail: paymentMethod})
                });
            } else return this._super({detail: paymentMethod});
        },
        async validateOrder(isForceValidate) {
            const order = this.env.pos.get_order();
            if (order && order.get_money_adjustment_due()) {
                if (order.get_total_paid() > order.get_money_adjustment_due()) {
                    await this.showPopup('ErrorPopup', {
                        title: this.env._t('Money Adjustment Mismatch'),
                        body: this.env._t("The amount of your payment lines must not be greater than total payments amount."),
                    });
                    return;
                }
            }

            this._super(isForceValidate);
        }

    });
});
