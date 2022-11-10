odoo.define('pos_extended.ClosePosPopup', function (require) {
    'use strict';

    const ClosePosPopup = require('point_of_sale.ClosePosPopup');
    const Registries = require('point_of_sale.Registries');
    const {_t} = require('web.core');

    const ClosePosPopupExt = ClosePosPopup =>
        class extends ClosePosPopup {
            mounted() {
                super.mounted();
                const $el = $(this.el);
                const show_money_adjustment_pos = this.env.pos.get_pos_function_visibility_for_current_user('show_money_adjustment_pos');
                $el.find('.button.money-adjustment').css('visibility', show_money_adjustment_pos ? 'visible' : 'hidden');
            }

            hasPaymentMethodBalanceRestriction() {
                for (const pm of this.otherPaymentMethods) {
                    const payment_method = this.env.pos.payment_methods_by_id[pm.id];
                    if (payment_method && payment_method.restrict_close_with_balance && pm.amount) {
                        return pm;
                    }
                }
                return false;
            }

            async filterPaymentOrders(payment_method) {
                this.trigger('close-popup');
                const searchDetails = {fieldName: 'PAYMENT_METHOD', searchTerm: payment_method};
                this.trigger('close-popup');
                this.showScreen('TicketScreen', {
                    ui: {filter: 'SYNCED', searchDetails},
                    destinationOrder: this.env.pos.get_order(),
                });
            }

            async moneyAdjustment(event) {
                const self = this;
                const totalDue = this.otherPaymentMethods.reduce(
                    (sum, pm) => sum + pm.amount,
                    self.defaultCashDetails.amount);
                const paymentMethods = this.env.pos.payment_methods.filter(
                    (method) => this.env.pos.config.payment_method_ids.includes(method.id) && method.type != 'pay_later'
                );
                const selectionList = paymentMethods.map((paymentMethod) => ({
                    id: paymentMethod.id,
                    label: paymentMethod.name,
                    item: paymentMethod,
                }));
                // const {confirmed, payload: selectedPaymentMethod} = await this.showPopup('SelectionPopup', {
                //     title: this.env._t('Select the payment method to settle the due'),
                //     list: selectionList,
                // });
                // if (!confirmed) return;
                const newOrder = this.env.pos.add_new_order({temporary: true});
                newOrder.set_money_adjustment_due(totalDue);
                // const payment = newOrder.add_paymentline(selectedPaymentMethod);
                // payment.set_amount(totalDue);
                this.trigger('close-popup');
                this.showScreen('PaymentScreen');
            }

            async closeSession() {
                const pm = this.hasPaymentMethodBalanceRestriction();
                if (pm) {
                    return this.showPopup('ErrorPopup', {
                        title: this.env._t('Closing Error'),
                        body: this.env._t(`${pm.name} has a closing balance restriction. Please move the funds.`),
                    });
                } else {
                    return super.closeSession();
                }
            }
        };

    Registries.Component.extend(ClosePosPopup, ClosePosPopupExt);
    return ClosePosPopupExt;
});
