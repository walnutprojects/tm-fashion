odoo.define('pos_sale_extended.CashierName', function (require) {
    'use strict';
    const CashierName = require('pos_hr.CashierName');
    const Registries = require('point_of_sale.Registries');

    const CashierNameExt = (CashierName) =>
        class extends CashierName {
            mounted() {
                super.mounted();
                this.env.pos.on('change:selectedOrder', this.checkCashier, this);
            }

            willUnmount() {
                this.env.pos.off('change:selectedOrder', null, this);
            }

            checkCashier() {
                const order = this.env.pos.get_order();
                if (order.get_employee() != this.env.pos.get_cashier()) {
                    this.env.pos.set_cashier(order.get_employee());
                }
            }

            async selectCashier() {
                const is_refund_order = this.env.pos.get_order().getHasRefundLines();
                if (is_refund_order && !this.env.pos.config.allow_cashier_change_refund_orders) {
                    return this.showNotification(
                        _.str.sprintf('Sorry, Cashier cannot be changed for this order.'),
                        3000
                    );
                }
                return await super.selectCashier();
            }
        };

    Registries.Component.extend(CashierName, CashierNameExt);

    return CashierName;
});
