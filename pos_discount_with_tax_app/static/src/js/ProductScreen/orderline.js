/** @odoo-module */

import { Orderline } from "@point_of_sale/app/generic_components/orderline/orderline";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/store/pos_hook";

patch(Orderline.prototype, {
    setup() {
        this.pos = usePos();
    },
    getCurrencySymbol() {
        return this.currency ? this.currency.symbol : "$";
    },
});