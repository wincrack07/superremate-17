/** @odoo-module **/
/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */

import { _t } from "@web/core/l10n/translation";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { WkDiscountPopup } from "@pos_custom_discounts/app/disscount/discountPopup";
import { WkCustomDiscountPopup } from "@pos_custom_discounts/app/disscount/CoustomDiscountPoupop";
import { usePos } from "@point_of_sale/app/store/pos_hook";

patch(ProductScreen.prototype, {
    setup() {
        super.setup();
        this.pos = usePos();
        this.popup = useService("popup");
    },
    onNumpadClick(buttonValue) {
        var self = this;      
        const selectedOrderline = this.pos.get_order().get_selected_orderline();
        if (!selectedOrderline) {
            return;
        } if (buttonValue == 'discount' && selectedOrderline) {
            this.numberBuffer.reset();
            this.pos.numpadMode = "quantity";
            if (self.pos.config.discount_ids.length || self.pos.config.allow_custom_discount) {
                if (selectedOrderline && selectedOrderline.list_discount && selectedOrderline.selected_list_discount) {
                    this.popup.add(WkDiscountPopup, {
                        'title': "Discount List",
                        'selected_list_discount': selectedOrderline.selected_list_discount
                    });
                } else if (selectedOrderline && selectedOrderline.custom_discount) {
                    this.popup.add(WkCustomDiscountPopup, {
                        'title': _t("Customize Discount"),
                        'discount': selectedOrderline.discount,
                        'custom_discount': true,
                        'custom_discount_reason': selectedOrderline.custom_discount_reason,
                    });
                }
                else {
                    this.popup.add(WkDiscountPopup, {
                        'title': "Discount List"
                    });
                }
                return;
            } else {
                console.log("error+=========No discount is available for current POS. Please add discount from configuration===========")
                // self.showPopup('WebkulErrorPopup', {
                //     'title': self.env._t('No Discount Is Available'),
                //     'body': self.env._t('No discount is available for current POS. Please add discount from configuration')
                // });
                return ;
            }
        }
        super.onNumpadClick(buttonValue);
    }
});