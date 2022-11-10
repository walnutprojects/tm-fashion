odoo.define('pos_extended.PaymentScreenStatus', function (require) {
    'use strict';

    const PaymentScreenStatus = require('point_of_sale.PaymentScreenStatus');
    const Registries = require('point_of_sale.Registries');

    const PaymentScreenStatusExt = PaymentScreenStatus =>
        class extends PaymentScreenStatus {
            // get totalDueText() {
            //     if (this.currentOrder.get_money_adjustment_due()) {
            //         return this.env.pos.format_currency(this.currentOrder.get_money_adjustment_due());
            //     }
            //     return super.totalDueText;
            // }
        };

    Registries.Component.extend(PaymentScreenStatus, PaymentScreenStatusExt);
    return PaymentScreenStatusExt;
});
