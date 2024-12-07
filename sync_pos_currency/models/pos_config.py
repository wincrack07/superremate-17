# -*- coding: utf-8 -*-

from odoo import fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    multi_currency_payment = fields.Boolean('Multi Currency', help='To enable multi currency payment in pos')
    payment_currency_ids = fields.Many2many('res.currency', string="Currency")
