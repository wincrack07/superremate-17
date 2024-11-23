/* @odoo-modules */
/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */
import { Orderline } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Orderline.prototype, {
    /**
     * Checks if the current line applies for a global discount from `pos_discount.DiscountButton`.
     * @returns Boolean
     */
    setup(_defaultObj, options) {
        super.setup(...arguments);
        self.custom_discount = self.custom_discount || '';
        self.custom_discount_reason = self.custom_discount_reason || '';
        self.list_discount = self.list_discount || false;
        self.selected_list_discount = self.selected_list_discount || false;
    },
    init_from_JSON(json) {
        var self = this;
        super.init_from_JSON(...arguments);
        self.custom_discount = json.custom_discount || '';
        self.custom_discount_reason = json.custom_discount_reason || '';
        self.list_discount = json.list_discount || false;
        self.selected_list_discount = json.selected_list_discount || false;
    },
    export_as_JSON() {
        var self = this;
        var loaded = super.export_as_JSON(...arguments);
        if (self.custom_discount_reason)
            loaded.custom_discount_reason = self.custom_discount_reason;
        if (self.custom_discount)
            loaded.custom_discount = self.custom_discount;
        if (self.list_discount)
            loaded.list_discount = self.list_discount;
        if (self.selected_list_discount)
            loaded.selected_list_discount = self.selected_list_discount;
        return loaded
    },
    export_for_printing() {
        var dict = super.export_for_printing(...arguments);
        dict.custom_discount = this.custom_discount;
        dict.custom_discount_reason = this.custom_discount_reason;
        dict.list_discount = this.list_discount;
        dict.selected_list_discount = this.selected_list_discount;
        return dict;
    },
    get_custom_discount_reason() {
        return this.custom_discount_reason;
    },
    getDisplayData() {
        var line = super.getDisplayData()
        if (this.get_custom_discount_reason()) {
            line["get_custom_discount_reason"] = this.get_custom_discount_reason();
        }else{
            line["get_custom_discount_reason"] = null;
        }
        return line
    },
});
