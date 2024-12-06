/** @odoo-module */

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";
import { onMounted, useRef, useState } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";

export class SelectDiscountPopup extends AbstractAwaitablePopup {
    static template = "SelectDiscountPopup";

    setup() {
        super.setup();
        this.pos = usePos();
        onMounted(() => {
           this.mounted();
        });
    }

    mounted() {
        $('input.discount_on').on('change', function() {
            $('input.discount_on').not(this).prop('checked', false);
        });
    }

    click_confirm(){
        var order = this.pos.get_order();
        var orderlines = order.get_orderlines();
        var selected = $("input.discount_on:checked").attr("id");
        if(selected == 'on_order'){
            if(order.discount_on  == 'orderline'){
                orderlines.forEach(function (line) {
                    line.discount = 0.0;
                    line.discountStr = '0';
                    line.orderline_discount_type = '';
                    line.is_line_discount =false;
                });
            }
            order.set_discount_on('order');
        }
        else{
            if(order.discount_on  == 'order'){
                order.set_order_discount(0.0);
                order.order_discount_type = '';
            }
            order.set_discount_on('orderline');
        }
        this.cancel();
    }

    click_cancel(){
        this.cancel();
    }
}
