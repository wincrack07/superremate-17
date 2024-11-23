/** @odoo-module */

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";


patch(Order.prototype, {
    setup() {
        super.setup(...arguments);
        if (this.pos.config.alphabot_cliente_id) {
            var partner = this.get_partner();
            if (!partner){
                var default_customer = this.pos.config.alphabot_cliente_id[0];
                partner = this.pos.db.get_partner_by_id(default_customer);
                this.set_partner(partner);
            }
            if (this.pos.company.country && this.pos.company.country.code === "PA") {
                this.to_invoice = true;
            }
        }
    },
});
