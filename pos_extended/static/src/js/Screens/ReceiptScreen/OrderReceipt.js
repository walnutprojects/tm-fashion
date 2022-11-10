odoo.define('pos_extended.OrderReceipt', function (require) {
    "use strict";

    const OrderReceipt = require('point_of_sale.OrderReceipt');
    const Registries = require('point_of_sale.Registries');

    const OrderReceiptExt = OrderReceipt =>
        class extends OrderReceipt {
            constructor() {
                super(...arguments);
            }

            mounted() {
                super.mounted();
                this.renderBarcodes();
            }

            renderBarcodes() {
                const barcodeEl = $('.barcode');
                barcodeEl.each(function () {
                    const $el = $(this);
                    $el.JsBarcode(
                        $el.data('code'),
                        {
                            height: 50,
                            width: $el.data('width') || 1.1,
                            fontSize: 13,
                            displayValue: false,
                        }
                    );
                })
                return true;
            }

        };

    Registries.Component.extend(OrderReceipt, OrderReceiptExt);
    return OrderReceipt;
});