/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { registry } from "@web/core/registry";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { MultiCurrencyPopup } from "../Popups/MultiCurrencyPopup"

patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.popup = useService("popup");
    },
    async payMultipleCurrency() {
        if(this.pos.multicurrencypayment.length > 0){
            var payment_method_data = []
            this.payment_methods_from_config.forEach(function(id) {
                payment_method_data.push(id);
            });
            const { confirmed, payload } = await this.popup.add(MultiCurrencyPopup, {
                'payment_method': payment_method_data
            });
            if (confirmed) {
                if ($(".pay_amount").val()){
                    var payment_method = parseInt($(".payment-method-select").val())
                    var currency_amount = $(".pay_amount").val()
                    var get_amount = currency_amount / payload.inverse_rate
                    if(this.pos.config.cash_rounding){
                        var cash_rounding = this.pos.cash_rounding[0].rounding;
                        get_amount = round_pr(get_amount, cash_rounding);
                    }

                    let result = this.currentOrder.add_paymentline(this.env.services.pos.payment_methods_by_id[payment_method]);
                    this.selectedPaymentLine.set_amount(get_amount);
                    this.selectedPaymentLine.set_selected_currency(payload.currency_name);
                    this.selectedPaymentLine.set_currency_symbol(payload.symbol);
                    this.selectedPaymentLine.set_currency_rate(payload.inverse_rate);
                    this.selectedPaymentLine.set_currency_amount_paid(currency_amount);
                }
                else {
                    this.env.services.popup.add(ErrorPopup, { title: 'Amount Not Added',
                                            body: 'Please Enter the Amount!!' });
                }
            }
            else{
                return
            }
        }
        else{
            this.env.services.popup.add(ErrorPopup, { title: 'Currency Not Configured',
                                            body: 'Please Configure The Currency For Multi-Currency Payment.' });
            return;
        }
      }
})


