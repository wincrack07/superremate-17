/** @odoo-module */

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { DiscountTypePopup } from "@pos_discount_with_tax_app/js/Popups/DiscountPopup";

patch(ProductScreen.prototype, {
    setup() {
        super.setup();
        this.pos = usePos();
    },
    async onNumpadClick(buttonValue) {
        if (["quantity", "discount", "price"].includes(buttonValue)) {
            if(buttonValue == 'discount'){
                if(this.pos.config.allow_order_disc){
                    if(this.pos.get_order() && this.pos.get_order().discount_on){
                        await this.popup.add(DiscountTypePopup, {
                            body: 'Cheque',
                            startingValue: self,
                            title: "Discount",
                        });
                        this.numberBuffer.capture();
                        this.numberBuffer.reset();
                        this.pos.numpadMode = buttonValue;
                        return;
                    }
                    else{
                        alert('Please click on "Add Discount" and select discount on order/orderline')
                    }
                }
                else{
                    this.numberBuffer.capture();
                    this.numberBuffer.reset();
                    this.pos.numpadMode = buttonValue;
                    return;
                }
            }
            else{
                this.numberBuffer.capture();
                this.numberBuffer.reset();
                this.pos.numpadMode = buttonValue;
                return;
            }
        }
        this.numberBuffer.sendKey(buttonValue);
    }
});