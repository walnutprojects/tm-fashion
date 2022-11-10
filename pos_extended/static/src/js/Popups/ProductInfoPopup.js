odoo.define('pos_extended.ProductInfoPopup', function (require) {
    "use strict";

    const ProductInfoPopup = require('point_of_sale.ProductInfoPopup');
    const Registries = require('point_of_sale.Registries');


    const ProductInfoPopupExt = ProductInfoPopup =>
        class extends ProductInfoPopup {
            mounted() {
                Registries.Component.baseNameMap.ProductInfoPopup.prototype.mounted.apply(this, arguments);
                this.toggleCostInfo();
            }

            toggleCostInfo() {
                const $el = $(this.el);
                const show_cost_info_pos = this.env.pos.get_pos_function_visibility_for_current_user('show_cost_info_pos');
                $el.find('td:contains("Cost:")').parent().toggle(show_cost_info_pos)
                $el.find('td:contains("Total Cost:")').parent().toggle(show_cost_info_pos)
                $el.find('td:contains("Margin:")').parent().toggle(show_cost_info_pos)
                $el.find('td:contains("Total Margin:")').parent().toggle(show_cost_info_pos)
            }
        };

    Registries.Component.extend(Registries.Component.baseNameMap.ProductInfoPopup, ProductInfoPopupExt);

    return ProductInfoPopup;

});

