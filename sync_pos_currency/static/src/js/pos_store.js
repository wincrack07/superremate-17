/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { useService } from "@web/core/utils/hooks";
import { Payment } from "@point_of_sale/app/store/models";
// import { useState } from "@odoo/owl";

patch(PosStore.prototype, {

    async _processData(loadedData) {
        await super._processData(...arguments);
        const multi_curr = this.config.payment_currency_ids
        this.multicurrencypayment = await this.orm.call("res.currency","search_read",[], {
            context: {'check_from_pos': true},
            fields: ['name', 'symbol',  'position', 'rounding', 'inverse_rate', 'rate', 'decimal_places'],
            domain: [['id', 'in', multi_curr]],
        });
    },
})

patch(Payment.prototype, {
    setup(obj, options) {
        super.setup(...arguments);
        this.selected_currency = this.selected_currency || false;
        this.selected_currency_rate = this.selected_currency_rate || 0.0
        this.selected_currency_symbol = this.selected_currency_symbol || 0.0
        this.currency_amount_total = this.currency_amount_total || 0.0
    },

    set_selected_currency(currency){
        this.selected_currency = currency;
    },

    get_selected_currency() {
        return this.selected_currency;
    },

    set_currency_symbol(symbol){
        this.selected_currency_symbol = symbol
    },

    get_currency_symbol() {
        return this.selected_currency_symbol;
    },

    set_currency_rate(rate) {
        this.selected_currency_rate = rate
    },

    get_currency_rate() {
        return this.selected_currency_rate;
    },

    set_currency_amount_paid(total) {
        this.currency_amount_total = total
    },

    get_currency_amount_paid() {
        return Number(this.currency_amount_total);
    },

    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.selected_currency = json.selected_currency;
        this.selected_currency_symbol = json.selected_currency_symbol;
        this.selected_currency_rate = json.selected_currency_rate;
        this.currency_amount_total = json.currency_amount_total;
    },

    export_as_JSON() {
        let json = super.export_as_JSON(...arguments);
        json.selected_currency = this.get_selected_currency();
        json.selected_currency_symbol = this.get_currency_symbol();
        json.selected_currency_rate = this.get_currency_rate() || 0.0;
        json.currency_amount_total = this.get_currency_amount_paid() || 0.0;
        return json;
    },

    export_for_printing() {
        var receipt = super.export_for_printing(...arguments);
        receipt.selected_currency = this.get_selected_currency();
        receipt.selected_currency_symbol = this.get_currency_symbol();
        receipt.selected_currency_rate = this.get_currency_rate() || 0.0;
        var rounded_rate = receipt.selected_currency_rate;
        receipt.rounded_currency_rate = Math.round(rounded_rate * 100) / 100;
        receipt.currency_amount_total = this.get_currency_amount_paid() || 0.0;
        return receipt;
    }
});
