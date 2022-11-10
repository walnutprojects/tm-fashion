odoo.define("pos_extended.ProductScreen", function (require) {
    "use strict";

    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');

    const PosProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            mounted() {
                super.mounted();
                if (!this.env.isMobile && this.env.pos.config.extended_order_container) {
                    $(".pads").appendTo(".rightpane");
                }
            }
        }

    Registries.Component.extend(ProductScreen, PosProductScreen);

    return ProductScreen;
});

