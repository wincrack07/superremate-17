/** @odoo-module **/

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { registry } from "@web/core/registry";
import { Component } from "@odoo/owl";

export class MultiCurrencyPopup extends AbstractAwaitablePopup {
    static template = "MultiCurrencyPopup";
    setup() {
        super.setup();
        this.values = this.env.services.pos.multicurrencypayment;
        this.default_currency = this.env.services.pos.currency;
        this.selected_curr_name = this.values[0].name;
        this.AmountTotal = this.env.services.pos.get_order().get_due();
        this.selected_rate = this.values[0].rate
        this.inverse_rate = this.values[0].inverse_rate
        this.symbol = this.values[0].symbol
        this.amount_total_currency = (this.inverse_rate * this.AmountTotal).toFixed(4)
        if(this.env.services.pos.config.cash_rounding){
            var cash_rounding = this.env.services.pos.cash_rounding[0].rounding;
            this.AmountTotal = round_pr(this.env.services.pos.get_order().get_due(),cash_rounding)
        }
    }

    getValues(event){
        this.selected_value = this.values.find((val) => val.id === parseFloat(event.target.value));
        this.selected_curr_name = this.selected_value.name;
        this.selected_rate = this.selected_value.rate
        this.inverse_rate = this.selected_value.inverse_rate
        this.symbol = this.selected_value.symbol
        this.amount_total_currency = (this.inverse_rate * this.AmountTotal).toFixed(4);
        this.render();
    }

    getPayload() {
        return {
            currency_name: this.selected_curr_name,
            selected_rate : this.selected_rate,
            inverse_rate: this.inverse_rate,
            symbol : this.symbol,
        }
    }
}
