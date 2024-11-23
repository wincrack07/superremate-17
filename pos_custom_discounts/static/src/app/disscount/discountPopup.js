/** @odoo-module */
/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useState, onMounted } from "@odoo/owl";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { WkCustomDiscountPopup } from "@pos_custom_discounts/app/disscount/CoustomDiscountPoupop";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";

export class WkDiscountPopup extends AbstractAwaitablePopup {
    static template = "WkDiscountPopup";

    setup() {
        super.setup();
        this.pos = usePos();
        this.state = useState({ value: this.props.value });
        this.popup = useService("popup");
        onMounted(this.onMounted);
    }
    onMounted() {        
        var wk_discount_list = this.pos.all_discounts;
        this.wk_discount_percentage = 0;
        this.selected_discount = false;
        $(".button.apply").show();
        $(".button.apply_complete_order").show();
        $("#discount_error").hide();
        if (wk_discount_list && !wk_discount_list.length) {
            $(".button.apply_complete_order").hide();
            $(".button.apply").hide();
        }
        if (this.props.selected_list_discount) {
            $(".wk_popup_body span.wk_product_discount[id=" + this.props.selected_list_discount.id + "]").click()
        }
    }
    async wk_ask_password(password) {
        var ret = new $.Deferred();
        if (password) {
            const { confirmed, payload: inputPin } = await this.popup.add(NumberPopup, {
                isPassword: true,
                title: _t("Password?"),
                startingValue: null,
            });
    
            if (!confirmed) {
                return false;
            }
    
            if (password !== Sha1.hash(inputPin)) {
                await this.popup.add(ErrorPopup, {
                    title: _t("Incorrect Password"),
                    body: _t("Please try again."),
                });
                return false;
            }
            return true;
            
        } else {
            ret.resolve();
        }
        return ret;
    }
    async click_customize() {
        var self = this;
        if (self.pos.employees && self.pos.employees.length){
            var employee=null
            self.pos.employees.forEach(employee_v => {
                if( employee_v.id == self.pos.get_cashier().id){
                    employee=employee_v
                    return false;
                }                
            });
        }      
       
        if (self.pos.config.allow_security_pin && employee && employee.pin) {
            await self.wk_ask_password(employee.pin).then(function (data) { 
                if(data)  {
                    self.cancel();  
                    self.popup.add(WkCustomDiscountPopup);
                }             
                else
               return
            });
        } else {
            self.cancel();  
            this.popup.add(WkCustomDiscountPopup);
        }
             
    }
    click_wk_product_discount(event) {
        $("#discount_error").hide();
        $(".wk_product_discount").css('background', 'white');
        var discount_id = parseInt($(event.currentTarget).attr('id'));
        $(event.currentTarget).css('background', '#6EC89B');
        var wk_discount_list = this.pos.all_discounts;
        for (var i = 0; i < wk_discount_list.length; i++) {
            if (wk_discount_list[i].id == discount_id) {
                var wk_discount = wk_discount_list[i];
                this.wk_discount_percentage = wk_discount.discount_percent;
                this.selected_discount = wk_discount;
            }
        }
    }
    async click_remove_discount() {
        this.pos.get_order().get_selected_orderline().set_discount(0);
        this.pos.get_order().get_selected_orderline().list_discount = false;
        this.pos.get_order().get_selected_orderline().selected_list_discount = false;
        this.pos.get_order().get_selected_orderline().custom_discount_reason = "";
        this.pos.get_order().save_to_db();
        if (this.pos.get_order()._updateRewards) {
            this.pos.get_order()._updateRewards();
        }
        this.cancel()
    }
    click_apply(event) {
        var order = this.pos.get_order();
        if (this.wk_discount_percentage != 0) {
            order.get_selected_orderline().set_discount(this.wk_discount_percentage);
            order.get_selected_orderline().custom_discount_reason = '';
            order.get_selected_orderline().custom_discount = false;
            order.get_selected_orderline().list_discount = true;
            order.get_selected_orderline().selected_list_discount = this.selected_discount;
            $('ul.orderlines li.selected div#custom_discount_reason').text('');
            if (order._updateRewards) {
                order._updateRewards();
            }
            this.cancel();
        } else {
            $(".wk_product_discount").css("background-color", "burlywood");
            setTimeout(function () {
                $(".wk_product_discount").css("background-color", "");
            }, 100);
            setTimeout(function () {
                $(".wk_product_discount").css("background-color", "burlywood");
            }, 200);
            setTimeout(function () {
                $(".wk_product_discount").css("background-color", "");
            }, 300);
            setTimeout(function () {
                $(".wk_product_discount").css("background-color", "burlywood");
            }, 400);
            setTimeout(function () {
                $(".wk_product_discount").css("background-color", "");
            }, 500);
            return;
        }
    }
    click_apply_complete_order(event) {
        var order = this.pos.get_order();
        if (this.wk_discount_percentage != 0) {
            var orderline_ids = order.get_orderlines();
            for (var i = 0; i < orderline_ids.length; i++) {
                orderline_ids[i].custom_discount = false;
                orderline_ids[i].custom_discount_reason = "";
                orderline_ids[i].set_discount(this.wk_discount_percentage);
                orderline_ids[i].list_discount = true;
                orderline_ids[i].selected_list_discount = this.selected_discount;
            }
            if (order._updateRewards) {
                order._updateRewards();
            }
            this.cancel();
        } else {
            $(".wk_product_discount").css("background-color", "burlywood");
            setTimeout(function () {
                $(".wk_product_discount").css("background-color", "");
            }, 100);
            setTimeout(function () {
                $(".wk_product_discount").css("background-color", "burlywood");
            }, 200);
            setTimeout(function () {
                $(".wk_product_discount").css("background-color", "");
            }, 300);
            setTimeout(function () {
                $(".wk_product_discount").css("background-color", "burlywood");
            }, 400);
            setTimeout(function () {
                $(".wk_product_discount").css("background-color", "");
            }, 500);
            return;
        }
    }

}

