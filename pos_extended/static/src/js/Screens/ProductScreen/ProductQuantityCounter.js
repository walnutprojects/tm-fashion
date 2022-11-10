odoo.define('pos_extended.ProductQuantityCounter', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const utils = require('web.utils');

    const round_pr = utils.round_precision;

    class ProductQuantityCounter extends PosComponent {
        get_total_quantity() {
            return this.order.get_total_quantity();
        }

        get_total_sale_quantity() {
            return this.get_total_quantity()[0];
        }

        get_total_refund_quantity() {
            return this.get_total_quantity()[1];
        }

        get order() {
            return this.env.pos.get_order();
        }
    }

    ProductQuantityCounter.template = 'ProductQuantityCounter';

    Registries.Component.add(ProductQuantityCounter);

    return ProductQuantityCounter;
});
