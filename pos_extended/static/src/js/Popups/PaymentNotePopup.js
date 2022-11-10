odoo.define('pos_extended.PaymentNotePopup', function (require) {
    'use strict';

    const NumberPopup = require('point_of_sale.NumberPopup');
    const Registries = require('point_of_sale.Registries');


    class PaymentNotePopup extends NumberPopup {
        constructor() {
            super(...arguments);
        }

        setup() {
            this.callback = this.props.callback;
        }

        confirm() {
            const note = this.getPayload();
            if (!note) {
                return;
            }
            this.callback();
            const order = this.env.pos.get_order();
            const selected_paymentline = order.selected_paymentline;
            selected_paymentline.set_note(note);
            this.trigger('close-popup')
        }
    }


    Registries.Component.add(PaymentNotePopup);

    return PaymentNotePopup;

});