odoo.define('pos_extended.SetReturnReasonButton', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const {useListener} = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');

    class SetReturnReasonButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click', this.onClick);
        }

        mounted() {
            this.currentOrder.orderlines.on('add remove change', () => {
                this.toggleEl();
            }, this);
            this.toggleEl();
        }

        toggleEl() {
            const order = this.env.pos.get('selectedOrder');
            const has_return_lines = order.has_return_lines();
            $(this.el).toggle(has_return_lines);
        }

        get currentOrder() {
            return this.env.pos.get_order();
        }

        get currentOrderLine() {
            return this.currentOrder.get_selected_orderline();
        }

        get selectedReasonObj() {
            return this.env.pos.db.get_return_reason_by_id(this.currentOrderLine);
        }

        get ReturnReasonList() {
            const selectedReason = this.currentOrderLine.get_return_reason();
            return this.env.pos.return_reasons.map(reason => ({
                id: reason.id,
                label: reason.name,
                isSelected: selectedReason === reason.id,
                item: reason.id,
            }));
        }

        async onClick() {
            if (!this.currentOrderLine.is_return_line()) {
                this.showNotification(
                    _.str.sprintf(this.env._t('Please select a return line!')),
                    3000
                );
                return;
            }
            const selectionList = this.ReturnReasonList;
            let {confirmed, payload: selectedReason} = await this.showPopup('SelectionPopup', {
                title: this.env._t('Set Return Reason'),
                list: selectionList,
            });
            if (confirmed) {
                this.currentOrderLine.set_return_reason(selectedReason);
            }
        }
    }

    SetReturnReasonButton.template = 'SetReturnReasonButton';

    ProductScreen.addControlButton({
        component: SetReturnReasonButton,
        condition: function () {
            return true;
        },
    });

    Registries.Component.add(SetReturnReasonButton);

    return SetReturnReasonButton;
});
