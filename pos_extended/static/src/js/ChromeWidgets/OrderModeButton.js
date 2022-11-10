odoo.define('pos_extended.OrderModeButton', function (require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    const {isConnectionError} = require('point_of_sale.utils');
    const {useListener} = require('web.custom_hooks');


    class OrderModeButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click', this.onClick);
        }

        get current_order_mode() {
            const order = this.env.pos.get_order();
            return order ? order.get_order_mode() ? order.get_order_mode() : 'mode' : 'mode';
        }

        mounted() {
            this.env.pos.get('orders').on('add remove change', () => this.render(), this);
            this.env.pos.on('change:selectedOrder', () => this.render(), this);
        }

        willUnmount() {
            this.env.pos.get('orders').off('add remove change', null, this);
            this.env.pos.off('change:selectedOrder', null, this);
        }

        getOrderModes() {
            return [{
                id: 1,
                label: "Sale",
                isSelected: false,
                item: 'sale',
            }];
        }

        async onClick() {
            const self = this;
            const selectionList = this.getOrderModes();
            const {confirmed, payload: selectedOrderMode} = await this.showPopup('SelectionPopup', {
                title: this.env._t('Order Mode'),
                list: selectionList,
            });
            if (confirmed) {
                const order = self.env.pos.get_order();
                if (selectedOrderMode === 'sale') {
                    order.set_order_mode(selectedOrderMode);
                    order.remove_orderline(order.get_orderlines());
                } else {
                    try {
                        const res = await this.rpc({
                            route: '/pos/check_connection',
                        })
                        if (res) {
                            order.set_order_mode(selectedOrderMode);
                            order.remove_orderline(order.get_orderlines());
                        }
                    } catch (error) {
                        if (isConnectionError(error)) {
                            self.showPopup('ErrorPopup', {
                                title: self.env._t('Network Error'),
                                body: self.env._t(`Unable to switch to ${selectedOrderMode} mode if offline.`),
                            });
                        } else {
                            throw error;
                        }
                    }
                }
            }
        }
    }

    OrderModeButton.template = 'point_of_sale.OrderModeButton';

    Registries.Component.add(OrderModeButton);

    return OrderModeButton;
});
