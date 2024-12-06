/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { useService } from "@web/core/utils/hooks";
import { SelectDiscountPopup } from "@pos_discount_with_tax_app/js/Popups/SelectDiscountPopupWidget";
import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";

export class OrderDiscountButton extends Component {
    static template = "OrderDiscountButton";

    setup() {
        this.pos = usePos();
        this.popup = useService("popup");
    }
    get discountType(){
        let order = this.pos.get_order();
        let text = "Add Discount";
        if(order){
            if(order.discount_on == 'order'){
                text = "Discount On Order";
            }
            if(order.discount_on == 'orderline'){
                text = "Discount On Orderline";
            }
        }
        return text;
    }
    async click() {
        const { confirmed } = await this.popup.add(SelectDiscountPopup, {
            title: _t("Select Discount Type"),
        });
    }
}

ProductScreen.addControlButton({
    component: OrderDiscountButton,
    condition: function () {
        return this.pos.config.allow_order_disc;
    },
});