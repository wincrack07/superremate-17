/** @odoo-module */

import { Component, useEffect, useRef } from "@odoo/owl";
import { CenteredIcon } from "@point_of_sale/app/generic_components/centered_icon/centered_icon";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { OrderWidget } from "@point_of_sale/app/generic_components/order_widget/order_widget";
import { patch } from "@web/core/utils/patch";

patch(OrderWidget.prototype, {
    setup() {
        super.setup();
        this.pos = usePos();
    },
    getDiscount(){
        let order = this.pos.get_order();
        let order_discount = order ? order.get_order_discount() : 0;
        return this.env.utils.formatCurrency(order_discount);
    },
    getSubtotal(){
        let order = this.pos.get_order();
        let subtotal = order ? order.get_total_without_tax() : 0;
        return this.env.utils.formatCurrency(subtotal);
    },
    getTax() {
        let order = this.pos.get_order();
        let order_discount = order ? order.get_order_discount() : 0;
        const total = order.get_total_with_tax();
        const totalWithoutTax = order.get_total_without_tax() ;
        const taxAmount = total - totalWithoutTax + order_discount ;
        return {
            displayAmount: this.env.utils.formatCurrency(taxAmount),
        };
    },
});