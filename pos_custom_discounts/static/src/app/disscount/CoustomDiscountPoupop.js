/** @odoo-module */
/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import {  onMounted } from "@odoo/owl";
export class WkCustomDiscountPopup extends AbstractAwaitablePopup {
    static template = "WkCustomDiscountPopup";
    setup() {
        super.setup();
        this.pos = usePos();
        onMounted(this.onMounted);
    }
    onMounted() {
        if (this.props.custom_discount) {
            $("#discount").val(this.props.discount)
            $("#reason").val(this.props.custom_discount_reason)
        }
    }
    click_current_product(event) {
        if (($('#discount').val()) > 100 || $('#discount').val() <= 0) {
            $('#error_div').show();
            $('#customize_error').html('<i class="fa fa-exclamation-triangle" aria-hidden="true"></i > Discount percent must be between 0 and 100.')
        } else {
            var wk_customize_discount = parseFloat($('#discount').val())
            var reason = ($("#reason").val());
            var order = this.pos.get_order();
            this.pos.get_order().get_selected_orderline().list_discount = false;
            this.pos.get_order().get_selected_orderline().selected_list_discount = false;
            order.get_selected_orderline().set_discount(wk_customize_discount);
            order.get_selected_orderline().custom_discount_reason = reason;
            order.get_selected_orderline().custom_discount = true;
            order.save_to_db();
            if (order._updateRewards) {
                order._updateRewards();
            }
            this.cancel();
        }
    }
    click_whole_order(event) {
        var self = this;
        var order = this.pos.get_order();
        var orderline_ids = order.get_orderlines();
        if (($('#discount').val()) > 100 || $('#discount').val() <= 0) {
            $('#error_div').show();
            $('#customize_error').html('<i class="fa fa-exclamation-triangle" aria-hidden="true"></i > Discount percent must be between 0 and 100.')
        } else {
            var wk_customize_discount = parseFloat($('#discount').val());
            var reason = ($("#reason").val());
            for (var i = 0; i < orderline_ids.length; i++) {
                orderline_ids[i].list_discount = false;
                orderline_ids[i].selected_list_discount = false;
                orderline_ids[i].set_discount(wk_customize_discount);
                orderline_ids[i].custom_discount_reason = reason;
                orderline_ids[i].custom_discount = true;
            }
            order.save_to_db();
            if (order._updateRewards) {
                order._updateRewards();
            }
            self.cancel()
        }
    }
    async click_remove_discount() {
        var self = this;
        this.pos.get_order().get_selected_orderline().set_discount(0);
        this.pos.get_order().get_selected_orderline().custom_discount = false;
        this.pos.get_order().get_selected_orderline().custom_discount_reason = '';
        this.pos.get_order().save_to_db();
        if (this.pos.get_order()._updateRewards) {
            this.pos.get_order()._updateRewards();
        }
        self.cancel()
    }
    
}