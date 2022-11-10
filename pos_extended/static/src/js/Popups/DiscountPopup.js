odoo.define('pos_extended.DiscountPopup', function (require) {
    'use strict';

    const NumberPopup = require('point_of_sale.NumberPopup');
    const NumberBuffer = require('point_of_sale.NumberBuffer');
    const {useState, useRef} = owl.hooks;

    const Registries = require('point_of_sale.Registries');

    class DiscountPopup extends NumberPopup {
        constructor() {
            super(...arguments);
        }

        mounted() {
            super.mounted();
            this.inputDiscountTypeRef.el.value = 'percentage';
        }

        setup() {
            super.setup();
            this.inputDiscountTypeRef = useRef('input-discount-type');
            this.state = useState({inputDiscountType: ''});
        }

        getPayload() {
            return {type: this.state.inputDiscountType, val: NumberBuffer.get()};
        }
    }

    DiscountPopup.template = 'DiscountPopup';

    Registries.Component.add(DiscountPopup);

    return NumberPopup;
});
