odoo.define('pos_extended.NumpadWidget', function (require) {
    'use strict';

    const NumpadWidget = require('point_of_sale.NumpadWidget');
    const Registries = require('point_of_sale.Registries');

    const NumpadWidgetExt = (NumpadWidget) =>
        class extends NumpadWidget {
            mounted() {
                super.mounted();
                const $el = $(this.el);
                const [show_discount_btn_pos, show_price_btn_pos, show_delete_btn_pos, show_sign_change_btn_pos] = this.env.pos.get_pos_function_visibility_for_current_user(['show_discount_btn_pos', 'show_price_btn_pos', 'show_delete_btn_pos', 'show_sign_change_btn_pos']);
                $el.find('.mode-button:contains("Disc")').css('visibility', show_discount_btn_pos ? 'visible' : 'hidden');
                $el.find('.mode-button:contains("Price")').css('visibility', show_price_btn_pos ? 'visible' : 'hidden');
                $el.find('.input-button.numpad-backspace').css('visibility', show_delete_btn_pos ? 'visible' : 'hidden');
                $el.find('.input-button.numpad-minus').css('visibility', show_sign_change_btn_pos ? 'visible' : 'hidden');
            }

            async checkDiscountManagerValidation(discount) {
                return true;
            }
            async checkPriceManagerValidation() {
                return true;
            }

            async changeMode(mode) {
                var self = this;
                var selected_orderline = self.env.pos.get_order().get_selected_orderline()
                if (selected_orderline) {
                    if (mode == 'discount') {
                        const {confirmed, payload} = await this.showPopup('NumberPopup', {
                            title: this.env._t('Discount Percentage'),
                            startingValue: selected_orderline.get_discount() || 0,
                            isInputSelected: true
                        });
                        if (confirmed) {
                            const val = Math.round(Math.max(0, Math.min(100, parseFloat(payload))));
                            const validationSuccess = await self.checkDiscountManagerValidation(val);
                            if (!validationSuccess) return;
                            selected_orderline.set_discount(val);
                        }
                    } else if (mode == 'price') {
                        const {confirmed, payload} = await this.showPopup('NumberPopup', {
                            title: this.env._t('Price'),
                            startingValue: selected_orderline.get_unit_price() || 0,
                            isInputSelected: true
                        });
                        if (confirmed) {
                            const validationSuccess = await self.checkPriceManagerValidation(payload);
                            if (!validationSuccess) return;
                            selected_orderline.price_manually_set = true;
                            selected_orderline.set_unit_price(payload);
                        }
                    }
                    super.changeMode('quantity');
                } else {
                    self.showPopup('ErrorPopup', {
                        'title': self.env._t('No Selected Orderline'),
                        'body': self.env._t('No order line is Selected. Please add or select an Orderline')
                    });
                    return;
                }

            }
        };
    Registries.Component.extend(NumpadWidget, NumpadWidgetExt);

    return NumpadWidgetExt;
});
