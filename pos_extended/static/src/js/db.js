odoo.define('pos_extended.db', function (require) {
    "use strict";
    var PosDB = require('point_of_sale.DB');

    PosDB.include({
        init: function (options) {
            this.refund_voucher_by_barcode = {};
            this.return_reason_by_id = {};
            this._super.apply(this, arguments);
        },
        get_refund_voucher_by_barcode: function (code) {
            return this.refund_voucher_by_barcode[code];
        },
        get_return_reason_by_id: function (id) {
            return this.return_reason_by_id[id];
        },
        add_refund_vouchers: function (refund_vouchers) {
            if (!(refund_vouchers instanceof Array)) {
                refund_vouchers = [refund_vouchers];
            }
            for (const refund_voucher of refund_vouchers) {
                this.refund_voucher_by_barcode[refund_voucher.name] = refund_voucher;
            }
        },
        add_return_reasons: function (return_reasons) {
            if (!(return_reasons instanceof Array)) {
                return_reasons = [return_reasons];
            }
            for (const return_reason of return_reasons) {
                this.return_reason_by_id[return_reason.id] = return_reason;
            }
        },
    });
    return PosDB;
});
