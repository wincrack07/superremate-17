/** @odoo-module */

import { Orderline, Payment, Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { roundPrecision as round_pr } from "@web/core/utils/numbers";

patch(Order.prototype, {
    setup(_defaultObj, options) {
        super.setup(...arguments);
        this.discount_on = '';
        this.order_discount_type = '';
        this.discount_order = 0.0;
        this.main_disc = 0.0;
        if(options.json){
            this.set_discount_on(options.json.discount_on);
            this.set_order_discount(options.json.discount_order);
            this.set_order_discount_type(options.json.order_discount_type);
        }
    },

    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.discount_on = this.discount_on || false;
        json.discount_order = this.get_order_discount() || 0.0;
        json.order_discount_type = this.order_discount_type || false;
        return json;
    },

    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
    },

    set_discount_on(discount_on){
        this.discount_on = discount_on;
    },

    set_order_discount_type(order_discount_type){
        this.order_discount_type = order_discount_type;
    },

    set_order_discount(order_discount){
        this.discount_order = order_discount;
    },

    get_discount_on(){
        return this.discount_on;
    },

    get_order_discount_type(){
        return this.order_discount_type ;
    },

    get_order_discount(){
        var rounding = this.pos.currency.rounding;
        var percentage_charge = 0;
        var order = this.pos.get_order();
        if (order && order.discount_on == 'order') {
            if(order.get_total_without_tax() == 0){
                this.discount_order = 0.0;
                this.main_disc = 0.0;
            }

            if (order.order_discount_type === 'fixed') {
                var percentage_charge = this.discount_order;
                this.main_disc = round_pr(percentage_charge, rounding);
                return this.main_disc
            }
            if (order.order_discount_type === 'percentage') {
                var order = this.pos.get_order();
                var subtotal = 0.0;
                if(this.pos.config.order_discount_on == 'taxed'){
                    subtotal = this.get_total_without_tax() + this.get_total_tax();
                }
                else{
                    subtotal = this.get_total_without_tax();
                }
                var disc = this.discount_order;
                var percentage = (subtotal * disc) /100;
                var percentage_charge = percentage;
                this.main_disc =  round_pr(percentage_charge, rounding);
                return this.main_disc;
            }else{
                return 0.0
            }
        }
        else{
            return 0.0
        }
    },

    get_fixed_discount() {
        var total=0.0;
        var i;
        for(i=0;i<this.orderlines.models.length;i++) {
            if(this.orderlines.models[i].orderline_discount_type == 'fixed'){
                total = total + Math.min(Math.max(parseFloat(this.orderlines.models[i].discount * this.orderlines.models[i].quantity) || 0, 0),10000);
            }
            else{
                var discounted_price = (this.orderlines.models[i].price * this.orderlines.models[i].quantity) *(1.0 - (this.orderlines.models[i].discount / 100.0))
                total += (this.orderlines.models[i].price * this.orderlines.models[i].quantity) -discounted_price
            }
        }
        return total
    },

    get_total_with_tax() {
        var total = this.get_total_without_tax() + this.get_total_tax();
        return total - this.main_disc;
    },
});

patch(Orderline.prototype, {
    setup() {
        super.setup(...arguments);
//        this.orderline_discount_type =  '';
//        this.is_line_discount = false;
        this.orderline_discount_type = this.orderline_discount_type || false;
        this.is_line_discount = this.is_line_discount || false;
    },

    clone(){
        const orderline = super.clone(...arguments);
        orderline.note = this.note;
        orderline.is_line_discount = this.is_line_discount || false;
        orderline.orderline_discount_type = this.orderline_discount_type || false;
        return orderline;
    },

    export_as_JSON(){
        const json = super.export_as_JSON(...arguments);
        json.is_line_discount = this.is_line_discount || false;
        json.orderline_discount_type = this.orderline_discount_type || false;
        return json;
    },

    export_for_printing(){
        const json = super.export_for_printing(...arguments);
        json.is_line_discount = this.is_line_discount || false;
        json.orderline_discount_type = this.orderline_discount_type || false;
        return json;
    },

    init_from_JSON(json){
        super.init_from_JSON(...arguments);
        this.is_line_discount = json.is_line_discount || false;
        this.orderline_discount_type = json.orderline_discount_type || false;
    },

    set_orderline_discount_type(orderline_discount_type){
        this.orderline_discount_type = orderline_discount_type;
    },

    get_orderline_discount_type(){
        return this.orderline_discount_type ;
    },

    getDisplayData() {
        return {
            productName: this.get_full_product_name(),
            price: this.env.utils.formatCurrency(this.get_display_price()),
            qty: this.get_quantity_str(),
            unit: this.get_unit().name,
            unitPrice: this.env.utils.formatCurrency(this.get_unit_display_price()),
            oldUnitPrice: this.env.utils.formatCurrency(this.get_old_unit_display_price()),
            discount: this.get_discount_str(),
            customerNote: this.get_customer_note(),
            internalNote: this.getNote(),
            comboParent: this.comboParent?.get_full_product_name(),
            discount_type : this.get_orderline_discount_type(),
        };
    },

    set_discount(discount){
        var disc = Math.min(Math.max(parseFloat(discount) || 0, 0),100);
        var order = this.order;
        if(order){
            if(order.discount_on == 'order'){
                order.set_order_discount(disc)
                this.discount = 0;
                this.discountStr = '' + 0;
                this.orderline_discount_type = '';
            }
            else{
                if (this.orderline_discount_type == 'percentage'){
                    disc = Math.min(Math.max(parseFloat(discount) || 0, 0),100);
                }
                else if (this.orderline_discount_type == 'fixed'){
                    disc = parseFloat(discount);
                }
                if(disc == NaN || !disc ){
                    disc = 0;
                }
                this.discount = disc;
                this.discountStr = '' + disc;
            }

        }
        else{
            if(disc == NaN || !disc ){
                disc = 0;
            }
            this.discount = disc;
            this.discountStr = '' + disc;
        }
    },

    get_base_price(){
        var rounding = this.pos.currency.rounding;
        if (this.orderline_discount_type == 'fixed'){
            return round_pr((this.get_unit_price()- this.get_discount())* this.get_quantity(), rounding);
        }
        else{
            return round_pr(this.get_unit_price() * this.get_quantity() * (1 - this.get_discount()/100), rounding);
        }
    },

    get_all_prices(qty = this.get_quantity()) {
        var price_unit = this.get_unit_price() * (1.0 - this.get_discount() / 100.0);
        if (this.orderline_discount_type == 'fixed'){
            price_unit = this.get_base_price()/this.get_quantity();
        }
        var taxtotal = 0;

        var product = this.get_product();
        var taxes_ids = this.tax_ids || product.taxes_id;
        taxes_ids = taxes_ids.filter((t) => t in this.pos.taxes_by_id);
        var taxdetail = {};
        var product_taxes = this.pos.get_taxes_after_fp(taxes_ids, this.order.fiscal_position);

        var all_taxes = this.compute_all(
            product_taxes,
            price_unit,
            qty,
            this.pos.currency.rounding
        );
        var all_taxes_before_discount = this.compute_all(
            product_taxes,
            this.get_unit_price(),
            qty,
            this.pos.currency.rounding
        );
        all_taxes.taxes.forEach(function (tax) {
            taxtotal += tax.amount;
            taxdetail[tax.id] = {
                amount: tax.amount,
                base: tax.base,
            };
        });

        return {
            priceWithTax: all_taxes.total_included,
            priceWithoutTax: all_taxes.total_excluded,
            priceWithTaxBeforeDiscount: all_taxes_before_discount.total_included,
            priceWithoutTaxBeforeDiscount: all_taxes_before_discount.total_excluded,
            tax: taxtotal,
            taxDetails: taxdetail,
        };
    },
});