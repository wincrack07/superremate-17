/** @odoo-module */
/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

// import { PosDB } from "@point_of_sale/app/store/db";
patch(PosStore.prototype, {
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.all_discounts = loadedData['pos.custom.discount'];
    },
});