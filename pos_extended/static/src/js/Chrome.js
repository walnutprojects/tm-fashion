odoo.define('pos_extended.Chrome', function (require) {
    'use strict';

    const Chrome = require('point_of_sale.Chrome');
    const Registries = require('point_of_sale.Registries');

    const ChromeExt = (Chrome) =>
        class extends Chrome {
            async start() {
                await super.start();
                this.env.pos.on('change:cashier', this.render, this);
            }

            showOrderModeButton() {
                return this.env.pos && this.env.pos.config && this.env.pos.config.order_mode;
            }

            showCashMoveButton() {
                const res = super.showCashMoveButton();
                if (res && this.env.pos.users && this.env.pos.users.length) {
                    return this.env.pos.get_pos_function_visibility_for_current_user('show_cash_move_btn_pos')
                }
                return res;
            }
        };

    Registries.Component.extend(Chrome, ChromeExt);

    return Chrome;

});
