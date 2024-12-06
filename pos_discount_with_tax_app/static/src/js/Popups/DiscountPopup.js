/** @odoo-module */

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";
import { onMounted, useRef, useState } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";

export class DiscountTypePopup extends AbstractAwaitablePopup {
    static template = "DiscountTypePopup";
    static defaultProps = {
        confirmText: 'Ok',
        cancelText: 'Cancel',
        title: 'Select Discount Type',
        body: '',
        list: [],
        startingValue: '',
    };

    setup() {
        super.setup();
        this.pos = usePos();
        let self = this;
        onMounted(() => {
           this.mounted();
        });
    }

    mounted() {
        $('input.dicount_type').on('change', function() {
            $('input.dicount_type').not(this).prop('checked', false);
        });
    }

    click_confirm(){
        var order = this.pos.get_order();
        var selected = $("input.dicount_type:checked").attr("id");
        if(order.discount_on == 'order'){
            if(selected == 'fixed'){
                order.set_order_discount_type('fixed');
            }
            else{
                order.set_order_discount_type('percentage');
            }
        }
        else{
            if(selected == 'fixed'){
                order.get_selected_orderline().is_line_discount = true;
                order.get_selected_orderline().set_orderline_discount_type('fixed');
            }
            else{
                order.get_selected_orderline().is_line_discount = true;
                order.get_selected_orderline().set_orderline_discount_type('percentage');
            }
        }
        this.cancel();
    }

    click_cancel(){
        this.cancel();
    }
}