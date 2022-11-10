odoo.define('pos_extended.models', function (require) {
    "use strict";

    const models = require('point_of_sale.models');
    const utils = require('web.utils');
    const round_pr = utils.round_precision;

    models.load_fields('res.users', ['show_cost_info_pos', 'show_discount_btn_pos', 'show_price_btn_pos', 'show_delete_btn_pos', 'show_refund_btn_pos', 'show_sign_change_btn_pos', 'show_cash_move_btn_pos', 'show_money_adjustment_pos']);
    models.load_fields('res.company', ['logo', 'street', 'city', 'state_id'])
    models.load_fields('pos.payment.method', ['note_required', 'restrict_close_with_balance']);
    models.load_fields('product.product', ['name_secondary']);

    models.load_models([{
        model: 'pos.return.reason',
        fields: ['name'],
        loaded: function (self, return_reasons) {
            self.db.add_return_reasons(return_reasons);
            self.return_reasons = return_reasons;
        },
    }]);

    const _super_posmodel = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function () {
            _super_posmodel.initialize.apply(this, arguments);
        },
        get_pos_function_visibility_for_current_user: function (type) {
            if (!type) return false;
            let user = this.env.pos.user;
            const cashier = this.env.pos.get_cashier();
            if (cashier.user_id) {
                [user] = this.env.pos.users.filter(user => user.id === this.env.pos.get_cashier().user_id[0]);
            }
            if (Array.isArray(type)) {
                return type.map(t => user[t]);
            } else {
                return user[type];
            }
        },
        format_currency: function (amount, precision) {
            var currency =
                this && this.currency
                    ? this.currency
                    : {symbol: '$', position: 'after', rounding: 0.01, decimals: 3};

            amount = this.format_currency_no_symbol(amount, currency.decimals, currency);

            if (currency.position === 'after') {
                return amount + ' ' + (currency.symbol || '');
            } else {
                return (currency.symbol || '') + ' ' + amount;
            }
        },

    });

    const _order_super = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function (attr, options) {
            _order_super.initialize.apply(this, arguments)
            if (!this.get_order_mode()) this.set_order_mode('sale');
            this.barcode = this.barcode || "";
            if (!this.barcode) this.set_barcode();
        },
        init_from_JSON: function (json) {
            _order_super.init_from_JSON.apply(this, arguments);
            this.set_order_mode(json.order_mode);
            this.barcode = json.barcode;
        },
        set_orderline_options: function (orderline, options) {
            _order_super.set_orderline_options.apply(this, arguments);
            if (options.lot_name !== undefined) {
                orderline.set_pack_lot_lines(orderline, options.lot_name);
            }
        },
        set_order_mode: function (mode) {
            this.set('order_mode', mode);
        },
        get_order_mode: function () {
            return this.get('order_mode') || '';
        },
        set_money_adjustment_due: function (due) {
            return this.set('money_adjustment_due', due);
        },
        get_money_adjustment_due: function (due) {
            return this.get('money_adjustment_due', 0);
        },
        get_excluded_product_ids: function () {
            const excluded_products_ids = [];
            if (this.pos.config.discount_product_id) excluded_products_ids.push(this.pos.config.discount_product_id[0]);
            if (this.pos.config.refund_voucher_product_id) excluded_products_ids.push(this.pos.config.refund_voucher_product_id[0]);
            return excluded_products_ids;
        },
        get_total_quantity: function () {
            var return_qty = 0;
            var sale_qty = 0;
            const excluded_products_ids = this.get_excluded_product_ids();
            for (const line of this.get_orderlines()) {
                if (excluded_products_ids.includes(line.get_product().id)) continue;
                if (line.get_quantity() < 0) {
                    return_qty += line.get_quantity();
                } else {
                    sale_qty += line.get_quantity();
                }
            }
            ;
            return [sale_qty, Math.abs(return_qty)];
        },
        // get_due: function (paymentline) {
        //     if (this.get_money_adjustment_due()) {
        //         if (!paymentline) {
        //             var due = this.get_money_adjustment_due() - this.get_total_paid();
        //         } else {
        //             var due = this.get_money_adjustment_due();
        //             var lines = this.paymentlines.models;
        //             for (var i = 0; i < lines.length; i++) {
        //                 if (lines[i] === paymentline) {
        //                     break;
        //                 } else {
        //                     due -= lines[i].get_amount();
        //                 }
        //             }
        //         }
        //         return round_pr(due, this.pos.currency.rounding);
        //     } else {
        //         return _order_super.get_due.apply(this, arguments);
        //     }
        // },
        set_barcode: function () {
            const self = this;
            const temp = Math.floor(100000000000 + Math.random() * 9000000000000)
            self.barcode = temp.toString();
        },
        set_employee: function (employee) {
            this.employee = employee;
            this.trigger('change');
        },
        get_employee: function () {
            return this.employee;
        },
        has_return_lines: function () {
            for (const orderline of this.get_orderlines()) {
                if (orderline.is_return_line()) {
                    return true;
                }
            }
            return false;
        },
        remove_orderline: function (line) {
            if (!Array.isArray(line)) line = [line];
            for (let l of line) {
                if (l != undefined && l.refunded_orderline_id) delete this.pos.toRefundLines[l.refunded_orderline_id];
            }
            _order_super.remove_orderline.apply(this, arguments);
        },
        export_as_JSON: function () {
            let json = _order_super.export_as_JSON.apply(this, arguments);
            return Object.assign(json, {
                order_mode: this.get_order_mode(),
                barcode: this.barcode,
            });
        },
        export_for_printing: function () {
            var result = _order_super.export_for_printing.apply(this, arguments);
            result.order_barcode = result.name.split(' ')[1];
            result.barcode = this.barcode;
            if (this.employee) {
                result.cashier = this.employee.name;
            }
            const [total_sale_qty, total_refund_qty] = this.get_total_quantity();
            result.total_sale_qty = total_sale_qty;
            result.total_refund_qty = total_refund_qty;
            return result;
        },
    });


    var OrderlineSuper = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        init_from_JSON: function (json) {
            OrderlineSuper.init_from_JSON.apply(this, arguments);
            this.set_return_reason(json.return_reason);
        },
        set_return_reason: function (return_reason) {
            this.set('return_reason', return_reason);
        },
        set_pack_lot_lines: function (orderline, lot_name) {
            const payload = {newArray: [{id: 0, text: lot_name}]}
            const modifiedPackLotLines = Object.fromEntries(
                payload.newArray.filter(item => item.id).map(item => [item.id, item.text])
            );
            const newPackLotLines = payload.newArray
                .filter(item => !item.id)
                .map(item => ({lot_name: item.text}));

            orderline.setPackLotLines({modifiedPackLotLines, newPackLotLines});
        },
        get_return_reason: function () {
            return this.get('return_reason') || '';
        },
        is_return_line: function () {
            const discount_product_id = this.pos.config.discount_product_id && this.pos.config.discount_product_id[0];
            return this.get_quantity() < 0 && this.get_product().id !== discount_product_id;
        },
        can_be_merged_with: function (orderline) {
            if (!this.pos.config.merge_orderline) return false;
            return OrderlineSuper.can_be_merged_with.apply(this, arguments);
        },
        export_as_JSON: function () {
            var json = OrderlineSuper.export_as_JSON.apply(this, arguments);
            json.return_reason = this.get_return_reason();
            return json;
        },
        export_for_printing: function () {
            var result = OrderlineSuper.export_for_printing.apply(this, arguments);
            result.product_name_secondary = this.get_product().name_secondary;
            if (result.product_name_secondary) {
                result.product_name_wrapped[0] += `- ${result.product_name_secondary}`;
            }
            return result;
        },
    });

    var _super_paymentline = models.Paymentline.prototype;
    models.Paymentline = models.Paymentline.extend({
        initialize: function (attr, options) {
            _super_paymentline.initialize.apply(this, arguments);
            this.note = this.note || "";
        },
        init_from_JSON: function (json) {
            _super_paymentline.init_from_JSON.apply(this, arguments);
            this.set_note(json.note);
        },
        set_note: function (note) {
            this.note = note || '';
            this.trigger('change', this);
        },
        get_note: function () {
            return this.note;
        },
        export_as_JSON: function () {
            let json = _super_paymentline.export_as_JSON.apply(this, arguments);
            return Object.assign(json, {
                note: this.get_note(),
            });
        },
        export_for_printing: function () {
            let result = _super_paymentline.export_for_printing.apply(this, arguments);
            result.note = this.note;
            return result;
        }
    });
});
