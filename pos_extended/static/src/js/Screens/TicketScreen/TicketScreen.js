odoo.define('pos_extended.TicketScreen', function (require) {
    'use strict';

    const models = require('point_of_sale.models');
    const TicketScreen = require('point_of_sale.TicketScreen');
    const {Gui} = require('point_of_sale.Gui');
    const {useListener} = require('web.custom_hooks');
    const {useBarcodeReader} = require('point_of_sale.custom_hooks');


    const Registries = require('point_of_sale.Registries');

    const TicketScreenExt = (TicketScreen) =>
        class extends TicketScreen {
            constructor() {
                super(...arguments);
                useListener('click-update-order', this.onUpdateOrderBtnClick);
                useListener('click-search-other-pos', this.onSearchOtherPosBtnClick);
                useBarcodeReader({
                    barcode: this._barcodeAction,
                    product: this._barcodeProductAction,
                    client: this._barcodeClientAction
                });
                this.refund_other_pos_orders = this.env.pos.config.refund_other_pos_orders;
            }

            mounted() {
                super.mounted();
                const $el = $(this.el);
                const show_refund_btn_pos = this.env.pos.get_pos_function_visibility_for_current_user('show_refund_btn_pos');
                $el.find('.button.pay').css('visibility', show_refund_btn_pos ? 'visible' : 'hidden');
            }

            getPaymentMethodsName(order) {
                return order.get_paymentlines().map(pl => pl.name).join(', ');
            }

            async _barcodeAction(code) {
                await this._onSearch({detail: {fieldName: 'BARCODE', searchTerm: code.base_code}})
            }

            async _barcodeProductAction(code) {
                await this._onSearch({detail: {fieldName: 'PRODUCT_BARCODE', searchTerm: code.base_code}})
            }

            async _barcodeClientAction(code) {
                const partner = this.env.pos.db.get_partner_by_barcode(code.code);
                if (partner) {
                    await this._onSearch({detail: {fieldName: 'CUSTOMER', searchTerm: partner.name}})
                }
            }

            isSyncedOrdersScreen() {
                return this.props.ui && this.props.ui.filter === 'SYNCED';
            }

            getUpdateOrderOptions(order) {
                const self = this;
                const options = [];
                if (this.showPaymentMethods(order)) {
                    options.push({
                        id: options.length + 1,
                        label: "Payments",
                        isSelected: false,
                        item: function (order) {
                            Gui.showPopup('UpdatePaymentPopup', {order, widget: self});
                        },
                    });
                }
                return options;

            }

            async onUpdateOrderBtnClick({detail: order}) {
                order = this._state.syncedOrders.cache[order.backendId] || order;
                const {confirmed, payload: selectedOption} = await this.showPopup('SelectionPopup',
                    {
                        title: this.env._t('What do you want to update?'),
                        list: this.getUpdateOrderOptions(order),
                    });
                if (confirmed) await selectedOption(order)
            }

            async onSearchOtherPosBtnClick(event) {
                Object.assign(this._state.ui.searchDetails, event.detail);
                this._state.syncedOrders.currentPage = 1;
                const domain = this._computeSyncedOrdersDomain();
                if (!domain.length || !domain.filter(d => d[0] === 'pos_reference').length) {
                    this.showNotification(
                        'Please enter a receipt number for searching another store.',
                        3000
                    );
                    return;
                }
                const limit = this._state.syncedOrders.nPerPage;
                const offset = (this._state.syncedOrders.currentPage - 1) * this._state.syncedOrders.nPerPage;
                const {ids, totalCount} = await this.rpc({
                    model: 'pos.order',
                    method: 'search_sudo_paid_order_ids',
                    kwargs: {domain, limit, offset},
                    context: this.env.session.user_context,
                });
                const idsNotInCache = ids.filter((id) => !(id in this._state.syncedOrders.cache));
                if (idsNotInCache.length > 0) {
                    const fetchedOrders = await this.rpc({
                        model: 'pos.order',
                        method: 'export_for_ui',
                        args: [idsNotInCache],
                        context: this.env.session.user_context,
                    });
                    // Check for missing products and partners and load them in the PoS
                    await this.env.pos._loadMissingProducts(fetchedOrders);
                    await this.env.pos._loadMissingPartners(fetchedOrders);
                    // Cache these fetched orders so that next time, no need to fetch
                    // them again, unless invalidated. See `_onInvoiceOrder`.
                    fetchedOrders.forEach((order) => {
                        const pos_order = new models.Order({}, {
                            pos: this.env.pos,
                            json: order
                        });
                        pos_order.pos_config = order.pos_config;
                        this._state.syncedOrders.cache[order.id] = pos_order;
                    });
                }
                this._state.syncedOrders.totalCount = totalCount;
                this._state.syncedOrders.toShow = ids.map((id) => this._state.syncedOrders.cache[id]);
                this.render();
            }

            _getToRefundDetail(orderline) {
                const toRefundDetail = super._getToRefundDetail(orderline);
                if (orderline.has_product_lot && orderline.pack_lot_lines.length && !toRefundDetail.lot_name) {
                    toRefundDetail.lot_name = orderline.pack_lot_lines.models[0].attributes.lot_name;
                }
                return toRefundDetail;
            }

            showPaymentMethods(order) {
                if (!order) {
                    for (const o of this.getFilteredOrderList()) {
                        if (['paid'].includes(o.state)) {
                            return true;
                        }
                    }
                    return false;
                }
                return ['paid'].includes(order.state);
            }

            showUpdateOrderBtn(order) {
                return !order.pos_config && !!this.getUpdateOrderOptions(order).length;
            }

            _prepareRefundOrderlineOptions(toRefundDetail) {
                const refundOrderlineOptions = super._prepareRefundOrderlineOptions(toRefundDetail);
                if (toRefundDetail.lot_name) {
                    refundOrderlineOptions.lot_name = toRefundDetail.lot_name
                }
                return refundOrderlineOptions;
            }

            showRefundAnotherStoreFeature() {
                return this.refund_other_pos_orders;
            }

            filterOrderListExtended() {
                const {fieldName, searchTerm} = this._state.ui.searchDetails;
                if (fieldName === 'PRODUCT_BARCODE') {
                    const filtered_orders = [];
                    for (const order of this._getOrderList()) {
                        for (const line of order.get_orderlines()) {
                            if (line.product.barcode && line.product.barcode.toLowerCase().includes(searchTerm.toLowerCase())) {
                                filtered_orders.push(line.order);
                                break;
                            }
                        }
                    }
                    return filtered_orders;
                }
                return false
            }

            /**
             * @override
             */
            getFilteredOrderList() {
                if (this._state.ui.filter == 'SYNCED') return this._state.syncedOrders.toShow;
                const filterCheck = (order) => {
                    if (this._state.ui.filter && this._state.ui.filter !== 'ACTIVE_ORDERS') {
                        const screen = order.get_screen_data();
                        return this._state.ui.filter === this._getScreenToStatusMap()[screen.name];
                    }
                    return true;
                };
                const {fieldName, searchTerm} = this._state.ui.searchDetails;
                const searchField = this._getSearchFields()[fieldName];

                const filteredOrdersByExtend = this.filterOrderListExtended();
                if (filteredOrdersByExtend) return filteredOrdersByExtend;

                const searchCheck = (order) => {
                    if (!searchField) return true;
                    const repr = searchField.repr(order);
                    if (repr === null) return true;
                    if (!searchTerm) return true;
                    return repr && repr.toString().toLowerCase().includes(searchTerm.toLowerCase());
                };
                const predicate = (order) => {
                    return filterCheck(order) && searchCheck(order);
                };
                return this._getOrderList().filter(predicate);
            }

            _getSearchFields() {
                return Object.assign({}, super._getSearchFields(), {
                    BARCODE: {
                        displayName: this.env._t('Barcode'),
                        modelField: 'barcode_number',
                    },
                    PRODUCT_BARCODE: {
                        displayName: this.env._t('Product Barcode'),
                        modelField: 'lines.product_id.barcode',
                    },
                    PAYMENT_METHOD: {
                        displayName: this.env._t('Payment Method'),
                        modelField: 'payment_ids.payment_method_id.name',
                    },
                });
            }

            async _onDoRefund() {
                await super._onDoRefund();
                const order = this.getSelectedSyncedOrder();
                const destinationOrder = this.env.pos.get_order();
                if (this.env.pos.config.set_og_cashier_for_refund && order.employee) {
                    this.env.pos.set_cashier(order.employee);
                    destinationOrder.set_employee(order.employee);
                }
            }
        };
    Registries.Component.extend(TicketScreen, TicketScreenExt);

    return TicketScreen;
});
