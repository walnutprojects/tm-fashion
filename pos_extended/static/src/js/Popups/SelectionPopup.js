odoo.define('pos_extended.SelectionPopup', function (require) {
    'use strict';

    const SelectionPopup = require('point_of_sale.SelectionPopup');
    const Registries = require('point_of_sale.Registries');
    const {_lt} = require('@web/core/l10n/translation');

    const SelectionPopupExt = SelectionPopup =>
        class extends SelectionPopup {
            clear() {
                this.props.clear();
                this.trigger('close-popup');
            }
        };

    Registries.Component.extend(Registries.Component.baseNameMap.SelectionPopup, SelectionPopupExt);

    SelectionPopup.defaultProps = Object.assign({},
        SelectionPopup.defaultProps,
        {clearText: _lt('Clear')}
    );

    return SelectionPopup;
});
