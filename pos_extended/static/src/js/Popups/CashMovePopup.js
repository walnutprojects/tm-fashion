odoo.define('pos_extended.CashMovePopup', function (require) {
    'use strict';

    const CashMovePopup = require('point_of_sale.CashMovePopup');
    const Registries = require('point_of_sale.Registries');
    const {_t} = require('web.core');

    const CashMovePopupExt = CashMovePopup =>
        class extends CashMovePopup {
            confirm() {
                if (this.state.inputReason == '') {
                    this.state.inputHasError = true;
                    this.errorMessage = this.env._t('Please enter a reason before confirming.');
                    return;
                }
                return super.confirm();
            }
        };

    Registries.Component.extend(CashMovePopup, CashMovePopupExt);
    return CashMovePopupExt;
});
